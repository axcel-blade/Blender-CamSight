"""Clear the import state Blender's extension policy checker rejects.

Older builds inserted this extension's ``src`` directory into ``sys.path`` and
imported ``blender_camsight`` as a top-level package. Reloading the add-on does
not undo that, so Blender keeps reporting those modules until the process
restarts. This removes only entries that point at this extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import MutableMapping, MutableSequence


def drop_leaked_imports(
    sys_path: MutableSequence[str],
    modules: MutableMapping[str, object],
    extension_root: Path,
) -> None:
    """Drop a leaked ``src`` path entry and top-level ``blender_camsight`` modules."""
    root = extension_root.resolve()
    src = (root / "src").resolve()
    kept: list[str] = []
    for entry in sys_path:
        try:
            if Path(entry).resolve() == src:
                continue
        except OSError:
            pass
        kept.append(entry)
    if len(kept) != len(sys_path):
        sys_path[:] = kept

    for name in list(modules):
        if name != "blender_camsight" and not name.startswith("blender_camsight."):
            continue
        if _module_is_inside(modules[name], root):
            del modules[name]


def drop_leaked_extension_imports(extension_root: Path) -> None:
    """Clean leaked imports when running inside Blender, then refresh policy warnings."""
    import sys

    if "bpy" not in sys.modules:
        return
    drop_leaked_imports(sys.path, sys.modules, extension_root)
    try:
        import addon_utils
    except ImportError:
        return
    reset = getattr(addon_utils, "_is_first_reset", None)
    if callable(reset):
        reset()


def _module_is_inside(module: object, root: Path) -> bool:
    file = getattr(module, "__file__", None)
    if isinstance(file, str) and _path_is_inside(file, root):
        return True
    search = getattr(module, "__path__", None)
    if search is None:
        return False
    return any(isinstance(entry, str) and _path_is_inside(entry, root) for entry in search)


def _path_is_inside(path: str, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(root)
    except (OSError, ValueError):
        return False
    return True
