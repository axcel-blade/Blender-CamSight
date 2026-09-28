"""Package entry so Blender can install this folder as an add-on."""

try:
    from . import addon as _addon
except ImportError:  # imported as a loose module (pytest collection of the repo root)
    import addon as _addon

bl_info = _addon.bl_info


def register() -> None:
    _addon.register()


def unregister() -> None:
    _addon.unregister()
