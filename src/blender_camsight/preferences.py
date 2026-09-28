"""Add-on preferences: defaults and the toggle shortcut."""

from __future__ import annotations

import bpy

from .constants import (
    ADDON_ID,
    DEFAULT_PREVIEW_HEIGHT,
    DEFAULT_PREVIEW_WIDTH,
    DEFAULT_PREVIEW_X,
    DEFAULT_PREVIEW_Y,
    DEFAULT_SHADING,
    DEFAULT_SHORTCUT_ALT,
    DEFAULT_SHORTCUT_CTRL,
    DEFAULT_SHORTCUT_KEY,
    DEFAULT_SHORTCUT_SHIFT,
    DEFAULT_SHOW_CROSSHAIR,
    DEFAULT_SHOW_FRAME,
    DEFAULT_SHOW_HORIZON,
    DEFAULT_SHOW_INFO,
    DEFAULT_SHOW_SAFE,
    DEFAULT_SHOW_THIRDS,
    MAX_PREVIEW_SIZE,
    MIN_PREVIEW_SIZE,
    SHADING_ITEMS,
)

_module_name = ADDON_ID


def set_module_name(name: str) -> None:
    global _module_name
    _module_name = name or ADDON_ID
    CameraPreviewPreferences.bl_idname = _module_name


def get_preferences(context):
    addon = context.preferences.addons.get(_module_name)
    if addon is None:
        return None
    return addon.preferences


def _shortcut_changed(_self, _context) -> None:
    try:
        from . import addon as addon_mod

        addon_mod.refresh_keymap()
    except Exception:
        pass


class CameraPreviewPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    default_width: bpy.props.IntProperty(
        name="Default Width",
        default=DEFAULT_PREVIEW_WIDTH,
        min=MIN_PREVIEW_SIZE,
        max=MAX_PREVIEW_SIZE,
    )
    default_height: bpy.props.IntProperty(
        name="Default Height",
        default=DEFAULT_PREVIEW_HEIGHT,
        min=MIN_PREVIEW_SIZE,
        max=MAX_PREVIEW_SIZE,
    )
    default_x: bpy.props.IntProperty(name="Default X", default=DEFAULT_PREVIEW_X, min=0, max=10000)
    default_y: bpy.props.IntProperty(name="Default Y", default=DEFAULT_PREVIEW_Y, min=0, max=10000)
    default_shading: bpy.props.EnumProperty(
        name="Default Shading",
        items=SHADING_ITEMS,
        default=DEFAULT_SHADING,
    )
    default_show_frame: bpy.props.BoolProperty(name="Camera Frame", default=DEFAULT_SHOW_FRAME)
    default_show_crosshair: bpy.props.BoolProperty(name="Crosshair", default=DEFAULT_SHOW_CROSSHAIR)
    default_show_thirds: bpy.props.BoolProperty(name="Rule of Thirds", default=DEFAULT_SHOW_THIRDS)
    default_show_safe: bpy.props.BoolProperty(name="Safe Areas", default=DEFAULT_SHOW_SAFE)
    default_show_horizon: bpy.props.BoolProperty(name="Horizon Line", default=DEFAULT_SHOW_HORIZON)
    default_show_info: bpy.props.BoolProperty(name="Camera Information", default=DEFAULT_SHOW_INFO)
    shortcut_key: bpy.props.EnumProperty(
        name="Key",
        items=[(letter, letter, "") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
        default=DEFAULT_SHORTCUT_KEY,
        update=_shortcut_changed,
    )
    shortcut_shift: bpy.props.BoolProperty(
        name="Shift", default=DEFAULT_SHORTCUT_SHIFT, update=_shortcut_changed
    )
    shortcut_ctrl: bpy.props.BoolProperty(
        name="Ctrl", default=DEFAULT_SHORTCUT_CTRL, update=_shortcut_changed
    )
    shortcut_alt: bpy.props.BoolProperty(
        name="Alt", default=DEFAULT_SHORTCUT_ALT, update=_shortcut_changed
    )

    def draw(self, _context):
        layout = self.layout
        layout.label(text="Default Preview")
        grid = layout.grid_flow(columns=2, align=True)
        grid.prop(self, "default_width")
        grid.prop(self, "default_height")
        grid.prop(self, "default_x")
        grid.prop(self, "default_y")
        layout.prop(self, "default_shading")
        layout.label(text="Default Overlays")
        layout.prop(self, "default_show_frame")
        layout.prop(self, "default_show_crosshair")
        layout.prop(self, "default_show_thirds")
        layout.prop(self, "default_show_safe")
        layout.prop(self, "default_show_horizon")
        layout.prop(self, "default_show_info")
        layout.separator()
        layout.label(text="Toggle Shortcut")
        row = layout.row(align=True)
        row.prop(self, "shortcut_shift", toggle=True)
        row.prop(self, "shortcut_ctrl", toggle=True)
        row.prop(self, "shortcut_alt", toggle=True)
        row.prop(self, "shortcut_key")
        layout.label(text="Shift+C replaces Blender's Frame All while Blender-CamSight is enabled.")
