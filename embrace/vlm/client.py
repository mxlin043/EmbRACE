"""VLM client and model routing.

Every model-specific setting (endpoint, protocol, credentials, sampling,
reasoning tag) lives in ``configs/vlm_models.yaml``; nothing here depends on
model names.  Two wire protocols are supported:

* ``openai``    -- OpenAI-compatible ``/chat/completions``: the OpenAI API,
  Google's OpenAI-compatible Gemini endpoint, and self-hosted servers
  (vLLM, SGLang, LMDeploy, ...);
* ``anthropic`` -- Anthropic ``/v1/messages``.
"""

import base64
import copy
import fnmatch
import io
import os
import re

import requests
import yaml


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
DEFAULT_CONFIG = os.path.join(PROJECT_ROOT, "configs", "vlm_models.yaml")

BUILTIN_DEFAULTS = {
    "protocol": "openai",
    "api_base": None,
    "api_key_env": None,
    "api_key": None,
    "api_model": None,
    "temperature": 0.5,
    "max_tokens": None,
    "timeout": 120,
    "extra_body": {},
    "reasoning_tag": "think",
    "guided_regex": False,
}
SAMPLING_KEYS = ("temperature", "top_p", "top_k", "min_p", "presence_penalty",
                 "max_tokens")
_META_KEYS = ("match", "provider", "sampling")
_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


# --------------------------------------------------------------------------
# routing


def _expand(value):
    """Expand ``${VAR}`` and ``${VAR:-default}`` in every string."""
    if isinstance(value, str):
        return _ENV_RE.sub(
            lambda m: os.environ.get(m.group(1)) or (m.group(2) or ""), value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def load_vlm_config(path=None):
    with open(path or DEFAULT_CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _matches(model, patterns):
    if isinstance(patterns, str):
        patterns = [patterns]
    return any(fnmatch.fnmatchcase(model, p) for p in patterns)


def resolve_route(model, config, api_base=None, api_key=None, protocol=None):
    """Settings for ``model``: defaults < provider < preset < entry < flags."""
    entry = next((e for e in config.get("models") or []
                  if _matches(model, e.get("match", []))), None)
    if entry is None and api_base is None:
        raise KeyError(
            f"No route for model {model!r}: add an entry under `models:` in "
            f"the VLM config, or pass --api_base (and --protocol) explicitly.")

    route = copy.deepcopy(BUILTIN_DEFAULTS)
    route.update(config.get("defaults") or {})
    if entry is not None:
        provider = entry.get("provider")
        if provider is not None:
            providers = config.get("providers") or {}
            if provider not in providers:
                raise KeyError(f"model {model!r}: unknown provider {provider!r}")
            route.update(providers[provider])
        sampling = entry.get("sampling")
        if isinstance(sampling, str):
            presets = config.get("sampling_presets") or {}
            if sampling not in presets:
                raise KeyError(f"model {model!r}: unknown sampling preset {sampling!r}")
            sampling = presets[sampling]
        route.update(sampling or {})
        route.update({k: v for k, v in entry.items() if k not in _META_KEYS})

    if api_base is not None:
        route["api_base"] = api_base
    if protocol is not None:
        route["protocol"] = protocol
    route = _expand(route)
    route["api_model"] = route.get("api_model") or model
    route["extra_body"] = route.get("extra_body") or {}

    if route["protocol"] not in ("openai", "anthropic"):
        raise ValueError(f"model {model!r}: unknown protocol {route['protocol']!r}")
    if not route.get("api_base"):
        raise ValueError(f"model {model!r}: no api_base configured")
    if api_key is not None:
        route["api_key"] = api_key
    elif not route.get("api_key") and route.get("api_key_env"):
        route["api_key"] = os.environ.get(route["api_key_env"])
        if not route["api_key"]:
            raise EnvironmentError(
                f"model {model!r} needs an API key: export {route['api_key_env']}=...")
    return route


# --------------------------------------------------------------------------
# reply parsing


def parse_reasoning_action(response):
    """Extract ``<think>/<reasoning>`` and ``<action>`` from a model reply.

    Returns ``{"action", "thinking"}``.  When no action can be parsed the
    action is ``"Idle"`` and ``parse_failed`` is set, so the caller can re-ask.
    """
    response = response or ""
    think = re.search(r"<(think|reasoning)>(.*?)</\1>", response, re.DOTALL)
    action = re.search(r"<action>(.*?)</action>", response, re.DOTALL)
    if not action:
        # GLM-4.1V sometimes wraps the answer in its own box tokens.
        action = re.search(r"<\|begin_of_box\|>(.*?)<\|end_of_box\|>",
                           response, re.DOTALL)
    thinking = think.group(2).strip() if think else ""
    if not action:
        return {"action": "Idle", "thinking": thinking or "There is no thinking.",
                "parse_failed": True}
    return {"action": action.group(1).strip(),
            "thinking": thinking or "There is no thinking."}


# --------------------------------------------------------------------------
# client


def encode_image(img):
    """PIL image -> base64 JPEG string (native resolution)."""
    with io.BytesIO() as buffer:
        img.convert("RGB").save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


class VLMClient:
    """Send a multi-turn, multi-image conversation and return the reply text.

    ``turns`` is a list of ``{"role": "system"|"user"|"assistant",
    "text": str, "images": [PIL.Image, ...]}``.
    """

    def __init__(self, model, route):
        self.model = model
        self.route = route
        self.protocol = route["protocol"]
        self.api_base = route["api_base"].rstrip("/")
        # Set by the evaluator when route["guided_regex"] is true.
        self.structured_regex = None
        self.last_request_metadata = {}
        self.last_response_metadata = {}

    def _url(self):
        if self.protocol == "anthropic":
            base = self.api_base if self.api_base.endswith("/v1") \
                else self.api_base + "/v1"
            return base + "/messages"
        return self.api_base + "/chat/completions"

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        key = self.route.get("api_key")
        if self.protocol == "anthropic":
            headers["anthropic-version"] = "2023-06-01"
            if key:
                headers["x-api-key"] = key
        elif key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def _payload(self, turns):
        anthropic = self.protocol == "anthropic"
        system_text = None
        messages = []
        image_count = 0
        for turn in turns:
            role = turn["role"]
            text = turn.get("text") or ""
            if role == "system":
                system_text = text
                continue
            if role == "assistant":
                messages.append({"role": "assistant", "content": text})
                continue
            encoded = [encode_image(img) for img in (turn.get("images") or [])]
            image_count += len(encoded)
            if anthropic:
                blocks = [{"type": "image",
                           "source": {"type": "base64", "media_type": "image/jpeg",
                                      "data": data}} for data in encoded]
                if text:
                    blocks.append({"type": "text", "text": text})
            else:
                blocks = [{"type": "text", "text": text}] if text else []
                blocks += [{"type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{data}"}}
                           for data in encoded]
            if blocks:
                messages.append({"role": role, "content": blocks})

        payload = {"model": self.route["api_model"]}
        if anthropic:
            payload["messages"] = messages
            if system_text:
                payload["system"] = system_text
        else:
            if system_text:
                messages.insert(0, {"role": "system", "content": system_text})
            payload["messages"] = messages
        for key in SAMPLING_KEYS:
            if self.route.get(key) is not None:
                payload[key] = self.route[key]
        payload.update(copy.deepcopy(self.route["extra_body"]))
        if self.structured_regex:
            payload["structured_outputs"] = {"regex": self.structured_regex}
        return payload, image_count

    def post_messages(self, turns):
        payload, image_count = self._payload(turns)
        url = self._url()
        self.last_request_metadata = {
            "model": self.model,
            "api_model": payload["model"],
            "protocol": self.protocol,
            "endpoint": url,
            "sampling": {k: payload[k] for k in SAMPLING_KEYS if k in payload},
            "image_count": image_count,
            "turn_count": len(payload["messages"]),
        }
        self.last_response_metadata = {}
        try:
            response = requests.post(url, headers=self._headers(), json=payload,
                                     timeout=self.route["timeout"])
        except requests.RequestException as error:
            raise ConnectionError(f"VLM request failed: {error}") from error
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        result = response.json()
        self.last_response_metadata = {
            "status_code": response.status_code,
            "id": result.get("id"),
            "model": result.get("model"),
            "usage": result.get("usage"),
        }
        if self.protocol == "anthropic":
            parts = [b.get("text", "") for b in result.get("content", [])
                     if isinstance(b, dict) and b.get("type") == "text"]
            text = "\n".join(p for p in parts if p)
            if not text:
                raise RuntimeError("no text block in Anthropic response")
            return text
        return result["choices"][0]["message"]["content"]
