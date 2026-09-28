"""Blender-CamSight package.

Importing this package does not import Blender. Call ``register`` from the
root add-on entry point, which runs inside Blender.
"""

from __future__ import annotations

from .constants import ADDON_VERSION, ADDON_VERSION_STRING

__version__ = ADDON_VERSION_STRING
__all__ = ["register", "unregister", "__version__"]


def register(module_name: str | None = None) -> None:
    from .addon import register as register_addon

    register_addon(module_name=module_name)


def unregister() -> None:
    from .addon import unregister as unregister_addon

    unregister_addon()
