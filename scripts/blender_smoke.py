"""Headless check that the add-on registers inside Blender and then removes itself.

Load the checkout as a package. ``blender --python`` would otherwise import
``addon.py`` as a loose module, and the relative import inside it would fail.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path


def _load_addon():
    root = Path(__file__).resolve().parents[1]
    # Not ``blender_camsight``: that name is the extension id, and this loader
    # must not replace it in ``sys.modules``.
    name = "camsight_checkout"
    spec = importlib.util.spec_from_file_location(
        name,
        root / "__init__.py",
        submodule_search_locations=[str(root)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load the add-on package from {root}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _preview_settings():
    import bpy

    for module in sys.modules.values():
        cls = getattr(module, "CameraPreviewSettings", None)
        if isinstance(cls, type) and issubclass(cls, bpy.types.PropertyGroup):
            return cls
    return None


def main() -> int:
    try:
        import bpy

        addon = _load_addon()
        addon.register()
        settings = _preview_settings()
        # Blender 5.2 keeps registered add-on classes off ``bpy.types``.
        # ``is_registered`` is the check that still holds.
        if settings is None or not settings.is_registered:
            raise RuntimeError("CameraPreviewSettings was not registered")
        if not hasattr(bpy.types.Scene, "camera_preview"):
            raise RuntimeError("Scene.camera_preview was not registered")
        addon.unregister()
        if settings.is_registered:
            raise RuntimeError("CameraPreviewSettings was still registered")
        if hasattr(bpy.types.Scene, "camera_preview"):
            raise RuntimeError("Scene.camera_preview was still present after unregister")
    except Exception:
        traceback.print_exc()
        return 1
    print("camera preview: register/unregister ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
