"""Operators for toggling the preview and interacting with the monitor."""

from __future__ import annotations

import bpy
from mathutils import Vector

from .constants import (
    CONTROL_TIMER_SECONDS,
    DOLLY_STEP,
    FAST_MOVE_MULTIPLIER,
    MOVE_SPEED,
    ORBIT_SENSITIVITY,
    TOGGLE_OPERATOR_ID,
)
from .drawing import runtime
from .preferences import get_preferences
from .preview import PreviewLayout, hit_test
from .properties import set_preview_enabled
from .viewport import is_compatible_region

_HELD_KEYS = {
    "W": Vector((0.0, 0.0, -1.0)),
    "S": Vector((0.0, 0.0, 1.0)),
    "A": Vector((-1.0, 0.0, 0.0)),
    "D": Vector((1.0, 0.0, 0.0)),
    "E": Vector((0.0, 1.0, 0.0)),
    "Q": Vector((0.0, -1.0, 0.0)),
}


def _settings(context):
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, "camera_preview", None)


def _apply_defaults(settings, context) -> None:
    prefs = get_preferences(context)
    if prefs is None:
        from .constants import (
            DEFAULT_PREVIEW_HEIGHT,
            DEFAULT_PREVIEW_WIDTH,
            DEFAULT_PREVIEW_X,
            DEFAULT_PREVIEW_Y,
            DEFAULT_SHADING,
            DEFAULT_SHOW_CROSSHAIR,
            DEFAULT_SHOW_FRAME,
            DEFAULT_SHOW_HORIZON,
            DEFAULT_SHOW_INFO,
            DEFAULT_SHOW_SAFE,
            DEFAULT_SHOW_THIRDS,
        )

        settings.preview_width = DEFAULT_PREVIEW_WIDTH
        settings.preview_height = DEFAULT_PREVIEW_HEIGHT
        settings.preview_position_x = DEFAULT_PREVIEW_X
        settings.preview_position_y = DEFAULT_PREVIEW_Y
        settings.shading_mode = DEFAULT_SHADING
        settings.show_camera_frame = DEFAULT_SHOW_FRAME
        settings.show_crosshair = DEFAULT_SHOW_CROSSHAIR
        settings.show_rule_of_thirds = DEFAULT_SHOW_THIRDS
        settings.show_safe_areas = DEFAULT_SHOW_SAFE
        settings.show_horizon = DEFAULT_SHOW_HORIZON
        settings.show_camera_info = DEFAULT_SHOW_INFO
        return
    settings.preview_width = prefs.default_width
    settings.preview_height = prefs.default_height
    settings.preview_position_x = prefs.default_x
    settings.preview_position_y = prefs.default_y
    settings.shading_mode = prefs.default_shading
    settings.show_camera_frame = prefs.default_show_frame
    settings.show_crosshair = prefs.default_show_crosshair
    settings.show_rule_of_thirds = prefs.default_show_thirds
    settings.show_safe_areas = prefs.default_show_safe
    settings.show_horizon = prefs.default_show_horizon
    settings.show_camera_info = prefs.default_show_info


class CAMERA_PREVIEW_OT_toggle(bpy.types.Operator):
    bl_idname = TOGGLE_OPERATOR_ID
    bl_label = "Toggle Camera Preview"
    bl_description = "Show or hide the live camera monitor"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            return {"CANCELLED"}
        set_preview_enabled(settings, not settings.preview_enabled)
        if settings.preview_enabled:
            bpy.ops.camera_preview.session("INVOKE_DEFAULT")
        else:
            runtime().stop_requested = True
        return {"FINISHED"}


class CAMERA_PREVIEW_OT_enable(bpy.types.Operator):
    bl_idname = "camera_preview.enable"
    bl_label = "Enable Camera Preview"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            return {"CANCELLED"}
        set_preview_enabled(settings, True)
        runtime().mark_dirty()
        bpy.ops.camera_preview.session("INVOKE_DEFAULT")
        return {"FINISHED"}


class CAMERA_PREVIEW_OT_disable(bpy.types.Operator):
    bl_idname = "camera_preview.disable"
    bl_label = "Disable Camera Preview"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            return {"CANCELLED"}
        set_preview_enabled(settings, False)
        runtime().stop_requested = True
        return {"FINISHED"}


class CAMERA_PREVIEW_OT_reset(bpy.types.Operator):
    bl_idname = "camera_preview.reset"
    bl_label = "Reset Camera Preview"
    bl_description = "Restore preview size, position, and overlays from preferences"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = _settings(context)
        if settings is None:
            return {"CANCELLED"}
        _apply_defaults(settings, context)
        runtime().mark_dirty()
        return {"FINISHED"}


class CAMERA_PREVIEW_OT_session(bpy.types.Operator):
    """Modal session that drags, resizes, and optionally flies the camera.

    Events outside the monitor are passed through so the main viewport can
    still orbit, pan, zoom, and transform objects.
    """

    bl_idname = "camera_preview.session"
    bl_label = "Camera Preview Session"
    bl_options = {"INTERNAL"}

    def invoke(self, context, _event):
        state = runtime()
        if state.modal_running:
            state.stop_requested = False
            return {"FINISHED"}
        state.modal_running = True
        state.stop_requested = False
        self._drag = None
        self._held = set()
        self._timer = context.window_manager.event_timer_add(
            CONTROL_TIMER_SECONDS, window=context.window
        )
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        self._finish(context)

    def _finish(self, context) -> None:
        state = runtime()
        state.modal_running = False
        state.stop_requested = False
        timer = getattr(self, "_timer", None)
        if timer is not None:
            try:
                context.window_manager.event_timer_remove(timer)
            except Exception:
                pass
            self._timer = None

    def modal(self, context, event):
        settings = _settings(context)
        state = runtime()
        if settings is None or not settings.preview_enabled or state.stop_requested:
            self._finish(context)
            return {"CANCELLED"}
        if event.type == "TIMER":
            self._fly(context, settings, event)
            return {"PASS_THROUGH"}
        region = context.region
        area = context.area
        if region is None or area is None or not is_compatible_region(area.type, region.type):
            return {"PASS_THROUGH"}
        mouse = (event.mouse_region_x, event.mouse_region_y)
        layout = PreviewLayout(
            x=float(settings.preview_position_x),
            y=float(settings.preview_position_y),
            width=float(settings.preview_width),
            height=float(settings.preview_height),
        )
        zone = hit_test(layout, mouse[0], mouse[1])
        if event.type == "LEFTMOUSE" and event.value == "PRESS" and zone == "close":
            set_preview_enabled(settings, False)
            self._finish(context)
            return {"FINISHED"}
        if event.type == "LEFTMOUSE" and event.value == "PRESS" and zone == "header":
            self._drag = ("move", mouse[0], mouse[1], settings.preview_position_x, settings.preview_position_y)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "PRESS" and zone == "resize":
            self._drag = ("resize", mouse[0], mouse[1], settings.preview_width, settings.preview_height)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            self._drag = None
        if event.type == "MOUSEMOVE" and self._drag is not None:
            self._apply_drag(settings, mouse)
            return {"RUNNING_MODAL"}
        if self._control_event(context, settings, event, zone):
            return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def _apply_drag(self, settings, mouse) -> None:
        mode, origin_x, origin_y, start_a, start_b = self._drag
        dx = int(mouse[0] - origin_x)
        dy = int(mouse[1] - origin_y)
        if mode == "move":
            settings.preview_position_x = max(0, start_a + dx)
            settings.preview_position_y = max(0, start_b + dy)
        else:
            settings.preview_width = start_a + dx
            settings.preview_height = start_b + dy

    def _control_event(self, context, settings, event, zone) -> bool:
        if not settings.camera_control_enabled or settings.camera_lock or zone not in {"body", "header"}:
            if event.type in _HELD_KEYS and event.value == "RELEASE":
                self._held.discard(event.type)
            return False
        camera = settings.selected_camera or context.scene.camera
        if camera is None or camera.type != "CAMERA":
            return False
        if event.type in _HELD_KEYS and event.value == "PRESS":
            self._held.add(event.type)
            return True
        if event.type in _HELD_KEYS and event.value == "RELEASE":
            self._held.discard(event.type)
            return True
        if event.type == "WHEELUPMOUSE":
            _dolly(camera, -DOLLY_STEP)
            return True
        if event.type == "WHEELDOWNMOUSE":
            _dolly(camera, DOLLY_STEP)
            return True
        if event.type == "MOUSEMOVE" and event.value == "PRESS":
            return False
        if event.type == "LEFTMOUSE" and self._drag is not None:
            return False
        if event.type == "MOUSEMOVE" and event.ctrl:
            _orbit(camera, event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y)
            return True
        return False

    def _fly(self, context, settings, event) -> None:
        if not settings.camera_control_enabled or settings.camera_lock or not self._held:
            return
        camera = settings.selected_camera or context.scene.camera
        if camera is None or camera.type != "CAMERA":
            return
        speed = MOVE_SPEED * CONTROL_TIMER_SECONDS
        if event.shift:
            speed *= FAST_MOVE_MULTIPLIER
        local = Vector((0.0, 0.0, 0.0))
        for key in self._held:
            local += _HELD_KEYS[key]
        if local.length == 0:
            return
        local.normalize()
        world = camera.matrix_world.to_3x3() @ (local * speed)
        camera.location += world


def _dolly(camera, distance: float) -> None:
    forward = camera.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
    camera.location += forward * distance


def _orbit(camera, dx: float, dy: float) -> None:
    camera.rotation_euler[2] += dx * ORBIT_SENSITIVITY
    camera.rotation_euler[0] += dy * ORBIT_SENSITIVITY


CLASSES = (
    CAMERA_PREVIEW_OT_toggle,
    CAMERA_PREVIEW_OT_enable,
    CAMERA_PREVIEW_OT_disable,
    CAMERA_PREVIEW_OT_reset,
    CAMERA_PREVIEW_OT_session,
)
