"""Sidebar panel in the 3D Viewport."""

from __future__ import annotations

import bpy

from .constants import ADDON_NAME, PANEL_CATEGORY


class CAMERA_PREVIEW_PT_panel(bpy.types.Panel):
    bl_label = ADDON_NAME
    bl_idname = "CAMERA_PREVIEW_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        settings = context.scene.camera_preview
        layout.prop(settings, "preview_enabled")
        layout.prop(settings, "selected_camera")
        if context.scene.camera is None and settings.selected_camera is None:
            box = layout.box()
            box.label(text="No Active Camera")
            box.label(text="Create or select a camera")
            box.label(text="to enable the preview.")

        preview = layout.column(align=True)
        preview.label(text="Preview")
        preview.prop(settings, "preview_width")
        preview.prop(settings, "preview_height")
        position = layout.column(align=True)
        position.label(text="Position")
        position.prop(settings, "preview_position_x")
        position.prop(settings, "preview_position_y")

        layout.prop(settings, "shading_mode")
        note = layout.box()
        note.label(text="Live image uses this 3D Viewport's shading.")
        note.label(text="Solid is the supported mode in this version.")

        overlays = layout.column(align=True)
        overlays.label(text="Overlays")
        overlays.prop(settings, "show_camera_frame")
        overlays.prop(settings, "show_crosshair")
        overlays.prop(settings, "show_rule_of_thirds")
        overlays.prop(settings, "show_safe_areas")
        overlays.prop(settings, "show_horizon")

        layout.separator()
        layout.label(text="Information")
        layout.prop(settings, "show_camera_info")
        layout.label(text="Interaction")
        layout.prop(settings, "camera_control_enabled")
        if settings.camera_control_enabled:
            layout.prop(settings, "camera_lock")
            layout.label(text="Over the preview: Ctrl-drag orbits,")
            layout.label(text="wheel dollies, WASD moves, Shift is faster.")
        layout.separator()
        layout.operator("camera_preview.reset", icon="FILE_REFRESH")
