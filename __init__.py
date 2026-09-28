"""Package entry so Blender can install this folder as an add-on."""

# Blender lists add-ons by parsing this file without running it.
# bl_info must stay a literal dict. Assigning it from another module hides the add-on.
bl_info = {
    "name": "Blender-CamSight",
    "author": "AXCEL BLADE",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Blender-CamSight",
    "description": "Live first-person camera monitor that leaves the main viewport free",
    "category": "3D View",
}

try:
    from . import addon as _addon
except ImportError:  # imported as a loose module (pytest collection of the repo root)
    import addon as _addon


def register() -> None:
    _addon.register()


def unregister() -> None:
    _addon.unregister()
