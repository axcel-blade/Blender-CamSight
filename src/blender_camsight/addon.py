"""Add-on registration. Implementation lives in the sibling modules."""

from __future__ import annotations

from typing import List, Optional, Tuple

import bpy

from .constants import (
    ADDON_NAME,
    ADDON_VERSION,
    DEFAULT_SHORTCUT_ALT,
    DEFAULT_SHORTCUT_CTRL,
    DEFAULT_SHORTCUT_KEY,
    DEFAULT_SHORTCUT_SHIFT,
    KEYMAP_NAME,
    KEYMAP_SPACE,
    MIN_BLENDER_VERSION,
    TOGGLE_OPERATOR_ID,
)
from .handlers import register_handlers, unregister_handlers
from .operators import CLASSES as OPERATOR_CLASSES
from .panel import CAMERA_PREVIEW_PT_panel
from .preferences import CameraPreviewPreferences, get_preferences, set_module_name
from .properties import CameraPreviewSettings, register_properties, unregister_properties
from .registration import register_classes, unregister_classes

_registered_classes: List[type] = []
_keymaps: List[Tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []
_module_name: Optional[str] = None

CLASSES = (
    CameraPreviewSettings,
    *OPERATOR_CLASSES,
    CAMERA_PREVIEW_PT_panel,
    CameraPreviewPreferences,
)


def register(module_name: Optional[str] = None) -> None:
    """Register classes, scene properties, handlers, and the toggle keymap."""
    global _module_name
    if _registered_classes:
        return
    _module_name = module_name
    if module_name:
        set_module_name(module_name)
    _registered_classes.extend(register_classes(CLASSES, bpy.utils.register_class))
    register_properties()
    register_handlers()
    _register_keymap()


def unregister() -> None:
    """Remove keymaps, handlers, properties, and classes. Safe to call twice."""
    _unregister_keymap()
    unregister_handlers()
    unregister_properties()
    unregister_classes(_registered_classes, bpy.utils.unregister_class)
    _registered_classes.clear()


def refresh_keymap() -> None:
    _unregister_keymap()
    _register_keymap()


def _shortcut_from_preferences():
    context = bpy.context
    prefs = None
    try:
        prefs = get_preferences(context)
    except Exception:
        prefs = None
    if prefs is None:
        return DEFAULT_SHORTCUT_KEY, DEFAULT_SHORTCUT_SHIFT, DEFAULT_SHORTCUT_CTRL, DEFAULT_SHORTCUT_ALT
    return prefs.shortcut_key, prefs.shortcut_shift, prefs.shortcut_ctrl, prefs.shortcut_alt


def _register_keymap() -> None:
    if _keymaps:
        return
    window_manager = bpy.context.window_manager
    keyconfig = window_manager.keyconfigs.addon
    if keyconfig is None:
        return
    keymap = keyconfig.keymaps.new(name=KEYMAP_NAME, space_type=KEYMAP_SPACE)
    key, shift, ctrl, alt = _shortcut_from_preferences()
    item = keymap.keymap_items.new(
        TOGGLE_OPERATOR_ID,
        type=key,
        value="PRESS",
        shift=bool(shift),
        ctrl=bool(ctrl),
        alt=bool(alt),
    )
    _keymaps.append((keymap, item))


def _unregister_keymap() -> None:
    for keymap, item in _keymaps:
        try:
            keymap.keymap_items.remove(item)
        except Exception:
            pass
    _keymaps.clear()


def blender_version_supported() -> bool:
    return bpy.app.version >= MIN_BLENDER_VERSION


def addon_label() -> str:
    return f"{ADDON_NAME} {'.'.join(str(part) for part in ADDON_VERSION)}"
