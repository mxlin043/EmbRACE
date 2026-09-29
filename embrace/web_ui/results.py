"""Browse evaluation results step by step in the browser.

Reads the folders the evaluator writes, ``runs/<Map>/<task>/<model>/`` (``infos.json`` and the
frames ``000.jpg`` ...), and serves a page that lists the benchmark tasks with each model's
outcome, walks through any episode step by step (egocentric view, reasoning, action), puts two
models side by side, and tabulates success per task type. Episodes are scored with the scorer's
own ``score_episode``, or read from the ``metrics.json`` it wrote when that is newer than the
record. Nothing is written. The folder is rescanned while the page is open, so the page also
follows an evaluation that is still running.

    python -m embrace.web_ui.results --runs runs
    # open http://localhost:8090
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import threading
import time
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_from_directory

from embrace.eval.score_metrics import score_episode

PAGE = Path(__file__).with_name("results.html")
FRAME = re.compile(r"\d{3}\.jpg")
REGION_IMAGES = ("xy_region.png", "ue_top_down_overlay.jpg")
EPISODE_COLUMNS = ["map", "task", "model", "steps", "sr", "os", "ne", "tl", "spl"]

app = Flask(__name__)


class ResultIndex:
    """The episodes under the runs root, scored once per version of their record."""

    def __init__(self, runs, task_dir, region_dir, models, rescan_s):
        self.runs, self.task_dir, self.region_dir = Path(runs), Path(task_dir), Path(region_dir)
        self.models = models
        self.rescan_s = rescan_s
        self.cache = {}                 # infos.json path -> (mtime, episode row)
        self.rows, self.scanned_at = [], None
        self.pending = 0
        self.lock = threading.Lock()
        self.tasks = self._load_tasks()

    def _load_tasks(self):
        tasks = []
        for path in sorted(self.task_dir.glob("*/*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            tasks.append([path.parent.name, path.stem, data.get("Type"),
                          data.get("Instruction", ""), data.get("PD_ID")])
        return tasks

    def _wanted(self, model):
        return not self.models or any(fnmatch.fnmatch(model, p) for p in self.models)

    def _score(self, infos, map_name, stem, model):
        folder = infos.parent
        record = json.loads(infos.read_text(encoding="utf-8"))
        metrics_path = folder / "metrics.json"
        metrics = None
        if metrics_path.exists() and metrics_path.stat().st_mtime >= infos.stat().st_mtime:
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metrics = None
        if metrics is None:
            try:
                metrics = score_episode(map_name, stem, record, published_root=self.region_dir)
            except (OSError, ValueError, KeyError):
                metrics = {}
        ne = metrics.get("ne_uu")
        return [map_name, stem, model, len(record.get("Action") or []),
                metrics.get("sr"), metrics.get("os"),
                None if ne is None else round(ne / 100.0, 3),
                metrics.get("tl"), metrics.get("spl_term")]

    def scan(self):
        found = []
        for infos in self.runs.glob("*/*/*/infos.json"):
            map_name, stem, model = infos.parts[-4], infos.parts[-3], infos.parts[-2]
            if self._wanted(model):
                found.append((infos, map_name, stem, model))
        todo = [f for f in found if self.cache.get(f[0], (None,))[0] != f[0].stat().st_mtime]
        self.pending = len(todo)
        for infos, map_name, stem, model in todo:
            try:
                mtime = infos.stat().st_mtime
                self.cache[infos] = (mtime, self._score(infos, map_name, stem, model))
            except (OSError, json.JSONDecodeError):
                pass                    # a record still being written is picked up next time
            self.pending -= 1
        with self.lock:
            self.rows = [self.cache[f[0]][1] for f in found if f[0] in self.cache]
            self.scanned_at = time.time()

    def loop(self):
        while True:
            try:
                self.scan()
            except Exception as error:  # keep serving the last good index
                print(f"[!!!] Rescan failed: {error}")
            time.sleep(self.rescan_s)

    def snapshot(self):
        with self.lock:
            rows, scanned_at = list(self.rows), self.scanned_at
        return {"task_columns": ["map", "task", "type", "instruction", "pd_id"],
                "tasks": self.tasks, "episode_columns": EPISODE_COLUMNS,
                "episodes": rows, "scanned_at": scanned_at, "pending": self.pending,
                "refresh_s": self.rescan_s}


INDEX: ResultIndex | None = None


def _name(value):
    """A single path component taken from the request, never a path."""
    if not value or "/" in value or "\\" in value or value in (".", ".."):
        abort(404)
    return value


@app.route("/")
def page():
    return Response(PAGE.read_text(encoding="utf-8"), mimetype="text/html")


@app.route("/api/index")
def api_index():
    return jsonify(INDEX.snapshot())


@app.route("/api/episode")
def api_episode():
    map_name, stem, model = (_name(request.args.get(k)) for k in ("map", "task", "model"))
    infos = INDEX.runs / map_name / stem / model / "infos.json"
    if not infos.is_file():
        abort(404)
    record = json.loads(infos.read_text(encoding="utf-8"))
    return jsonify({
        "Action": record.get("Action") or [],
        "Thinking": record.get("Thinking") or record.get("Rationale") or [],
        "Pose_Trajectory": record.get("Pose_Trajectory") or [],
        "Door_State_Trajectory": record.get("Door_State_Trajectory"),
        "PD_Dist_2D": record.get("PD_Dist_2D"),
    })


@app.route("/api/regions")
def api_regions():
    map_name, stem = _name(request.args.get("map")), _name(request.args.get("task"))
    folder = INDEX.region_dir / map_name / stem
    stages = []
    for stage, prefix in (("midway", "midway_"), ("final", "final_"), ("final", "")):
        files = [prefix + name for name in REGION_IMAGES]
        if all((folder / f).is_file() for f in files) and stage not in [s[0] for s in stages]:
            stages.append([stage] + files)
    return jsonify(stages=stages)


@app.route("/frames/<map_name>/<stem>/<model>/<frame>")
def frames(map_name, stem, model, frame):
    if not FRAME.fullmatch(frame):
        abort(404)
    return send_from_directory(INDEX.runs.resolve() / _name(map_name) / _name(stem) / _name(model),
                               frame, max_age=3600)


@app.route("/regions/<map_name>/<stem>/<image>")
def regions(map_name, stem, image):
    if not any(image == p + n for p in ("", "midway_", "final_") for n in REGION_IMAGES):
        abort(404)
    return send_from_directory(INDEX.region_dir.resolve() / _name(map_name) / _name(stem),
                               image, max_age=3600)


def main():
    global INDEX
    parser = argparse.ArgumentParser(description="Browse evaluation results step by step")
    parser.add_argument("--runs", default="runs", help="Result root written by the evaluator")
    parser.add_argument("--task_dir", default="datas/benchmark/task",
                        help="Benchmark tasks, one folder per map")
    parser.add_argument("--region_dir", default="datas/benchmark/success_region",
                        help="Success regions, used to score and to show the target area")
    parser.add_argument("--models", nargs="+", default=None, metavar="PATTERN",
                        help="Only these model folders (names or globs)")
    parser.add_argument("--refresh", type=float, default=10.0,
                        help="Seconds between rescans of --runs (default 10)")
    parser.add_argument("--web_port", type=int, default=8090)
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address; 0.0.0.0 opens the page to other machines")
    args = parser.parse_args()

    INDEX = ResultIndex(args.runs, args.task_dir, args.region_dir, args.models, args.refresh)
    threading.Thread(target=INDEX.loop, daemon=True).start()
    print(f"[>>>] {len(INDEX.tasks)} benchmark tasks, results from {Path(args.runs).resolve()}")
    print(f"[>>>] Open http://localhost:{args.web_port}")
    app.run(host=args.host, port=args.web_port, threaded=True)


if __name__ == "__main__":
    main()
