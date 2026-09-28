"""Thin Blender entry point.

Blender loads this module as part of the extension package. The implementation
lives in ``src/blender_camsight`` and is imported relatively so every bundled
module stays under that package. Extensions must not edit ``sys.path`` or load
bundled files as top-level modules.
"""

from __future__ import annotations

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


def _implementation():
    from pathlib import Path

    from .src.blender_camsight.policy import drop_leaked_extension_imports

    # A previous enable may still have ``src`` on sys.path. Drop that before
    # Blender draws the extension policy warning.
    drop_leaked_extension_imports(Path(__file__).resolve().parent)
    from .src import blender_camsight as package

    return package


def register() -> None:
    # Preferences are keyed by the full add-on module. An extension module is
    # bl_ext.<repository>.<id>, so the first dotted piece is not that key.
    _implementation().register(module_name=__package__ or None)


def unregister() -> None:
    _implementation().unregister()
