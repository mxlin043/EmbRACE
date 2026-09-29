"""Evaluate a VLM on EmbRACE tasks in a running UnrealZoo (UE5.6) server.

Protocol (the one used for all reported results):

* multi-turn conversation with one unified action space for every task type;
  the task type is never named, the model must infer it from the instruction;
* the initial observation is always kept, followed by a sliding window of the
  most recent ``window`` observations (default 13, i.e. at most 14 images per
  request), each paired with the assistant turn that acted on it;
* at most ``max_steps`` (default 60) actions per task; ``Finish`` ends a task.

Results are written to ``<save_dir>/<map>/<task>/<model>/`` as ``infos.json``
plus one JPEG per observation, and can be scored with
``python -m embrace.eval.score_metrics --runs-root <save_dir>``.

Endpoints, credentials and sampling per model come from
``configs/vlm_models.yaml``.

Usage:
    python -m embrace.eval.eval_vlm --port 9000 --model gpt-4o --map IndustrialArea
"""

import argparse
import json
import os
import shutil
import time
from pathlib import Path

import cv2
from PIL import Image

from embrace.core import Character_API
from embrace.vlm.client import (VLMClient, load_vlm_config,
                                parse_reasoning_action, resolve_route)


UNIFIED_ACTIONS = [
    "MoveForward", "MoveBackward", "TurnLeft", "TurnRight",
    "LookUp", "LookDown", "OpenDoor", "Pick", "Drop",
    "MidwayTarget", "Finish",
]

# Re-asks per step after an unavailable or unparsable action.  When all of them
# fail the step records Idle instead of aborting the task.
ACTION_ATTEMPTS = 3
# Transport retries per request, with exponential backoff (2, 4, 8, ... s).
MAX_RETRIES = 8

def structured_regex(reasoning_tag):
    """vLLM guided-decoding regex for routes with ``guided_regex: true``."""
    return (rf"<{reasoning_tag}>[^<]{{20,1500}}</{reasoning_tag}>"
            rf"\s*<action>({'|'.join(UNIFIED_ACTIONS)})</action>")


class EpisodeAborted(RuntimeError):
    """The VLM stayed unreachable for one task; skip it, keep the batch."""


def build_eval_system_prompt(task_text, midway_used, reasoning_tag="think",
                             no_rationale=False, pick_view_hint=True):
    """System prompt of the multi-turn evaluator.

    ``midway_used`` refers to the complete action history, not the retained
    window, so an early MidwayTarget is not forgotten once the window slides.
    """
    lines = [
        "You are an autonomous embodied agent operating in a 3D environment.",
        "",
        f'TASK: "{task_text}"',
        "",
        "MESSAGE STRUCTURE:",
        "- The first user message contains the initial task observation.",
        "- An assistant response following it is the action originally chosen "
        "from that initial observation.",
        "- The remaining completed user/assistant turns form the retained recent "
        "sliding-window segment in chronological order.",
        "- Intermediate interactions between the initial interaction and the "
        "retained recent segment may have been omitted.",
        "- The final user message has no assistant response and contains the "
        "observation from which you must act now.",
        "",
        "Use the task, the initial interaction, and the retained recent "
        "conversation to choose exactly one next action.",
        "",
        "FULL ACTION HISTORY STATUS:",
        ("- `MidwayTarget` has already appeared in the complete action history."
         if midway_used else
         "- `MidwayTarget` has not appeared in the complete action history, "
         "including interactions outside the retained sliding window."),
        "",
        "Available actions: " + ", ".join(f"`{a}`" for a in UNIFIED_ACTIONS),
        "",
        "Action rules:",
        "- `MoveForward` and `MoveBackward` move one discrete step; `TurnLeft` "
        "and `TurnRight` rotate in place; `LookUp` and `LookDown` tilt the view.",
        "- `OpenDoor` opens a door near you. It does not reach far, so approach "
        "the door first.",
        "- `Pick` picks up an object near you. It does not reach far, so "
        "approach the object first.",
    ] + ([
        "- Right after `Pick`, the view swings down to your own hands for that "
        "one observation so you can see what you are holding, and it returns "
        "to normal on your next action. Read that frame: empty hands mean the "
        "pick failed and the object is still where it was.",
    ] if pick_view_hint else []) + [
        "- `Drop` releases the object you are carrying, leaving it where you are.",
        "- Use `MidwayTarget` only when the TASK names at least two ordered "
        "destinations, and only after reaching the earlier one while the TASK "
        "still requires continuing to a different final destination.",
        "- If the TASK names only one destination, never use `MidwayTarget`.",
        "- Do not use `MidwayTarget` to report progress, and do not use it in "
        "place of `OpenDoor`, `Pick` or `Drop`.",
        "- Reaching a target means standing against it, not seeing it.",
        "- Stopping short fails the task, while one extra `MoveForward` costs "
        "almost nothing. Whenever you are not certain you are already "
        "touching the target, take another `MoveForward` instead of `Finish`.",
        "- Only `Finish` at a destination after a `MoveForward` has left the "
        "view essentially unchanged, showing that the target is physically "
        "stopping you. If what blocks you is not the target, turn and go "
        "around it.",
        "- `Finish` is terminal: use it only when the task's required final "
        "state is satisfied.",
        "- The action must be exactly one name from the list above "
        "(case-sensitive). Do not invent actions.",
        "",
        "Output exactly:",
        ("<action>ACTION</action>" if no_rationale else
         f"<{reasoning_tag}>Brief visual reasoning in at most 4 sentences."
         f"</{reasoning_tag}><action>ACTION</action>"),
    ]
    return "\n".join(lines)


def build_eval_conversation(task_text, images, thinkings, actions, window_size,
                            reasoning_tag="think", no_rationale=False,
                            pick_view_hint=True):
    """Assemble the conversation for the current step.

    ``images[i]`` is the observation the agent acted from at step ``i``; the
    last image is Current and has no action yet.  The initial interaction is
    always kept, then the most recent ``window_size`` observations.
    """
    current = len(images) - 1
    recent_start = max(1, current - (window_size - 1))

    def assistant(index):
        if no_rationale:
            return f"<action>{actions[index]}</action>"
        return (f"<{reasoning_tag}>{thinkings[index]}</{reasoning_tag}>"
                f"<action>{actions[index]}</action>")

    turns = [{
        "role": "system",
        "text": build_eval_system_prompt(
            task_text, "MidwayTarget" in actions, reasoning_tag, no_rationale,
            pick_view_hint),
    }]
    # On the first step the initial observation is Current; the closing turn
    # below already carries it.
    if current > 0:
        turns.append({"role": "user", "text": "Initial task observation.",
                      "images": [images[0]]})
    if actions:
        turns.append({"role": "assistant", "text": assistant(0)})
    for index in range(recent_start, current):
        turns.append({
            "role": "user",
            "text": "Observation obtained after the previous assistant action.",
            "images": [images[index]],
        })
        turns.append({"role": "assistant", "text": assistant(index)})
    turns.append({
        "role": "user",
        "text": "This is Current. Choose exactly one next action.",
        "images": [images[current]],
    })
    return turns


class EvalVLM:
    def __init__(self, ch_api, vlm, task_dir="./datas/benchmark/task", save_dir="./runs"):
        self.ch_api = ch_api
        self.vlm = vlm
        self.vlm_name = vlm.model
        # Tag the model is asked to wrap its reasoning in (think | reasoning).
        self.reasoning_tag = vlm.route["reasoning_tag"]
        if vlm.route.get("guided_regex"):
            self.vlm.structured_regex = structured_regex(self.reasoning_tag)

        self.task_dir = task_dir
        self.save_dir = save_dir
        # The longest expert T3 demonstration needs 52 steps.
        self.max_steps = 60
        # History 1..12 + Current: a turn is 30 degrees, so 12 turns make a full
        # rotation and the window still holds the frame the rotation began from.
        self.window_size = 13
        self.no_rationale = False
        self.pick_view_hint = True
        self.show = False
        self.task_types = None
        self.shard = None

        self.map_name = None
        self.task_list = []
        self.current_task_idx = 0
        self.task_data = None
        self._reset_episode()

    def _reset_episode(self):
        self.cmd_list = []
        self.thinking_list = []
        self.ego_list = []
        self.traj_pose_list = []
        # Interaction state for T4 (door) and T5 (object), same field layout as
        # the expert demonstrations, so one scorer reads both.
        self.door_state_list = []
        self.pd_pose_list = []
        self.pd_dist_2d_list = []
        self.step_timing_list = []
        self.step_counter = 0

    # ----------------------------------------------------------------- tasks

    def load_map_tasks(self, map_name):
        self.map_name = map_name
        task_root = os.path.join(self.task_dir, map_name)
        if not os.path.isdir(task_root):
            print(f"[!!!] Task directory not found: {task_root}")
            self.task_list = []
            return
        names = sorted(f for f in os.listdir(task_root) if f.endswith(".json"))
        if self.task_types:
            by_type = {t: [] for t in self.task_types}
            for name in names:
                with open(os.path.join(task_root, name), encoding="utf-8") as f:
                    task_type = int(json.load(f).get("Type", -1))
                if task_type in by_type:
                    by_type[task_type].append(name)
            names = [n for t in self.task_types for n in by_type[t]]
        if self.shard is not None:
            index, count = self.shard
            names = names[index::count]
        self.task_list = names
        print(f"[>>>] {len(names)} task(s) selected in {task_root}")

    def _task_save_folder(self, task_idx):
        stem = self.task_list[task_idx][:-len(".json")]
        return os.path.join(self.save_dir, self.map_name, stem, self.vlm_name)

    def _partial_path(self, task_idx):
        # Not named infos.json, so an interrupted task is never mistaken for done.
        return os.path.join(self._task_save_folder(task_idx), ".partial.json")

    def is_task_evaluated(self, task_idx):
        return os.path.exists(
            os.path.join(self._task_save_folder(task_idx), "infos.json"))

    def _capture(self):
        obs = self.ch_api.get_image_safe(cam_id=self.ch_api.cam_id, viewmode="lit")
        if self.show:
            cv2.imshow("Ego View", obs)
            cv2.waitKey(1)
        return obs

    def load_task(self, task_idx):
        ch_api = self.ch_api
        self.current_task_idx = task_idx
        task_path = os.path.join(self.task_dir, self.map_name,
                                 self.task_list[task_idx])
        print(f"\n[>>>] Task {task_idx + 1}/{len(self.task_list)}: {task_path}")
        with open(task_path, encoding="utf-8") as f:
            data = json.load(f)
        start_pose = data["Start_Pose"]

        # Every task starts from a freshly loaded map.
        ch_api.load_map(self.map_name)
        ch_api.set_resume()
        ch_api.set_char_pose_by_spawn(start_pose)
        if data.get("Type") != 5:
            ch_api.pre_loading_setup()
        else:
            ch_api.pre_loading_setup(data["PD_ID"], data["PD_Size"],
                                     data.get("PD_Start_Pose") or start_pose)
        ch_api.apply_task_exposure_settings(data)
        self.task_data = data
        self._reset_episode()

        # Warm-up identical to the one used when recording the demonstrations.
        ch_api.set_resume()
        ch_api.step_sync_combiation_cmd("Idle")
        for _ in range(2):
            obs = self._capture()
        ch_api.set_pause()
        ch_api.step_sync_combiation_cmd("Idle")
        for _ in range(2):
            obs = self._capture()

        self.ego_list.append(Image.fromarray(cv2.cvtColor(obs, cv2.COLOR_BGR2RGB)))
        self.traj_pose_list.append(list(start_pose))
        ch_api.set_resume()
        self._record_interaction_state()
        ch_api.set_pause()
        print(f"[>>>] Instruction: {data.get('Instruction')}")
        self._replay_partial(task_idx)

    def _record_interaction_state(self):
        """Append this step's door / object state (simulator must be resumed)."""
        task_type = self.task_data.get("Type")
        if task_type == 4:
            try:
                self.door_state_list.append(int(self.ch_api.get_door_state()))
            except Exception as error:
                print(f"[!!!] Failed to read door state: {error}")
                self.door_state_list.append(None)
        elif task_type == 5:
            try:
                self.pd_pose_list.append(self.ch_api.get_obj_pose(self.ch_api.pd_name))
            except Exception as error:
                print(f"[!!!] Failed to read object pose: {error}")
                self.pd_pose_list.append(None)
            try:
                self.pd_dist_2d_list.append(
                    self.ch_api.get_char_pd_dist2d_no_resume())
            except Exception as error:
                print(f"[!!!] Failed to read object distance: {error}")
                self.pd_dist_2d_list.append(None)

    # ---------------------------------------------------------------- resume

    def _save_partial(self):
        if not self.cmd_list:
            return
        folder = self._task_save_folder(self.current_task_idx)
        os.makedirs(folder, exist_ok=True)
        path = self._partial_path(self.current_task_idx)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"Model": self.vlm_name, "Action": self.cmd_list,
                       "Thinking": self.thinking_list,
                       "Step_Timing": self.step_timing_list},
                      f, indent=2, ensure_ascii=False)
        os.replace(path + ".tmp", path)
        print(f"[>>>] {len(self.cmd_list)} step(s) cached for resume: {path}")

    def _replay_partial(self, task_idx):
        """Replay cached actions of an interrupted task without calling the VLM.

        The start pose and the actions are deterministic, so the replay reaches
        the same state; images are re-rendered and reasoning restored from cache.
        """
        path = self._partial_path(task_idx)
        if not os.path.exists(path):
            return
        try:
            cached = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        actions = cached.get("Action") or []
        thinkings = cached.get("Thinking") or []
        if not actions or len(actions) != len(thinkings):
            return
        print(f"[>>>] Resuming: replaying {len(actions)} cached step(s)")
        for cmd, thinking in zip(actions, thinkings):
            self._execute(cmd, thinking)
        self.step_timing_list = list(cached.get("Step_Timing") or [])

    # ------------------------------------------------------------------ step

    def _allowed_actions(self):
        runnable = self.ch_api.ACTION_MAP_Combination
        return [a for a in UNIFIED_ACTIONS if a in runnable]

    def _execute(self, cmd, thinking):
        self.ch_api.set_resume()
        self.ch_api.step_sync_combiation_cmd(cmd)
        self.cmd_list.append(cmd)
        self.thinking_list.append(thinking)
        obs = self._capture()
        self.ego_list.append(Image.fromarray(cv2.cvtColor(obs, cv2.COLOR_BGR2RGB)))
        self.traj_pose_list.append(self.ch_api.get_agent_pose())
        self._record_interaction_state()
        self.ch_api.set_pause()
        self.step_counter += 1

    def _query(self, turns):
        for attempt in range(MAX_RETRIES):
            try:
                return self.vlm.post_messages(turns)
            except Exception as error:
                print(f"[!!!] VLM request failed ({attempt + 1}/{MAX_RETRIES}): {error}")
                if attempt == MAX_RETRIES - 1:
                    raise EpisodeAborted(str(error)) from error
                time.sleep(2 * (2 ** attempt))

    def step_once(self):
        """Ask the model for one action and execute it. Returns the action."""
        allowed = self._allowed_actions()
        correction = None
        t_start = time.time()
        for attempt in range(ACTION_ATTEMPTS):
            turns = build_eval_conversation(
                self.task_data.get("Instruction"), self.ego_list,
                self.thinking_list, self.cmd_list, self.window_size,
                self.reasoning_tag, self.no_rationale, self.pick_view_hint)
            if correction:
                # Sent with this request only; never stored in the history.
                turns.append({"role": "user", "text": correction})
            result = parse_reasoning_action(self._query(turns))
            cmd = result["action"]
            if cmd in allowed:
                break
            shape = ("<action>ACTION</action>." if self.no_rationale else
                     f"<{self.reasoning_tag}>...</{self.reasoning_tag}>"
                     "<action>ACTION</action>.")
            if result.get("parse_failed"):
                print(f"[!!!] No action parsed ({attempt + 1}/{ACTION_ATTEMPTS})")
                correction = (
                    "Your previous reply never produced an action: it kept "
                    "weighing options until it hit the length limit and was cut "
                    "off. Do not deliberate further. Keep your reasoning to at "
                    "most 40 words, commit to the single best action, and output "
                    "exactly " + shape)
            else:
                print(f"[!!!] Unavailable action {cmd!r} "
                      f"({attempt + 1}/{ACTION_ATTEMPTS})")
                correction = (
                    f'Your previous reply chose "{cmd}", which is not an '
                    f'available action. Choose exactly one of: '
                    f'{", ".join(allowed)}. Output exactly ' + shape)
        else:
            print(f"[!!!] {ACTION_ATTEMPTS} attempts failed; recording Idle.")
            cmd = "Idle"
        self.step_timing_list.append({"step": self.step_counter + 1,
                                      "client_s": round(time.time() - t_start, 3)})
        self._execute(cmd, result["thinking"])
        print(f"[>>>] Step {self.step_counter}: {cmd}")
        return cmd

    # ------------------------------------------------------------------ save

    def save_results(self):
        folder = self._task_save_folder(self.current_task_idx)
        os.makedirs(folder, exist_ok=True)
        task_copy = os.path.join(folder, "task.json")
        if not os.path.exists(task_copy):
            shutil.copy(os.path.join(self.task_dir, self.map_name,
                                     self.task_list[self.current_task_idx]),
                        task_copy)
        data = self.task_data
        task_type = data.get("Type")
        infos = {
            "Model": self.vlm_name,
            "Instruction": data.get("Instruction"),
            "Type": task_type,
            "Start_Pose": data.get("Start_Pose"),
            "Action": self.cmd_list,
            "Thinking": self.thinking_list,
            "Pose_Trajectory": self.traj_pose_list,
            "Window_Size": self.window_size,
            "Step_Timing": self.step_timing_list,
        }
        if task_type == 4 and self.door_state_list:
            infos["Door_State_Trajectory"] = self.door_state_list
        elif task_type == 5:
            for key in ("PD_ID", "PD_Size", "PD_Type", "PD_Start_Pose"):
                if key in data:
                    infos[key] = data[key]
            infos["PD_Pose_Trajectory"] = self.pd_pose_list
            infos["PD_Dist_2D"] = [None if v is None else round(v, 1)
                                   for v in self.pd_dist_2d_list]
        with open(os.path.join(folder, "infos.json"), "w", encoding="utf-8") as f:
            json.dump(infos, f, indent=4, ensure_ascii=False)
        partial = self._partial_path(self.current_task_idx)
        if os.path.exists(partial):
            os.remove(partial)
        for index, img in enumerate(self.ego_list):
            img.save(os.path.join(folder, f"{index:03d}.jpg"))
        print(f"[>>>] Saved: {folder}")

    # ------------------------------------------------------------------- run

    def run(self, map_name):
        self.load_map_tasks(map_name)
        for task_idx in range(len(self.task_list)):
            if self.is_task_evaluated(task_idx):
                print(f"[>>>] Task {task_idx + 1} already evaluated, skipping.")
                continue
            self.load_task(task_idx)
            try:
                while self.step_counter < self.max_steps:
                    if self.step_once() == "Finish":
                        break
            except EpisodeAborted as error:
                # Keep the steps already paid for; a rerun resumes from here.
                self._save_partial()
                print(f"[!!!] Task {task_idx + 1} abandoned ({error}).")
                continue
            self.save_results()
        print(f"[>>>] {map_name}: all selected tasks done.")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ip", default="127.0.0.1", help="UnrealCV server IP")
    parser.add_argument("--port", type=int, default=9000, help="UnrealCV port")
    parser.add_argument("--map", nargs="+", default=None,
                        help="Map(s) to evaluate (default: every map folder in --task_dir)")
    parser.add_argument("--model", required=True,
                        help="Model name: selects the route in the VLM config and "
                             "names the result folder")
    parser.add_argument("--vlm_config", default=None,
                        help="VLM routing file (default: configs/vlm_models.yaml)")
    parser.add_argument("--api_base", default=None,
                        help="Override the route's API base URL")
    parser.add_argument("--api_key", default=None,
                        help="Override the route's API key")
    parser.add_argument("--protocol", choices=("openai", "anthropic"), default=None,
                        help="Override the route's wire protocol")
    parser.add_argument("--task_dir", default="./datas/benchmark/task",
                        help="Benchmark tasks, one folder per map")
    parser.add_argument("--save_dir", default="./runs")
    parser.add_argument("--max_steps", type=int, default=60)
    parser.add_argument("--window", type=int, default=13,
                        help="Recent observations kept, including Current")
    parser.add_argument("--task_types", type=int, nargs="+",
                        help="Only evaluate these task types (0-5)")
    parser.add_argument("--shard", default=None,
                        help="i/n: evaluate every n-th task starting at i, so n "
                             "UE servers can split one map")
    parser.add_argument("--no_rationale", action="store_true",
                        help="Ablation: actions only, no reasoning in prompt or history")
    parser.add_argument("--pick_view_hint", choices=("on", "off"), default="on",
                        help="Explain the one-frame hand view after Pick (default on)")
    parser.add_argument("--show", action="store_true",
                        help="Show the ego view in an OpenCV window")
    args = parser.parse_args()

    route = resolve_route(args.model, load_vlm_config(args.vlm_config),
                          api_base=args.api_base, api_key=args.api_key,
                          protocol=args.protocol)
    vlm = VLMClient(args.model, route)
    print(f"[>>>] Model {args.model} -> {route['api_model']} via "
          f"{route['protocol']} at {route['api_base']}")
    print(f"[>>>] Connecting to UE server at {args.ip}:{args.port} ...")
    ch_api = Character_API(ip=args.ip, port=args.port)

    evaluator = EvalVLM(ch_api, vlm, task_dir=args.task_dir, save_dir=args.save_dir)
    evaluator.max_steps = args.max_steps
    evaluator.window_size = args.window
    evaluator.no_rationale = args.no_rationale
    evaluator.pick_view_hint = args.pick_view_hint == "on"
    evaluator.show = args.show
    evaluator.task_types = args.task_types
    if args.shard:
        index, count = (int(x) for x in args.shard.split("/"))
        if not 0 <= index < count:
            parser.error(f"--shard {args.shard}: need 0 <= i < n")
        evaluator.shard = (index, count)

    try:
        maps = args.map or sorted(
            d for d in os.listdir(args.task_dir)
            if os.path.isdir(os.path.join(args.task_dir, d)))
        for map_name in maps:
            evaluator.run(map_name)
    finally:
        if ch_api.client.isconnected():
            ch_api.client.disconnect()


if __name__ == "__main__":
    main()
