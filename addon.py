"""Thin Blender entry point.

Blender loads this module (or the package ``__init__`` that re-exports it).
The implementation lives in ``src/blender_camsight``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Keep this dict identical to the literal in __init__.py. Blender's add-on list reads only that file.
bl_info = {
    "name": "Blender-CamSight",
    "author": "AXCEL BLADE",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Blender-CamSight",
    "description": "Live first-person camera monitor that leaves the main viewport free",
    "category": "3D View",
}


def _ensure_src_on_path() -> None:
    src = Path(__file__).resolve().parent / "src"
    entry = str(src)
    if entry not in sys.path:
        sys.path.insert(0, entry)


def register() -> None:
    _ensure_src_on_path()
    from blender_camsight import register as register_package

    # Preferences are keyed by the full add-on module. An extension module is
    # bl_ext.<repository>.<id>, so the first dotted piece is not that key.
    register_package(module_name=__package__ or None)


def unregister() -> None:
    _ensure_src_on_path()
    from blender_camsight import unregister as unregister_package

    unregister_package()
