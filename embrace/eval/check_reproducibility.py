"""Replay recorded demonstrations and check that this installation reproduces them exactly.

Each task is set up, and each recorded action executed, by the evaluator's own code
(``EvalVLM.load_task`` and ``EvalVLM._execute``), so a task that reproduces here starts and
steps exactly as it does during evaluation. After every action the agent position is compared
with the recorded ``Pose_Trajectory``, together with the door state of an Open Door task and the
object position of a Pick & Drop task. The simulation is deterministic, so a correct
installation reproduces every recorded value exactly and the default tolerance is zero.

    python -m embrace.eval.check_reproducibility --port 9000
    python -m embrace.eval.check_reproducibility --port 9000 --task_dir datas/benchmark/task \
        --traj_dir datas/benchmark/trajectory --map IndustrialArea
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import tempfile
from types import SimpleNamespace

from embrace.core import Character_API
from embrace.eval.eval_vlm import EvalVLM


def max_position_diff(replayed, recorded):
    """Largest distance between matching positions, or inf when the lists do not line up."""
    if len(replayed) != len(recorded) or any(p is None for p in replayed):
        return math.inf
    return max((math.dist(a[:3], b[:3]) for a, b in zip(replayed, recorded)), default=0.0)


def replay(evaluator, map_name, task_file, record):
    """Replay one recorded demonstration and compare it with the recording."""
    evaluator.map_name = map_name
    evaluator.task_list = [task_file]
    evaluator.load_task(0)
    for action in record["Action"]:
        evaluator._execute(action, "")
    result = {"agent": max_position_diff(evaluator.traj_pose_list, record["Pose_Trajectory"])}
    if record.get("Type") == 4:
        result["door"] = evaluator.door_state_list == record.get("Door_State_Trajectory")
    elif record.get("Type") == 5:
        result["pd"] = max_position_diff(evaluator.pd_pose_list,
                                         record.get("PD_Pose_Trajectory") or [])
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Check that this installation reproduces recorded demonstrations exactly")
    parser.add_argument("--ip", default="127.0.0.1", help="UnrealCV server IP")
    parser.add_argument("--port", type=int, default=9000, help="UnrealCV port")
    parser.add_argument("--task_dir", default="./reproducibility/task",
                        help="Task files, one folder per map")
    parser.add_argument("--traj_dir", default="./reproducibility/trajectory",
                        help="Recorded demonstrations, <map>/<task>/infos.json")
    parser.add_argument("--map", nargs="+", default=None,
                        help="Map(s) to replay (default: every map folder in --task_dir)")
    parser.add_argument("--tolerance", type=float, default=0.0,
                        help="Largest accepted position difference, in uu (default 0)")
    args = parser.parse_args()

    maps = args.map or sorted(d for d in os.listdir(args.task_dir)
                              if os.path.isdir(os.path.join(args.task_dir, d)))
    jobs = []
    for map_name in maps:
        for task_file in sorted(os.listdir(os.path.join(args.task_dir, map_name))):
            if not task_file.endswith(".json"):
                continue
            record_path = os.path.join(args.traj_dir, map_name, task_file[:-len(".json")],
                                       "infos.json")
            if os.path.isfile(record_path):
                jobs.append((map_name, task_file, record_path))
            else:
                print(f"[!!!] No recording for {map_name}/{task_file}, skipped")
    if not jobs:
        sys.exit("[!!!] Nothing to replay")

    print(f"[>>>] Connecting to UE server at {args.ip}:{args.port} ...")
    ch_api = Character_API(ip=args.ip, port=args.port)
    # The evaluator only reads the model's name and reply tag, and nothing is saved.
    scratch = tempfile.mkdtemp(prefix="embrace_reproducibility_")
    evaluator = EvalVLM(ch_api, SimpleNamespace(model="reproducibility-check",
                                                route={"reasoning_tag": "think"}),
                        task_dir=args.task_dir, save_dir=scratch)
    lines, passed, agent_max, pd_max = [], 0, 0.0, 0.0
    try:
        for map_name, task_file, record_path in jobs:
            with open(record_path, encoding="utf-8") as f:
                record = json.load(f)
            result = replay(evaluator, map_name, task_file, record)
            agent_max = max(agent_max, result["agent"])
            ok = result["agent"] <= args.tolerance
            line = (f"{map_name}/{task_file[:-len('.json')]}  T{record.get('Type')}  "
                    f"{len(record['Action'])} actions  agent_max={result['agent']:.3f} uu")
            if "door" in result:
                ok = ok and result["door"]
                line += "  door states " + ("match" if result["door"] else "DIFFER")
            if "pd" in result:
                pd_max = max(pd_max, result["pd"])
                ok = ok and result["pd"] <= args.tolerance
                line += f"  pd_max={result['pd']:.3f} uu"
            passed += ok
            lines.append(f"[{'PASS' if ok else 'FAIL'}] {line}")
            print(lines[-1], flush=True)
    finally:
        if ch_api.client.isconnected():
            ch_api.client.disconnect()
        shutil.rmtree(scratch, ignore_errors=True)

    print("\n" + "\n".join(lines))
    print(f"Global max agent pos diff: {agent_max:.3f}")
    print(f"Global max PD pos diff: {pd_max:.3f}")
    print(f"[>>>] {passed}/{len(jobs)} demonstrations reproduced"
          + (" exactly" if args.tolerance == 0 else f" within {args.tolerance} uu"))
    sys.exit(0 if passed == len(jobs) else 1)


if __name__ == "__main__":
    main()
