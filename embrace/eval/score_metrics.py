"""Score evaluation episodes: SR, OS, NE, TL, SPL.

Implements the metric definitions in ``README.md`` (6.6 Scoring).
Everything is read from two places and nothing else: the episode's own
``infos.json`` and the published success area of its task.  Expert
trajectories are not consulted -- the reference Z and the shortest-path length
ride along inside ``area.json``.

Two layers of output:

* per episode, ``metrics.json`` next to the episode, with the metrics and the
  intermediate quantities (path length, NE, the reference path length);
* one aggregate report holding only the five metrics.

All distances are UE units (uu); NE is converted to metres only when printed.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from embrace.eval.success_region import (
    is_task_success,
    load_success_area,
)


DEFAULT_RUNS_ROOT = Path("runs")

Z_TOLERANCE_UU = 100.0     # Z tolerance of the success predicate
HELD_UU = 30.0             # G_pd_drop_thres_dist
SR_RADIUS_UU = 220.0       # the region is the footprint dilated by this
UU_PER_METRE = 100.0
DEGENERATE_UU = 1.0        # guard; the ell=0 rule should keep this unreachable


# --------------------------------------------------------------------------
# geometry


def _distance_to_segment(point, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(point[0] - ax, point[1] - ay)
    t = max(0.0, min(1.0, ((point[0] - ax) * dx + (point[1] - ay) * dy)
                     / (dx * dx + dy * dy)))
    return math.hypot(point[0] - (ax + t * dx), point[1] - (ay + t * dy))


def _inside(point, ring) -> bool:
    contour = np.asarray(ring, dtype=np.float32)
    return cv2.pointPolygonTest(
        contour, (float(point[0]), float(point[1])), False) >= 0


def navigation_error_uu(point, footprints) -> float:
    """XY distance to the nearest target footprint; 0 inside one.

    ``NE <= SR_RADIUS_UU`` is exactly the XY half of the success predicate, so
    NE is the continuous form of SR.
    """
    best = math.inf
    for footprint in footprints:
        if _inside(point, footprint):
            return 0.0
        best = min(best, min(
            _distance_to_segment(point[:2], footprint[i],
                                 footprint[(i + 1) % len(footprint)])
            for i in range(len(footprint))
        ))
    return best


def path_length_uu(poses) -> float:
    return sum(math.dist(poses[i][:2], poses[i + 1][:2])
               for i in range(len(poses) - 1))


# --------------------------------------------------------------------------
# per-episode scoring


def _last_index(sequence, value) -> int:
    return len(sequence) - 1 - sequence[::-1].index(value)


def _held(distances) -> list[bool]:
    return [d is not None and d < HELD_UU for d in distances]


def score_episode(map_name: str, task_stem: str, episode: dict[str, Any],
                  *, published_root: Path | None = None) -> dict[str, Any]:
    """Return every metric for one episode."""

    actions = episode.get("Action") or []
    poses = episode.get("Pose_Trajectory") or []
    task_type = episode.get("Type")
    area_kwargs = {} if published_root is None else {"root": published_root}
    final = load_success_area(map_name, task_stem, **area_kwargs)

    result: dict[str, Any] = {
        "map": map_name, "task": task_stem, "type": task_type,
        "sr": 0, "os": 0,
        "tl": len(actions),
        "path_length_uu": round(path_length_uu(poses), 3) if poses else 0.0,
    }

    if len(poses) != len(actions) + 1:
        raise ValueError(f"{len(poses)} poses for {len(actions)} actions")

    result["ne_uu"] = round(
        navigation_error_uu(poses[-1], final["Target_Footprints"]), 3)
    if task_type == 3:
        try:
            midway = load_success_area(
                map_name, task_stem + "__midway", **area_kwargs)
            result["ne_midway_uu"] = None
        except (OSError, ValueError):
            midway = None
        if midway is not None and "MidwayTarget" in actions:
            declared = _last_index(actions, "MidwayTarget")
            result["ne_midway_uu"] = round(navigation_error_uu(
                poses[declared + 1], midway["Target_Footprints"]), 3)

    result["os"] = int(_oracle(map_name, task_stem, episode, area_kwargs))
    result["sr"] = int(_succeeded(map_name, task_stem, episode, area_kwargs))
    result["spl_term"] = round(_spl_term(result["sr"], result["path_length_uu"],
                                         final, result), 6)
    result["shortest_path_uu"] = final.get("Shortest_Path_UU")
    return result


def _at(map_name, stem, pose, area_kwargs, stage="final", pd_pose=None) -> bool:
    key = stem + ("__midway" if stage == "midway" else "")
    return is_task_success(map_name, key, pose, pd_object_pose=pd_pose,
                           z_tolerance_uu=Z_TOLERANCE_UU,
                           **({"root": area_kwargs["root"]}
                              if "root" in area_kwargs else {}))


def _succeeded(map_name, stem, episode, area_kwargs) -> bool:
    """The success predicate: Finish as the last action, taken inside the success
    area, plus the MidwayTarget, door or object condition of the task type."""
    actions = episode["Action"]
    poses = episode["Pose_Trajectory"]
    task_type = episode.get("Type")
    if not actions or actions[-1] != "Finish":
        return False
    fi = len(actions) - 1

    if task_type in (0, 1, 2):
        return _at(map_name, stem, poses[fi + 1], area_kwargs)

    if task_type == 3:
        if "MidwayTarget" not in actions:
            return False
        mi = _last_index(actions, "MidwayTarget")
        return (mi < fi and _at(map_name, stem, poses[mi + 1], area_kwargs, "midway")
                and _at(map_name, stem, poses[fi + 1], area_kwargs))

    if task_type == 4:
        door = episode.get("Door_State_Trajectory") or []
        return (len(door) == len(actions) + 1 and int(door[fi + 1] or 0) == 1
                and _at(map_name, stem, poses[fi + 1], area_kwargs))

    if task_type == 5:
        distances = episode.get("PD_Dist_2D") or []
        pd_poses = episode.get("PD_Pose_Trajectory") or []
        if len(distances) != len(actions) + 1 or len(pd_poses) != len(actions) + 1:
            return False
        held = _held(distances)
        pd_type = str(episode.get("PD_Type", "")).lower()
        if True not in held or pd_type not in ("p", "pd"):
            return False
        # Pick: still held at Finish. Pick and drop: picked up, then released by Finish.
        if held[fi + 1] != (pd_type == "p"):
            return False
        return _at(map_name, stem, poses[fi + 1], area_kwargs, pd_pose=pd_poses[fi + 1])

    return False


def _oracle(map_name, stem, episode, area_kwargs) -> bool:
    """Did the episode ever reach the goal state, declarations aside."""
    actions = episode["Action"]
    poses = episode["Pose_Trajectory"]
    task_type = episode.get("Type")

    if task_type in (0, 1, 2):
        return any(_at(map_name, stem, q, area_kwargs) for q in poses)
    if task_type == 3:
        first = None
        for index, pose in enumerate(poses):
            if _at(map_name, stem, pose, area_kwargs, "midway"):
                first = index
                break
        return first is not None and any(
            _at(map_name, stem, q, area_kwargs) for q in poses[first:])
    if task_type == 4:
        door = episode.get("Door_State_Trajectory") or []
        if len(door) != len(poses):
            return False
        return any(_at(map_name, stem, q, area_kwargs) and int(door[i] or 0) == 1
                   for i, q in enumerate(poses))
    if task_type == 5:
        distances = episode.get("PD_Dist_2D") or []
        pd_poses = episode.get("PD_Pose_Trajectory") or []
        if len(distances) != len(poses) or len(pd_poses) != len(poses):
            return False
        held = _held(distances)
        if str(episode.get("PD_Type", "")).lower() == "p":
            return any(held[i] and _at(map_name, stem, q, area_kwargs,
                                       pd_pose=pd_poses[i])
                       for i, q in enumerate(poses))
        picked = False
        for index, pose in enumerate(poses):
            if held[index]:
                picked = True
                continue
            if picked and _at(map_name, stem, pose, area_kwargs,
                              pd_pose=pd_poses[index]):
                return True
        return False
    return False


def _spl_term(success: int, walked_uu: float, area: dict[str, Any],
              result: dict[str, Any]) -> float:
    reference = area.get("Shortest_Path_UU")
    if reference is None:
        raise ValueError(
            f"{result['map']}/{result['task']}: area.json has no Shortest_Path_UU"
        )
    denominator = max(walked_uu, reference)
    if denominator <= DEGENERATE_UU:
        # The ell=0 rule should already have replaced a zero reference with the
        # expert's own path length, so reaching here means the data is broken.
        print(f"[!!!] degenerate SPL denominator: "
              f"{result['map']}/{result['task']}")
        return float(success)
    return success * reference / denominator


# --------------------------------------------------------------------------
# batch


def _group(records, key):
    grouped = collections.defaultdict(list)
    for record in records:
        grouped[record[key]].append(record)
    return grouped


def iter_episodes(runs_root: Path, maps: list[str] | None):
    for infos in sorted(Path(runs_root).rglob("infos.json")):
        parts = infos.parts
        if len(parts) < 4:
            continue
        map_name, task_stem, model = parts[-4], parts[-3], parts[-2]
        if maps is not None and map_name not in maps:
            continue
        yield infos, map_name, task_stem, model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--map", action="append", default=None, metavar="MAP")
    parser.add_argument("--report", type=Path, default=None,
                        help="Where to write the aggregate report")
    parser.add_argument("--no-per-episode", action="store_true",
                        help="Skip writing metrics.json next to each episode")
    args = parser.parse_args(argv)

    source = iter_episodes(args.runs_root, args.map)

    records: list[dict[str, Any]] = []
    no_area = 0
    failed: list[tuple[str, str, str, str]] = []
    for infos, map_name, task_stem, model in source:
        try:
            episode = json.loads(infos.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            failed.append((map_name, task_stem, model, str(error)[:90]))
            continue
        try:
            record = score_episode(map_name, task_stem, episode)
        except FileNotFoundError:
            # No published success area: this task is not part of the test set.
            no_area += 1
            continue
        except (ValueError, KeyError) as error:
            failed.append((map_name, task_stem, model, str(error)[:90]))
            continue
        record["model"] = model
        records.append(record)
        if not args.no_per_episode:
            (infos.parent / "metrics.json").write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")

    if not records:
        print("[!!!] No episode could be scored")
        return 1

    def aggregate(subset):
        n = len(subset)
        successes = [r for r in subset if r["sr"] == 1]
        ne = sorted(r["ne_uu"] for r in subset if r.get("ne_uu") is not None)
        return {
            "n": n,
            "SR": sum(r["sr"] for r in subset) / n,
            "OS": sum(r["os"] for r in subset) / n,
            "NE_mean_m": (sum(ne) / len(ne) / UU_PER_METRE) if ne else None,
            "NE_median_m": (ne[len(ne) // 2] / UU_PER_METRE) if ne else None,
            "TL_mean": sum(r["tl"] for r in subset) / n,
            "SPL": sum(r["spl_term"] for r in subset) / n,
            "success_TL_ratio": (
                sum(r["tl"] for r in successes) / len(successes)
                if successes else None),
        }

    print(f"{'model':<22}{'type':>6}{'n':>6}{'SR':>8}{'OS':>8}"
          f"{'NE mean(m)':>12}{'NE med(m)':>11}{'TL':>7}{'SPL':>8}")
    print("-" * 88)
    by_model = collections.defaultdict(list)
    for record in records:
        by_model[record["model"]].append(record)
    for model in sorted(by_model):
        subset = by_model[model]
        by_type = collections.defaultdict(list)
        for record in subset:
            by_type[record["type"]].append(record)
        for task_type in sorted(by_type, key=str):
            a = aggregate(by_type[task_type])
            print(f"{model:<22}{f'T{task_type}':>6}{a['n']:>6}{a['SR']:>8.3f}"
                  f"{a['OS']:>8.3f}{a['NE_mean_m']:>12.2f}"
                  f"{a['NE_median_m']:>11.2f}{a['TL_mean']:>7.1f}"
                  f"{a['SPL']:>8.3f}")
        a = aggregate(subset)
        print(f"{model:<22}{'ALL':>6}{a['n']:>6}{a['SR']:>8.3f}{a['OS']:>8.3f}"
              f"{a['NE_mean_m']:>12.2f}{a['NE_median_m']:>11.2f}"
              f"{a['TL_mean']:>7.1f}{a['SPL']:>8.3f}")
        print("-" * 88)

    if no_area:
        print(f"\n[>>>] {no_area} trajectory(ies) skipped: no published success "
              f"area, i.e. not part of the test set")
    if failed:
        print(f"\n[!!!] {len(failed)} episode(s) could not be scored:")
        for map_name, task_stem, model, error in failed[:10]:
            print(f"    {map_name}/{task_stem} [{model}]: {error}")
        if len(failed) > 10:
            print(f"    ... and {len(failed) - 10} more")

    if args.report:
        # The written report holds the five metrics, NE as a mean only.  The
        # median and the intermediate quantities are in the terminal output and
        # in each episode's metrics.json.
        def public(subset):
            a = aggregate(subset)
            return {
                "n": a["n"], "SR": a["SR"], "OS": a["OS"],
                "NE_m": a["NE_mean_m"], "TL": a["TL_mean"], "SPL": a["SPL"],
            }

        report = {
            "overall": public(records),
            "by_model": {
                model: {
                    "overall": public(subset),
                    "by_type": {
                        f"T{task_type}": public(group)
                        for task_type, group in sorted(
                            _group(subset, "type").items(), key=lambda kv: str(kv[0]))
                    },
                }
                for model, subset in by_model.items()
            },
        }
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"\n[>>>] Public report written to {args.report} "
              f"(five metrics, NE mean only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
