"""EmbRACE web playground: walk around the benchmark environments in a browser.

UnrealZoo runs locally; this Flask app connects to it through UnrealCV and
serves one page with a live egocentric view and two control modes:

* Standard -- one key press or click is one discrete benchmark action, the
  same step a model takes.
* Free Move -- hold keys to walk, turn and look around continuously.

Tasks are listed from ``datas/benchmark/task`` and ``datas/dataset/task``.  Loading a task places the agent at the task's start pose (with its
target object and exposure) and shows its instruction.  There is no step limit
and no scoring: walk wherever you like.

Usage:
    python -m embrace.web_ui.playground --port 9000 --map IndustrialArea
    # then open http://localhost:8080
"""

import argparse
import json
import os
import threading
import time

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, send_file

from embrace.core import Character_API


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
with open(os.path.join(PROJECT_ROOT, "embrace", "configs", "maps.json"),
          encoding="utf-8") as _f:
    MAPS = [m["name"] for m in json.load(_f)["maps"]]

TYPE_NAMES = {
    0: "Basic", 1: "Exploration", 2: "Dynamic Spatial-Semantic",
    3: "Multi-stage", 4: "Open Door", 5: "Pick & Drop",
}
ACTIONS = [
    "MoveForward", "MoveBackward", "TurnLeft", "TurnRight", "LookUp",
    "LookDown", "OpenDoor", "Pick", "Drop",
]
INTERACTIONS = ("OpenDoor", "Pick", "Drop")

# Free Move: while a key is held, send one movement input, wait for it to
# return, then pause FREE_TICK_S.
FREE_FORWARD = 200
FREE_TURN = 20
FREE_TICK_S = 0.1
KEY_TIMEOUT_S = 0.6             # held keys expire without a browser heartbeat

app = Flask(__name__)


class State:
    def __init__(self):
        self.ch_api = None
        self.task_dirs = []
        self.preview_dirs = []
        self.map_name = None
        self.task = None          # loaded task JSON, or None in free roam
        self.task_name = None
        self.mode = "standard"
        self.keys = {}
        self.keys_time = 0.0
        self.pending = None       # interaction queued from Free Move
        self.free_thread = None
        self.frame = None
        self.pose = None
        self.last_actions = []
        self.busy = False
        self.status = "Connecting"
        self.error = False
        self.lock = threading.Lock()   # serialises every UnrealCV request


state = State()


# --------------------------------------------------------------------------
# simulator helpers (called with state.lock held)


def grab_ego(safe=True):
    """Capture the ego view.

    ``get_image_safe`` nudges the camera and puts it back to force a fresh
    render, which is only correct while the simulation is paused: with the
    world running, the agent moves between the two writes and the camera is
    left behind inside the agent's body.  Frames taken while the world runs
    (Free Move, the idle refresh) therefore use the plain capture.
    """
    ch = state.ch_api
    if safe:
        frame = ch.get_image_safe(cam_id=ch.cam_id, viewmode="lit")
    else:
        frame = ch.get_image(cam_id=ch.cam_id, viewmode="lit")
    if frame is not None:
        state.frame = frame


def read_pose():
    try:
        state.pose = [round(float(v), 1) for v in state.ch_api.get_agent_pose()]
    except Exception:
        pass


def load_free_map(map_name):
    ch = state.ch_api
    ch.load_map(map_name)
    ch.pre_loading_setup()
    ch.set_resume()
    ch.step_sync_combiation_cmd("Idle")
    for _ in range(2):
        grab_ego()
    ch.set_resume()
    state.map_name = map_name
    state.task = None
    state.task_name = None
    state.last_actions = []
    read_pose()


def find_task(map_name, task_name):
    """Path of ``<map>/<task>`` in the first task directory that has it."""
    for root in state.task_dirs:
        path = os.path.join(root, str(map_name), str(task_name))
        if os.path.isfile(path):
            return path
    return None


def load_task(map_name, task_name):
    """Start pose, target object and exposure, as the evaluator sets them up."""
    with open(find_task(map_name, task_name), encoding="utf-8") as f:
        data = json.load(f)
    ch = state.ch_api
    ch.load_map(map_name)
    ch.set_resume()
    ch.set_char_pose_by_spawn(data["Start_Pose"])
    if data.get("Type") == 5:
        ch.pre_loading_setup(data["PD_ID"], data["PD_Size"],
                             data.get("PD_Start_Pose") or data["Start_Pose"])
    else:
        ch.pre_loading_setup()
    ch.apply_task_exposure_settings(data)

    ch.set_resume()
    ch.step_sync_combiation_cmd("Idle")
    for _ in range(2):
        grab_ego()
    ch.set_pause()
    ch.step_sync_combiation_cmd("Idle")
    for _ in range(2):
        grab_ego()

    state.map_name = map_name
    state.task = data
    state.task_name = task_name
    state.last_actions = []
    read_pose()


def standard_action(action):
    """One discrete benchmark action (the simulation pauses after it)."""
    ch = state.ch_api
    ch.set_resume()
    ch.step_sync_combiation_cmd(action)
    grab_ego()
    read_pose()
    state.last_actions = (state.last_actions + [action])[-12:]


# --------------------------------------------------------------------------
# Free Move


def free_loop():
    ch = state.ch_api
    last_pose = 0.0
    with state.lock:
        ch.set_resume()
    while state.mode == "free":
        with state.lock:
            try:
                keys = (state.keys if time.time() - state.keys_time < KEY_TIMEOUT_S
                        else {})
                if state.pending:
                    action, state.pending = state.pending, None
                    ch.step_sync_combiation_cmd(action)
                    ch.set_resume()
                    state.last_actions = (state.last_actions + [action])[-12:]
                else:
                    move = [[0, 0], 0, 0]
                    if keys.get("forward"):
                        move[0][1] = FREE_FORWARD
                    elif keys.get("backward"):
                        move[0][1] = -FREE_FORWARD
                    if keys.get("left"):
                        move[0][0] = -FREE_TURN
                    elif keys.get("right"):
                        move[0][0] = FREE_TURN
                    if keys.get("lookup"):
                        move[1] = 1
                    elif keys.get("lookdown"):
                        move[1] = 2
                    ch.step(move)
                grab_ego(safe=False)
                if time.time() - last_pose > 0.25:
                    read_pose()
                    last_pose = time.time()
            except Exception as error:
                state.status = f"Error: {error}"
        time.sleep(FREE_TICK_S)
    with state.lock:
        try:
            ch.step([[0, 0], 0, 0])
            grab_ego(safe=False)
            read_pose()
        except Exception:
            pass


def start_free():
    if state.mode == "free":
        return
    state.keys = {}
    state.mode = "free"
    state.status = "Free Move"
    state.free_thread = threading.Thread(target=free_loop, daemon=True)
    state.free_thread.start()


def stop_free():
    if state.mode != "free":
        return
    state.mode = "standard"
    state.keys = {}
    if state.free_thread is not None:
        state.free_thread.join(timeout=3.0)
        state.free_thread = None
    state.status = "Ready"


# --------------------------------------------------------------------------
# background stream


def refresh_loop():
    """Keep the ego frame fresh in Standard mode (Free Move grabs its own)."""
    while True:
        time.sleep(0.2)
        if state.ch_api is None or state.busy or state.mode == "free":
            continue
        if state.lock.acquire(blocking=False):
            try:
                grab_ego(safe=False)
            except Exception:
                pass
            finally:
                state.lock.release()


def mjpeg():
    placeholder = np.full((480, 640, 3), 235, dtype=np.uint8)
    cv2.putText(placeholder, "No signal", (245, 245),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (150, 150, 150), 2)
    while True:
        frame = state.frame if state.frame is not None else placeholder
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ok:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                   + buf.tobytes() + b"\r\n")
        time.sleep(0.05 if state.mode == "free" else 0.1)


def run_locked(fn, *args, status="Ready"):
    if state.busy:
        return jsonify(ok=False, message="busy")
    state.busy = True
    try:
        with state.lock:
            fn(*args)
        state.status, state.error = status, False
        return jsonify(ok=True)
    except Exception as error:
        state.status, state.error = f"Error: {error}", True
        return jsonify(ok=False, message=str(error))
    finally:
        state.busy = False


# --------------------------------------------------------------------------
# routes


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.route("/stream")
def stream():
    return Response(mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/maps")
def api_maps():
    with_tasks = sorted(m for m in MAPS
                        if any(os.path.isdir(os.path.join(root, m))
                               for root in state.task_dirs))
    return jsonify(maps=MAPS, with_tasks=with_tasks, current=state.map_name)


@app.route("/api/tasks")
def api_tasks():
    map_name = request.args.get("map", state.map_name) or ""
    tasks, seen = [], set()
    for root in state.task_dirs:
        folder = os.path.join(root, map_name)
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if not name.endswith(".json") or name in seen:
                continue
            seen.add(name)
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                data = json.load(f)
            stem = name[:-len(".json")]
            thumb = thumb_path(map_name, stem)
            tasks.append({"name": name, "stem": stem, "type": data.get("Type"),
                          "instruction": data.get("Instruction", ""),
                          "thumb": thumb is not None})
    tasks.sort(key=lambda t: (t["type"] if t["type"] is not None else 99, t["name"]))
    return jsonify(map=map_name, tasks=tasks)


def thumb_path(map_name, stem):
    """The start view of a task: the first frame of its recorded demonstration."""
    for root in state.preview_dirs:
        path = os.path.join(root, map_name, stem, "000.jpg")
        if os.path.isfile(path):
            return path
    return None


@app.route("/api/thumb")
def api_thumb():
    map_name = os.path.basename(request.args.get("map", ""))
    stem = os.path.basename(request.args.get("task", ""))
    path = thumb_path(map_name, stem)
    if path is None:
        return Response(status=404)
    return send_file(path, mimetype="image/jpeg", max_age=3600)


@app.route("/api/status")
def api_status():
    task = None
    if state.task is not None:
        task = {"name": state.task_name,
                "type": state.task.get("Type"),
                "type_name": TYPE_NAMES.get(state.task.get("Type"), "Task"),
                "instruction": state.task.get("Instruction", ""),
                "start_pose": state.task.get("Start_Pose")}
    return jsonify(status=state.status, error=state.error, busy=state.busy,
                   mode=state.mode, map=state.map_name, task=task,
                   pose=state.pose, last_actions=state.last_actions)


@app.route("/api/action", methods=["POST"])
def api_action():
    action = (request.json or {}).get("action")
    if action not in ACTIONS:
        return jsonify(ok=False, message=f"unknown action {action}")
    if state.mode == "free":
        if action in INTERACTIONS:
            state.pending = action
            return jsonify(ok=True)
        return jsonify(ok=False, message="Free Move: hold the movement keys instead")
    return run_locked(standard_action, action, status=action)


@app.route("/api/mode", methods=["POST"])
def api_mode():
    mode = (request.json or {}).get("mode")
    if mode not in ("standard", "free"):
        return jsonify(ok=False, message=f"unknown mode {mode}")
    if state.busy:
        return jsonify(ok=False, message="busy")
    if mode == "free":
        start_free()
    else:
        stop_free()
    return jsonify(ok=True)


@app.route("/api/keys", methods=["POST"])
def api_keys():
    keys = (request.json or {}).get("keys") or {}
    state.keys = {k: bool(v) for k, v in keys.items()}
    state.keys_time = time.time()
    return jsonify(ok=True)


@app.route("/api/load_map", methods=["POST"])
def api_load_map():
    name = (request.json or {}).get("map")
    if name not in MAPS:
        return jsonify(ok=False, message=f"unknown map {name}")
    stop_free()
    state.status = f"Loading {name}"
    return run_locked(load_free_map, name)


@app.route("/api/load_task", methods=["POST"])
def api_load_task():
    body = request.json or {}
    map_name, task_name = body.get("map"), body.get("task")
    if find_task(map_name, task_name) is None:
        return jsonify(ok=False, message="unknown task")
    stop_free()
    state.status = "Loading task"
    return run_locked(load_task, map_name, task_name)


@app.route("/api/restart", methods=["POST"])
def api_restart():
    stop_free()
    state.status = "Back to start"
    if state.task_name:
        return run_locked(load_task, state.map_name, state.task_name)
    return run_locked(load_free_map, state.map_name)


# --------------------------------------------------------------------------
# page

PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EmbRACE Playground</title>
<style>
:root{
  --bg:#f4f5f7;--card:#fff;--line:#e5e7eb;--line2:#d1d5db;--text:#111827;--muted:#6b7280;--subtle:#9ca3af;
  --soft:#f9fafb;--dark:#111827;--focus:#4f46e5;--focus-bg:#eef2ff;
  --t0:#ef4444;--t0bg:#fee2e2;--t0fg:#b91c1c; --t1:#8b5cf6;--t1bg:#ede9fe;--t1fg:#6d28d9;
  --t2:#3b82f6;--t2bg:#dbeafe;--t2fg:#1d4ed8; --t3:#22c55e;--t3bg:#dcfce7;--t3fg:#15803d;
  --t4:#eab308;--t4bg:#fef9c3;--t4fg:#a16207; --t5:#f97316;--t5bg:#ffedd5;--t5fg:#c2410c;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);
  font:15px/1.45 Inter,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
button,select{font:inherit;color:inherit}
header{height:62px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;
  justify-content:space-between;padding:0 24px;gap:16px}
.brand{display:flex;align-items:center;gap:12px;min-width:0}
.brand b{font-size:19px;letter-spacing:-.01em;white-space:nowrap}
.conn{display:flex;align-items:center;gap:7px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dot{width:9px;height:9px;border-radius:50%;background:#22c55e;display:inline-block;flex:none}
.dot.busy{background:#f59e0b}.dot.err{background:#ef4444}
.hk{display:flex;align-items:center;gap:6px;color:var(--muted);flex-wrap:wrap;justify-content:flex-end}
.hk span{margin:0 10px 0 4px}
kbd{font:600 12px var(--mono);min-width:24px;height:24px;padding:0 6px;display:inline-grid;place-items:center;
  border:1px solid var(--line2);border-bottom-width:2px;border-radius:6px;background:#fff;color:var(--text)}
main{display:grid;grid-template-columns:360px minmax(0,1fr) 360px;gap:18px;padding:18px;
  height:calc(100vh - 62px);grid-template-areas:"left center right"}
.col{min-height:0;overflow:auto;display:flex;flex-direction:column;gap:18px}
.left{grid-area:left}.center{grid-area:center;overflow:hidden}.right{grid-area:right}
.vcard{flex:1 1 auto;min-height:0;display:flex;flex-direction:column}
.vwrap{flex:1 1 auto;min-height:0;display:flex;align-items:center;justify-content:center}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
.card-h{display:flex;align-items:center;justify-content:space-between;gap:10px;
  padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid var(--line)}
h2{font-size:17px;margin:0;letter-spacing:-.01em}
.meta{color:var(--subtle);font:13px var(--mono)}
.list{display:flex;flex-direction:column;min-height:0;flex:1}
.envrow{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.envrow label{color:var(--muted);white-space:nowrap}
select{flex:1;min-width:0;height:40px;border:1px solid var(--line2);border-radius:9px;background:#fff;padding:0 10px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.chip{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:4px 10px;font-size:13.5px;
  color:var(--muted);cursor:pointer}
.chip.on{background:#eef2f7;border-color:var(--text);color:var(--text);font-weight:600}
.tasks{display:flex;flex-direction:column;gap:6px;overflow:auto;min-height:0;flex:1;margin:0 -8px;padding:0 8px}
.tcard{display:flex;gap:12px;padding:9px;border:2px solid transparent;border-radius:12px;cursor:pointer;text-align:left;
  background:transparent;width:100%}
.tcard:hover{background:var(--soft)}
.tcard.sel{border-color:var(--text);background:#f8fafc}
.thumb{width:120px;height:90px;border-radius:7px;flex:none;object-fit:cover;background:#e5e7eb}
.tbody{min-width:0;display:flex;flex-direction:column;gap:5px}
.tins{font-size:14px;color:#374151;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.badge{display:inline-flex;align-items:center;gap:6px;font-weight:600;font-size:12.5px;padding:2px 8px;border-radius:6px;
  width:max-content;white-space:nowrap}
.badge i{width:8px;height:8px;border-radius:50%;display:inline-block}
.t0{background:var(--t0bg);color:var(--t0fg)}.t0 i{background:var(--t0)}
.t1{background:var(--t1bg);color:var(--t1fg)}.t1 i{background:var(--t1)}
.t2{background:var(--t2bg);color:var(--t2fg)}.t2 i{background:var(--t2)}
.t3{background:var(--t3bg);color:var(--t3fg)}.t3 i{background:var(--t3)}
.t4{background:var(--t4bg);color:var(--t4fg)}.t4 i{background:var(--t4)}
.t5{background:var(--t5bg);color:var(--t5fg)}.t5 i{background:var(--t5)}
.empty{color:var(--subtle);padding:18px 4px;text-align:center}
.btn{height:42px;border:1px solid var(--line2);background:#fff;border-radius:9px;padding:0 14px;font-weight:600;cursor:pointer}
.btn:hover:not(:disabled){border-color:var(--text)}
.btn:disabled{opacity:.45;cursor:default}
.btn.full{width:100%;margin-top:12px}
.btn .kk{font:600 11px var(--mono);color:var(--subtle);margin-left:8px}
.view{position:relative;border-radius:10px;overflow:hidden;background:#dfe3e8;width:100%;aspect-ratio:4/3;flex:none}
.view img{width:100%;height:100%;display:block;object-fit:contain}
.ovl{position:absolute;inset:0;display:none;place-items:center;background:rgba(255,255,255,.55);
  font-weight:600;color:var(--text);backdrop-filter:blur(1px)}
.ovl.on{display:grid}
.modepill{position:absolute;left:12px;top:12px;background:rgba(17,24,39,.72);color:#fff;font-size:12.5px;
  font-weight:600;padding:4px 10px;border-radius:999px}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:10px;padding:3px;background:var(--soft)}
.seg button{border:0;background:transparent;border-radius:7px;padding:6px 14px;font-weight:600;color:var(--muted);cursor:pointer}
.seg button.on{background:#fff;color:var(--text);box-shadow:0 1px 2px rgba(0,0,0,.08),0 0 0 1px var(--line2)}
.hint{color:var(--muted);font-size:13.5px;margin:-4px 0 12px}
.pad{display:grid;grid-template-columns:repeat(4,minmax(0,1fr)) minmax(0,1.3fr);grid-template-rows:56px 56px;gap:10px}
.k{position:relative;height:56px;border:1px solid var(--line2);background:#fff;border-radius:10px;cursor:pointer;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-weight:600;font-size:14.5px;
  user-select:none;touch-action:none}
.k small{font-size:15px;line-height:1;color:#374151}
.k .kk{position:absolute;top:5px;right:7px;font:600 10.5px var(--mono);color:var(--subtle)}
.k:hover:not(:disabled){border-color:var(--text)}
.k.on{background:var(--focus-bg);border-color:var(--focus)}
.k:disabled{opacity:.4;cursor:default}
.stack{grid-column:5;grid-row:1 / span 2;display:grid;grid-template-rows:repeat(3,minmax(0,1fr));gap:6px}
.stack .k{height:auto;font-size:14px}.stack .k .kk{top:50%;transform:translateY(-50%)}
.gap{visibility:hidden}
.posebar{margin-top:12px;border:1px solid var(--line);background:var(--soft);border-radius:10px;padding:10px 14px;
  display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--muted);font-size:14px}
.posebar b{font:600 14px var(--mono);color:var(--text);margin-left:4px}
.instr{font-size:19px;line-height:1.5;border-left:3px solid var(--line2);padding:4px 0 4px 16px;min-height:60px}
.instr.none{font-size:15px;color:var(--muted)}
.pgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px 10px}
.pgrid .lab{text-align:center;color:var(--subtle);font-size:13px}
.pgrid .val{text-align:center;font:500 15px var(--mono);background:var(--soft);border:1px solid var(--line);
  border-radius:8px;padding:7px 4px}
.pill{font-size:12.5px;font-weight:600;border:1px solid var(--line2);border-radius:999px;padding:2px 10px;color:#374151}
.trail{display:flex;flex-wrap:wrap;gap:5px}
.trail span{font:12px var(--mono);background:var(--soft);border:1px solid var(--line);border-radius:6px;padding:2px 6px;color:#374151}
.trail .none{background:none;border:0;color:var(--subtle);font:14px/1.45 Inter,system-ui,sans-serif;padding:0}
@media (max-width:1280px){
  main{grid-template-columns:320px minmax(0,1fr);grid-template-areas:"left center" "left right";height:auto}
  .col,.center{overflow:visible}.left{max-height:calc(100vh - 98px);position:sticky;top:18px}
  .vcard,.vwrap{flex:none}
}
@media (max-width:860px){
  header{height:auto;padding:12px 16px;flex-wrap:wrap}.hk{display:none}
  main{grid-template-columns:minmax(0,1fr);grid-template-areas:"center" "right" "left";padding:12px;gap:12px}
  .left{max-height:none;position:static}
  .pad{grid-template-columns:repeat(4,minmax(0,1fr));grid-template-rows:none}
  .stack{grid-column:1 / -1;grid-row:auto;grid-template-rows:none;grid-template-columns:repeat(3,1fr)}
  .stack .k{height:48px}
}
</style></head><body>
<header>
  <div class="brand">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2.2 5-4.8 2 2.2-5z"/></svg>
    <b>EmbRACE Playground</b>
    <span class="conn"><i class="dot" id="dot"></i><span id="env">UnrealZoo</span></span>
  </div>
  <div class="hk">
    <kbd>I</kbd><kbd>K</kbd><kbd>J</kbd><kbd>L</kbd><span>Move / Turn</span>
    <kbd>&uarr;</kbd><kbd>&darr;</kbd><span>Look</span>
    <kbd>O</kbd><kbd>P</kbd><kbd>N</kbd><span>Door / Pick / Drop</span>
  </div>
</header>
<main>
  <aside class="col left">
    <section class="card list">
      <div class="card-h"><h2>Tasks</h2><span class="meta" id="count"></span></div>
      <div class="envrow"><label for="map">Environment</label><select id="map"></select></div>
      <div class="chips" id="chips"></div>
      <div class="tasks" id="tasks"></div>
      <button class="btn full" id="roam">Free roam in this environment</button>
    </section>
  </aside>
  <section class="col center">
    <div class="card vcard">
      <div class="card-h"><h2>Egocentric View</h2><span class="meta" id="vmeta">640 &times; 480</span></div>
      <div class="vwrap" id="vwrap"><div class="view" id="viewbox"><img id="view" src="/stream" alt="Egocentric view">
        <span class="modepill" id="mpill">Standard</span><div class="ovl" id="ovl">Loading&hellip;</div></div></div>
    </div>
    <div class="card">
      <div class="card-h"><h2>Agent Control</h2>
        <div class="seg" id="seg"><button data-mode="standard">Standard</button><button data-mode="free">Free Move</button></div></div>
      <p class="hint" id="hint"></p>
      <div class="pad">
        <button class="k gap" tabindex="-1"></button>
        <button class="k" data-k="forward"><span class="kk">I</span><small>&#9650;</small>Forward</button>
        <button class="k gap" tabindex="-1"></button>
        <button class="k" data-k="lookup"><span class="kk">&uarr;</span><small>&uarr;</small>Look Up</button>
        <div class="stack">
          <button class="k" data-k="door"><span class="kk">O</span>Open Door</button>
          <button class="k" data-k="pick"><span class="kk">P</span>Pick</button>
          <button class="k" data-k="drop"><span class="kk">N</span>Drop</button>
        </div>
        <button class="k" data-k="left"><span class="kk">J</span><small>&#9664;</small>Turn Left</button>
        <button class="k" data-k="backward"><span class="kk">K</span><small>&#9660;</small>Backward</button>
        <button class="k" data-k="right"><span class="kk">L</span><small>&#9654;</small>Turn Right</button>
        <button class="k" data-k="lookdown"><span class="kk">&darr;</span><small>&darr;</small>Look Down</button>
      </div>
      <div class="posebar" id="pose">Current Pose</div>
    </div>
  </section>
  <aside class="col right">
    <div class="card">
      <div class="card-h"><h2>Task</h2><span id="tbadge"></span></div>
      <div class="instr none" id="instr">No task loaded. Pick a task on the left, or roam freely.</div>
    </div>
    <div class="card">
      <div class="card-h"><h2>Start Pose</h2><span class="pill">Fixed</span></div>
      <div class="pgrid" id="spose"></div>
      <button class="btn full" id="restart">Back to Start<span class="kk">&#9003;</span></button>
    </div>
    <div class="card">
      <div class="card-h"><h2>Recent Actions</h2></div>
      <div class="trail" id="trail"></div>
    </div>
  </aside>
</main>
<script>
const TYPES={0:'Basic',1:'Exploration',2:'Dynamic Spatial-Semantic',3:'Multi-stage',4:'Open Door',5:'Pick & Drop'};
const SHORT={0:'Basic',1:'Exploration',2:'Dynamic',3:'Multi-stage',4:'Open Door',5:'Pick & Drop'};
const CHIP={0:'Basic',1:'Explore',2:'Dynamic',3:'Multi-stage',4:'Door',5:'Pick & Drop'};
const KEYMAP={i:'forward',w:'forward',k:'backward',s:'backward',j:'left',a:'left',l:'right',d:'right',
  arrowup:'lookup',arrowdown:'lookdown',arrowleft:'left',arrowright:'right',
  o:'door',p:'pick',n:'drop',backspace:'restart'};
const ACTION={forward:'MoveForward',backward:'MoveBackward',left:'TurnLeft',right:'TurnRight',lookup:'LookUp',
  lookdown:'LookDown',door:'OpenDoor',pick:'Pick',drop:'Drop'};
const HOLD=new Set(['forward','backward','left','right','lookup','lookdown']);
const HINT={standard:'One key press or click is one discrete step, the same action a model takes.',
  free:'Hold a key or button to walk, turn and look around continuously.'};
const $=id=>document.getElementById(id);
let S={mode:'standard'},tasks=[],filter='all',held=new Set(),inflight=false;

async function post(url,body){
  try{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
    return await r.json();}catch(e){return {ok:false,message:String(e)};}
}
function badge(t,short){return t==null?'':`<span class="badge t${t}"><i></i>${(short?SHORT:TYPES)[t]}</span>`;}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

async function loadMaps(){
  const j=await (await fetch('/api/maps')).json();
  const sel=$('map');sel.innerHTML='';
  const withT=new Set(j.with_tasks);
  const add=(label,list)=>{const g=document.createElement('optgroup');g.label=label;
    list.forEach(m=>{const o=document.createElement('option');o.value=o.textContent=m;g.appendChild(o);});sel.appendChild(g);};
  if(j.with_tasks.length)add('With tasks',j.with_tasks);
  add('Free roam only',j.maps.filter(m=>!withT.has(m)));
  sel.value=j.current||j.with_tasks[0]||j.maps[0];
  await loadTasks();
}
async function loadTasks(){
  const j=await (await fetch('/api/tasks?map='+encodeURIComponent($('map').value))).json();
  tasks=j.tasks;renderChips();renderTasks();
}
function renderChips(){
  const present=[...new Set(tasks.map(t=>t.type))].sort();
  const items=[['all','All']].concat(present.map(t=>[String(t),CHIP[t]]));
  if(!items.some(i=>i[0]===filter))filter='all';
  $('chips').innerHTML=items.map(([k,l])=>`<button class="chip${k===filter?' on':''}" data-f="${k}">${esc(l)}</button>`).join('');
  $('chips').querySelectorAll('.chip').forEach(b=>b.onclick=()=>{filter=b.dataset.f;renderChips();renderTasks();});
}
function renderTasks(){
  const list=tasks.filter(t=>filter==='all'||String(t.type)===filter);
  $('count').textContent=tasks.length?`${tasks.length} task${tasks.length>1?'s':''}`:'';
  const cur=S.task&&S.map===$('map').value?S.task.name:null;
  $('tasks').innerHTML=list.length?list.map(t=>`<button class="tcard${t.name===cur?' sel':''}" data-t="${esc(t.name)}">
      ${t.thumb?`<img class="thumb" loading="lazy" src="/api/thumb?map=${encodeURIComponent($('map').value)}&task=${encodeURIComponent(t.stem)}" alt="">`
               :`<div class="thumb"></div>`}
      <div class="tbody">${badge(t.type,true)}<div class="tins">${esc(t.instruction)}</div></div></button>`).join('')
    :`<div class="empty">No tasks for this environment.<br>Use free roam to explore it.</div>`;
  $('tasks').querySelectorAll('.tcard').forEach(b=>b.onclick=()=>loadTask(b.dataset.t));
}
async function loadTask(name){
  if(S.busy)return;
  held.clear();
  await post('/api/load_task',{map:$('map').value,task:name});
  poll();
}
async function restart(){if(!S.busy){held.clear();await post('/api/restart');poll();}}
$('map').onchange=loadTasks;
$('roam').onclick=async()=>{if(!S.busy){held.clear();await post('/api/load_map',{map:$('map').value});poll();}};
$('restart').onclick=restart;
document.querySelectorAll('#seg button').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
async function setMode(m){if(m!==S.mode&&!S.busy){held.clear();await post('/api/mode',{mode:m});poll();}}

async function act(k){
  if(k==='restart'){restart();return;}
  const a=ACTION[k];if(!a||inflight)return;
  inflight=true;flash(k);
  try{await post('/api/action',{action:a});}finally{inflight=false;poll();}
}
function flash(k){const b=document.querySelector(`.k[data-k="${k}"]`);if(!b)return;b.classList.add('on');
  setTimeout(()=>{if(!held.has(k))b.classList.remove('on');},160);}
function sendKeys(){const o={};held.forEach(k=>o[k]=true);post('/api/keys',{keys:o});
  document.querySelectorAll('.k[data-k]').forEach(b=>b.classList.toggle('on',held.has(b.dataset.k)));}
setInterval(()=>{if(S.mode==='free'&&held.size)sendKeys();},150);
window.addEventListener('blur',()=>{if(held.size){held.clear();sendKeys();}});

document.querySelectorAll('.k[data-k]').forEach(b=>{
  const k=b.dataset.k;
  b.addEventListener('pointerdown',e=>{
    if(b.disabled)return;
    if(S.mode==='free'&&HOLD.has(k)){e.preventDefault();b.setPointerCapture(e.pointerId);held.add(k);sendKeys();}
  });
  const up=()=>{if(held.delete(k))sendKeys();};
  b.addEventListener('pointerup',up);b.addEventListener('pointercancel',up);
  b.addEventListener('click',()=>{if(b.disabled)return;if(!(S.mode==='free'&&HOLD.has(k)))act(k);});
});
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='SELECT'||e.ctrlKey||e.metaKey||e.altKey)return;
  const k=KEYMAP[e.key.toLowerCase()];if(!k)return;
  e.preventDefault();
  if(S.mode==='free'&&HOLD.has(k)){if(!held.has(k)){held.add(k);sendKeys();}return;}
  if(e.repeat)return;
  act(k);
});
document.addEventListener('keyup',e=>{
  const k=KEYMAP[e.key.toLowerCase()];
  if(k&&held.delete(k))sendKeys();
});

function renderPose(p){
  const n=['X','Y','Z','Pitch','Yaw','Roll'];
  $('pose').innerHTML='Current Pose'+(p?n.map((k,i)=>`<span>${k}<b>${Number(p[i]).toFixed(1)}</b></span>`).join('')
                                      :' <b>&ndash;</b>');
}
function renderStart(p){
  const n=['X','Y','Z','Pitch','Yaw','Roll'];
  $('spose').innerHTML=[0,1].map(r=>n.slice(r*3,r*3+3).map(k=>`<div class="lab">${k}</div>`).join('')+
    n.slice(r*3,r*3+3).map((k,i)=>`<div class="val">${p?Number(p[r*3+i]).toFixed(1):'&ndash;'}</div>`).join('')).join('');
}
function render(s){
  const prevTask=S.task&&S.task.name, prevMap=S.map;
  S=s;
  $('dot').className='dot'+(s.error?' err':s.busy?' busy':'');
  $('env').textContent='UnrealZoo \u00b7 '+(s.map||'\u2013')+(s.busy?' \u00b7 '+s.status:'');
  document.querySelectorAll('#seg button').forEach(b=>b.classList.toggle('on',b.dataset.mode===s.mode));
  $('mpill').textContent=s.mode==='free'?'Free Move':'Standard';
  $('hint').textContent=HINT[s.mode];
  $('ovl').classList.toggle('on',!!s.busy);$('ovl').textContent=(s.status||'Loading')+'\u2026';
  document.querySelectorAll('.k[data-k]').forEach(b=>b.disabled=!!s.busy);
  $('roam').disabled=$('restart').disabled=!!s.busy;
  if(s.task){
    $('tbadge').innerHTML=badge(s.task.type);
    $('instr').className='instr';$('instr').textContent=s.task.instruction;
    $('instr').style.borderLeftColor=`var(--t${s.task.type})`;
  }else{
    $('tbadge').innerHTML='';$('instr').className='instr none';$('instr').style.borderLeftColor='';
    $('instr').textContent='No task loaded. Pick a task on the left, or roam freely.';
  }
  renderStart(s.task&&s.task.start_pose);
  renderPose(s.pose);
  $('trail').innerHTML=s.last_actions&&s.last_actions.length?s.last_actions.map(a=>`<span>${a}</span>`).join('')
    :'<span class="none">No actions yet.</span>';
  if(s.map&&s.map!==prevMap&&$('map').value!==s.map){$('map').value=s.map;loadTasks();}
  else if((s.task&&s.task.name)!==prevTask)renderTasks();
}
function fitView(){
  const w=$('vwrap'),v=$('viewbox');
  if(matchMedia('(max-width:1280px)').matches){v.style.width='100%';v.style.height='';return;}
  const vw=Math.max(240,Math.min(w.clientWidth,w.clientHeight*4/3));
  v.style.width=vw+'px';v.style.height=(vw*3/4)+'px';
}
new ResizeObserver(fitView).observe($('vwrap'));window.addEventListener('resize',fitView);
async function poll(){try{render(await (await fetch('/api/status')).json());}catch(e){$('dot').className='dot err';}}
setInterval(poll,400);
loadMaps().then(poll);
</script></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="EmbRACE web playground")
    parser.add_argument("--ip", default="127.0.0.1", help="UnrealCV server IP")
    parser.add_argument("--port", type=int, default=9000, help="UnrealCV port")
    parser.add_argument("--map", default="IndustrialArea", help="Map loaded at start")
    parser.add_argument("--task_dirs", nargs="+",
                        default=[os.path.join(PROJECT_ROOT, "datas", "benchmark", "task"),
                                 os.path.join(PROJECT_ROOT, "datas", "dataset", "task")],
                        help="Task directories (one folder per map), listed together")
    parser.add_argument("--preview_dirs", nargs="+",
                        default=[os.path.join(PROJECT_ROOT, "datas", "benchmark", "trajectory"),
                                 os.path.join(PROJECT_ROOT, "datas", "dataset", "trajectory")],
                        help="Task thumbnails, the first frame of each demonstration: "
                             "<dir>/<Map>/<task>/000.jpg")
    parser.add_argument("--web_port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address (use 0.0.0.0 to expose on the LAN)")
    args = parser.parse_args()

    state.task_dirs = args.task_dirs
    state.preview_dirs = args.preview_dirs
    print(f"[>>>] Connecting to UE server at {args.ip}:{args.port} ...")
    state.ch_api = Character_API(ip=args.ip, port=args.port)
    print(f"[>>>] Loading map {args.map} ...")
    with state.lock:
        load_free_map(args.map)
    state.status = "Ready"
    threading.Thread(target=refresh_loop, daemon=True).start()
    print(f"[>>>] Playground ready: http://localhost:{args.web_port}")
    app.run(host=args.host, port=args.web_port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
