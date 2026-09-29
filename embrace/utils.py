"""
Utility functions for embrace package.
"""

import sys
import os
import json
from datetime import datetime


def load_task_types(as_dict=False):
    """Load task types from config file.

    Args:
        as_dict: If True, return {id: name} dict; otherwise return [(id, name), ...] list.
    """
    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'task_types.json')
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)['task_types']
    except Exception as e:
        print(f"[!!!] Failed to load task types config: {e}")
        data = [{"id": 0, "name": "Basic"}, {"id": 1, "name": "Exploration"},
                {"id": 2, "name": "Dynamic Spatial-Semantic"}, {"id": 3, "name": "Multi-stage"},
                {"id": 4, "name": "Open Door"}, {"id": 5, "name": "Pick & Drop"}]

    if as_dict:
        return {t['id']: t['name'] for t in data}
    return [(t['id'], t['name']) for t in data]


def flush_stdin():
    """Flush stdin buffer to clear any pending input."""
    import termios
    termios.tcflush(sys.stdin, termios.TCIFLUSH)


def print_current_time():
    """Print current timestamp."""
    now = datetime.now()
    print("\nCurrent Time:", now.strftime("%Y-%m-%d %H:%M:%S"))


def pos_to_filename(loc, widths):
    """
    Convert a 3D position to a filename-safe string.

    Args:
        loc: List of [x, y, z] coordinates
        widths: List of [x_width, y_width, z_width] for zero-padding

    Returns:
        String like "x00123_y-00456_z00789"
    """
    def format_dim(val, width, prefix):
        val_int = int(round(val))
        sign = "-" if val_int < 0 else ""
        val_str = str(abs(val_int)).zfill(width)
        return f"{prefix}{sign}{val_str}"

    x_str = format_dim(loc[0], widths[0], "x")
    y_str = format_dim(loc[1], widths[1], "y")
    z_str = format_dim(loc[2], widths[2], "z")
    return f"{x_str}_{y_str}_{z_str}"


# ===================== PD (Pick & Drop) Config Functions =====================

# Cache for PD config (loaded once, reused)
_pd_config_cache = None
_pd_config_document_cache = None


def _load_pd_config_document():
    """Load and cache the complete PD configuration document."""
    global _pd_config_document_cache
    if _pd_config_document_cache is not None:
        return _pd_config_document_cache

    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'pd_config.json')
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError('PD config root must be a JSON object')
        _pd_config_document_cache = data
    except Exception as e:
        print(f"[!!!] Failed to load PD config: {e}")
        _pd_config_document_cache = {}
    return _pd_config_document_cache


def _load_pd_config():
    """Load PD config from JSON file with caching."""
    global _pd_config_cache
    if _pd_config_cache is not None:
        return _pd_config_cache

    objects = _load_pd_config_document().get('pd_objects', [])
    _pd_config_cache = objects if isinstance(objects, list) else []
    return _pd_config_cache


# Pre-computed mappings (lazy initialization)
_pd_id_name_map = None
_pd_name_id_map = None
_pd_sizes_map = None


def get_pd_id_name_mapping():
    """Get PD ID to name mapping dict. Cached after first call."""
    global _pd_id_name_map
    if _pd_id_name_map is None:
        _pd_id_name_map = {item['id']: item['name'] for item in _load_pd_config()}
    return _pd_id_name_map


def get_pd_name_id_mapping():
    """Get PD name to ID mapping dict. Cached after first call."""
    global _pd_name_id_map
    if _pd_name_id_map is None:
        _pd_name_id_map = {item['name']: item['id'] for item in _load_pd_config()}
    return _pd_name_id_map


def get_pd_default_sizes():
    """Get PD default sizes mapping dict. Cached after first call."""
    global _pd_sizes_map
    if _pd_sizes_map is None:
        _pd_sizes_map = {item['id']: item['size'] for item in _load_pd_config()}
    return _pd_sizes_map


def get_pd_fallback_size():
    """Get the size used for a PD ID absent from the configuration."""
    value = _load_pd_config_document().get('default_size', 1.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0


def get_pd_name_by_id(pd_id):
    """Get PD name by ID."""
    return get_pd_id_name_mapping().get(pd_id, 'Unknown')


def get_pd_size_by_id(pd_id):
    """Get PD default size by ID."""
    return get_pd_default_sizes().get(pd_id, get_pd_fallback_size())


def get_pd_drop_by_reset_params(pd_id):
    """Return DropByReset parameters for ``pd_id`` with safe defaults.

    The returned tuple is ``(forward_distance, height_offset,
    (relative_pitch, relative_yaw, relative_roll))``. IDs absent from the
    config, and configured objects without a ``drop_by_reset`` section, use
    the document-level defaults.
    """
    document = _load_pd_config_document()
    defaults = document.get('drop_by_reset_defaults', {})
    if not isinstance(defaults, dict):
        defaults = {}

    object_config = next(
        (item for item in _load_pd_config()
         if isinstance(item, dict) and item.get('id') == pd_id),
        {},
    )
    override = object_config.get('drop_by_reset', {})
    if not isinstance(override, dict):
        override = {}

    def _number(key, fallback):
        value = override.get(key, defaults.get(key, fallback))
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(fallback)

    rotation = override.get(
        'relative_rotation', defaults.get('relative_rotation', [0, 0, 0]))
    if not isinstance(rotation, (list, tuple)) or len(rotation) != 3:
        rotation = [0, 0, 0]
    try:
        rotation = tuple(float(value) for value in rotation)
    except (TypeError, ValueError):
        rotation = (0.0, 0.0, 0.0)

    return (
        _number('forward_distance', 70),
        _number('height_offset', 50),
        rotation,
    )


def get_pd_names_list():
    """Get list of all PD names."""
    return [item['name'] for item in _load_pd_config()]
