"""Headless check that the add-on registers inside Blender and then removes itself."""

from __future__ import annotations

import sys
import traceback


def main() -> int:
    try:
        import addon
        import bpy

        addon.register()
        if getattr(bpy.types, "CameraPreviewSettings", None) is None:
            raise RuntimeError("CameraPreviewSettings was not registered")
        if not hasattr(bpy.types.Scene, "camera_preview"):
            raise RuntimeError("Scene.camera_preview was not registered")
        addon.unregister()
        if getattr(bpy.types, "CameraPreviewSettings", None) is not None:
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
