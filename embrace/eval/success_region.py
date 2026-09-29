"""Runtime loader and XY predicate for published task success areas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np


# The success regions of the benchmark, as extracted from the dataset release
# (scripts/download_data.sh): datas/benchmark/success_region/<Env>/<Task>/area.json.
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "datas" / "benchmark" / "success_region"


CompiledRegion = tuple[
    np.ndarray,
    tuple[np.ndarray, ...],
    tuple[float, float, float, float],
]


def _compile_regions(
    regions: Sequence[dict[str, Any]],
) -> tuple[CompiledRegion, ...]:
    compiled: list[CompiledRegion] = []
    for polygon in regions:
        outer = np.ascontiguousarray(
            polygon["Outer_Boundary"], dtype=np.float32
        )
        holes = tuple(
            np.ascontiguousarray(hole, dtype=np.float32)
            for hole in polygon.get("Holes", [])
        )
        compiled.append((
            outer,
            holes,
            (
                float(outer[:, 0].min()),
                float(outer[:, 1].min()),
                float(outer[:, 0].max()),
                float(outer[:, 1].max()),
            ),
        ))
    return tuple(compiled)


def _point_inside_compiled(
    point_xy: Sequence[float], regions: Sequence[CompiledRegion]
) -> bool:
    point = (float(point_xy[0]), float(point_xy[1]))
    if not np.isfinite(point).all():
        return False
    for outer, holes, (minimum_x, minimum_y, maximum_x, maximum_y) in regions:
        if not (
            minimum_x <= point[0] <= maximum_x
            and minimum_y <= point[1] <= maximum_y
        ):
            continue
        if cv2.pointPolygonTest(outer, point, False) < 0:
            continue
        if any(cv2.pointPolygonTest(hole, point, False) >= 0 for hole in holes):
            continue
        return True
    return False


def point_inside_regions(
    point_xy: Sequence[float], regions: Sequence[dict[str, Any]]
) -> bool:
    """Return whether a UE left-handed world XY lies in polygon-with-holes."""

    return _point_inside_compiled(point_xy, _compile_regions(regions))


def _validate_ring(ring: Any, label: str) -> None:
    values = np.asarray(ring, dtype=float)
    if values.ndim != 2 or values.shape[1] != 2 or len(values) < 3:
        raise ValueError(f"{label} must be an Nx2 polygon with at least 3 vertices")
    if not bool(np.isfinite(values).all()):
        raise ValueError(f"{label} contains a non-finite coordinate")
    if abs(float(cv2.contourArea(values.astype(np.float32)))) <= 0.0:
        raise ValueError(f"{label} has zero area")


def validate_success_area(data: dict[str, Any]) -> None:
    required = {
        "Schema_Version", "Map_Name", "Task_Stem", "Coordinate_System",
        "Distance_Metric", "Regions", "Target_Footprints", "Status",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"Success-area file is missing: {missing}")
    if data["Coordinate_System"] != "UE left-handed world XY (uu)":
        raise ValueError("Runtime success areas must remain in UE world XY")
    if data["Distance_Metric"] != "xy":
        raise ValueError("Only XY success-area distance is supported")
    if data["Status"] != "published":
        raise ValueError(f"Success area is not published: {data['Status']!r}")
    if not data["Regions"] or not data["Target_Footprints"]:
        raise ValueError("Published success area has empty geometry")
    for index, polygon in enumerate(data["Regions"]):
        if not isinstance(polygon, dict) or "Outer_Boundary" not in polygon:
            raise ValueError(f"Regions[{index}] has no Outer_Boundary")
        _validate_ring(polygon["Outer_Boundary"], f"Regions[{index}].Outer_Boundary")
        for hole_index, hole in enumerate(polygon.get("Holes", [])):
            _validate_ring(hole, f"Regions[{index}].Holes[{hole_index}]")
    for index, footprint in enumerate(data["Target_Footprints"]):
        _validate_ring(footprint, f"Target_Footprints[{index}]")

    if int(data.get("Task_Type", -1)) == 5:
        if data.get("Schema_Version") != 2:
            raise ValueError("T5 dual success areas require Schema_Version 2")
        if data.get("PD_Type") not in {"p", "pd"}:
            raise ValueError("T5 success area has invalid PD_Type")
        for key in ("PD_Object_Regions", "Character_Regions"):
            regions = data.get(key)
            if not isinstance(regions, list) or not regions:
                raise ValueError(f"T5 success area has empty {key}")
            for index, polygon in enumerate(regions):
                if not isinstance(polygon, dict) or "Outer_Boundary" not in polygon:
                    raise ValueError(f"{key}[{index}] has no Outer_Boundary")
                _validate_ring(
                    polygon["Outer_Boundary"],
                    f"{key}[{index}].Outer_Boundary",
                )
                for hole_index, hole in enumerate(polygon.get("Holes", [])):
                    _validate_ring(hole, f"{key}[{index}].Holes[{hole_index}]")
        if data["Regions"] != data["Character_Regions"]:
            raise ValueError("T5 Regions compatibility alias must equal Character_Regions")
        same_regions = data["PD_Object_Regions"] == data["Character_Regions"]
        if data["PD_Type"] == "p" and not same_regions:
            raise ValueError("Pick Only object and character regions must be identical")


@lru_cache(maxsize=512)
def _load_cached(
    path_text: str, modified_ns: int, stage: str = "final"
) -> tuple[dict[str, Any], tuple[CompiledRegion, ...]]:
    del modified_ns
    path = Path(path_text)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "stages" in data:
        if data.get("coordinate_system") != "UE left-handed world XY (uu)":
            raise ValueError("Runtime success areas must remain in UE world XY")
        if data.get("distance_metric") != "xy":
            raise ValueError("Only XY success-area distance is supported")
        stages = data.get("stages")
        if not isinstance(stages, dict) or stage not in stages:
            raise ValueError(f"Success area has no {stage!r} stage")
        clean_stage = stages[stage]
        if not isinstance(clean_stage, dict):
            raise ValueError(f"Success-area stage {stage!r} must be an object")
        character_regions = clean_stage.get("character_regions")
        footprints = clean_stage.get("target_footprints")
        if not isinstance(character_regions, list) or not character_regions:
            raise ValueError("Clean success area has empty character_regions")
        if not isinstance(footprints, list) or not footprints:
            raise ValueError("Clean success area has empty target_footprints")
        for index, polygon in enumerate(character_regions):
            _validate_ring(
                polygon["Outer_Boundary"],
                f"character_regions[{index}].Outer_Boundary",
            )
            for hole_index, hole in enumerate(polygon.get("Holes", [])):
                _validate_ring(
                    hole, f"character_regions[{index}].Holes[{hole_index}]"
                )
        for index, footprint in enumerate(footprints):
            _validate_ring(footprint, f"target_footprints[{index}]")
        normalized = {
            "Coordinate_System": data["coordinate_system"],
            "Distance_Metric": data["distance_metric"],
            "Regions": character_regions,
            "Character_Regions": character_regions,
            "Target_Footprints": footprints,
            "Target_Stage": stage,
            "Status": "published",
        }
        # The regions are 2D.  The stage also publishes the expert's height so
        # a pose in the right place on the wrong floor can be rejected without
        # reading the expert trajectories at evaluation time.
        character_reference_z = clean_stage.get("character_reference_z")
        if character_reference_z is not None:
            normalized["Character_Reference_Z"] = float(character_reference_z)
        # SPL's reference length is a task-level property, published next to the
        # geometry so scoring never has to rebuild the navigation graph.
        shortest = data.get("shortest_path_uu")
        if shortest is not None:
            normalized["Shortest_Path_UU"] = float(shortest)
            normalized["Shortest_Path_Source"] = data.get("shortest_path_source")
        object_reference_z = clean_stage.get("pd_object_reference_z")
        if object_reference_z is not None:
            normalized["PD_Object_Reference_Z"] = float(object_reference_z)
        object_regions = clean_stage.get("pd_object_regions")
        if object_regions is not None:
            if not isinstance(object_regions, list) or not object_regions:
                raise ValueError("Clean success area has empty pd_object_regions")
            for index, polygon in enumerate(object_regions):
                _validate_ring(
                    polygon["Outer_Boundary"],
                    f"pd_object_regions[{index}].Outer_Boundary",
                )
                for hole_index, hole in enumerate(polygon.get("Holes", [])):
                    _validate_ring(
                        hole,
                        f"pd_object_regions[{index}].Holes[{hole_index}]",
                    )
            normalized["PD_Object_Regions"] = object_regions
        data = normalized
    else:
        validate_success_area(data)
    return data, _compile_regions(data["Regions"])


def _resolve_area_path(
    map_name: str, task_stem: str, root: Path
) -> tuple[Path, str]:
    stage = "midway" if task_stem.endswith("__midway") else "final"
    base_stem = (
        task_stem[:-len("__midway")] if stage == "midway" else task_stem
    )
    clean = Path(root) / map_name / base_stem / "area.json"
    if clean.is_file():
        return clean, stage
    legacy = Path(root) / map_name / f"{task_stem}.json"
    return legacy, stage


def load_success_area(
    map_name: str,
    task_stem: str,
    root: Path = DEFAULT_ROOT,
) -> dict[str, Any]:
    path, stage = _resolve_area_path(map_name, task_stem, root)
    stat = path.stat()
    data, _ = _load_cached(
        str(path.resolve()), int(stat.st_mtime_ns), stage
    )
    return data


def _within_reference_z(
    pose: Sequence[float],
    data: dict[str, Any],
    key: str,
    tolerance: float,
    label: str,
) -> bool:
    reference = data.get(key)
    if reference is None:
        raise ValueError(
            f"z_tolerance_uu was requested but the published stage has no "
            f"{key}"
        )
    if len(pose) < 3:
        raise ValueError(f"{label} must contain UE Z to check the reference Z")
    return abs(float(pose[2]) - float(reference)) <= tolerance


def is_task_success(
    map_name: str,
    task_stem: str,
    character_pose: Sequence[float],
    root: Path = DEFAULT_ROOT,
    pd_object_pose: Sequence[float] | None = None,
    z_tolerance_uu: float | None = None,
) -> bool:
    """Evaluate spatial success in UE XY, optionally against the reference Z.

    Orientation is always ignored.  T0--T4 use only the character pose.  T5
    deliberately requires both the character and PD object poses so the wider
    Pick & Drop character allowance can never be mistaken for the object's
    valid drop area.

    ``z_tolerance_uu`` defaults to ``None``, which keeps the historical XY-only
    behaviour.  Passing a tolerance additionally requires each judged entity to
    be within that many uu of the stage's published reference Z, which is what
    separates two targets stacked on different floors.  The tolerance lives in
    the caller, not in the published data, so tuning it never rewrites the
    published files.
    """

    if len(character_pose) < 2:
        raise ValueError("character_pose must contain at least UE X and Y")
    path, stage = _resolve_area_path(map_name, task_stem, root)
    stat = path.stat()
    data, compiled = _load_cached(
        str(path.resolve()), int(stat.st_mtime_ns), stage
    )
    if "PD_Object_Regions" not in data:
        if not _point_inside_compiled(character_pose[:2], compiled):
            return False
        if z_tolerance_uu is None:
            return True
        return _within_reference_z(
            character_pose, data, "Character_Reference_Z",
            z_tolerance_uu, "character_pose",
        )
    if pd_object_pose is None or len(pd_object_pose) < 2:
        raise ValueError("T5 success requires pd_object_pose with at least UE X and Y")
    character_regions = _compile_regions(data["Character_Regions"])
    object_regions = _compile_regions(data["PD_Object_Regions"])
    if not (
        _point_inside_compiled(character_pose[:2], character_regions)
        and _point_inside_compiled(pd_object_pose[:2], object_regions)
    ):
        return False
    if z_tolerance_uu is None:
        return True
    return (
        _within_reference_z(
            character_pose, data, "Character_Reference_Z",
            z_tolerance_uu, "character_pose",
        )
        and _within_reference_z(
            pd_object_pose, data, "PD_Object_Reference_Z",
            z_tolerance_uu, "pd_object_pose",
        )
    )


def evaluate_t5_spatial_success(
    map_name: str,
    task_stem: str,
    character_pose: Sequence[float],
    pd_object_pose: Sequence[float],
    root: Path = DEFAULT_ROOT,
) -> dict[str, bool]:
    """Return separate and combined T5 spatial checks for diagnostics/UI."""

    if len(character_pose) < 2 or len(pd_object_pose) < 2:
        raise ValueError("T5 poses must each contain at least UE X and Y")
    data = load_success_area(map_name, task_stem, root)
    if "PD_Object_Regions" not in data:
        raise ValueError(f"Success area is not T5: {task_stem}")
    character_inside = point_inside_regions(
        character_pose[:2], data["Character_Regions"]
    )
    object_inside = point_inside_regions(
        pd_object_pose[:2], data["PD_Object_Regions"]
    )
    return {
        "character_inside": bool(character_inside),
        "pd_object_inside": bool(object_inside),
        "spatial_success": bool(character_inside and object_inside),
    }
