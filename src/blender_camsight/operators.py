"""Operators for toggling the preview and interacting with the monitor."""

from __future__ import annotations

import bpy
from mathutils import Vector

from .constants import (
    CONTROL_TIMER_SECONDS,
    DOLLY_STEP,
    FAST_MOVE_MULTIPLIER,
    MAX_PREVIEW_SIZE,
    MIN_PREVIEW_SIZE,
    MOVE_SPEED,
    ORBIT_SENSITIVITY,
    TOGGLE_OPERATOR_ID,
)
from .drawing import runtime
from .preferences import get_preferences
from .preview import apply_window_drag, displayed_layout, hit_test
from .properties import set_preview_enabled
from .viewport import find_view3d_window, is_compatible_region, is_view3d_area, region_local_mouse, window_region

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
            DEFAULT_SHADING_FOLLOW,
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
        settings.shading_follow_viewport = DEFAULT_SHADING_FOLLOW
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
    settings.shading_follow_viewport = prefs.default_shading_follow_viewport
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
            ensure_session()
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
        ensure_session()
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


def ensure_session() -> None:
    """Start the modal session on the next timer tick.

    Property updates and operators that call this from ``execute`` do not have
    a usable invoke context, so the session is deferred until Blender is idle.
    """
    state = runtime()
    state.stop_requested = False
    if state.modal_running or state.session_pending:
        return
    state.session_pending = True

    def _start():
        state.session_pending = False
        if state.modal_running:
            return None
        settings = _settings(bpy.context)
        if settings is None or not settings.preview_enabled:
            return None
        try:
            _invoke_session(bpy.context)
        except Exception:
            pass
        return None

    timers = getattr(getattr(bpy, "app", None), "timers", None)
    if timers is not None:
        try:
            timers.register(_start, first_interval=0.0)
            return
        except Exception:
            state.session_pending = False
    _start()


class CAMERA_PREVIEW_OT_session(bpy.types.Operator):
    """Modal session that drags, resizes, and optionally flies the camera.

    Drag the header or the image to move the monitor. Drag the bottom-right
    grip to resize it. Events outside the monitor are passed through so the
    main viewport can still orbit, pan, zoom, and transform objects.
    """

    bl_idname = "camera_preview.session"
    bl_label = "Camera Preview Session"
    bl_options = {"INTERNAL"}

    def invoke(self, context, _event):
        state = runtime()
        if state.modal_running:
            state.stop_requested = False
            state.session_pending = False
            return {"FINISHED"}
        state.modal_running = True
        state.session_pending = False
        state.stop_requested = False
        self._drag = None
        self._drag_area = None
        self._drag_region = None
        self._cursor_modal = False
        self._hover_cursor_name = None
        self._held = set()
        self._timer = context.window_manager.event_timer_add(
            CONTROL_TIMER_SECONDS, window=context.window
        )
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        self._finish(context)

    def _finish(self, context) -> None:
        self._restore_cursor(context)
        self._drag = None
        self._drag_area = None
        self._drag_region = None
        state = runtime()
        state.modal_running = False
        state.session_pending = False
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
            from .drawing import service_deferred_shading

            service_deferred_shading(context)
            if self._drag is None:
                self._fly(context, settings, event)
            return {"PASS_THROUGH"}
        if self._drag is not None:
            return self._modal_drag(context, settings, event)
        area, region = _region_under_mouse(context, event)
        if area is None or region is None or not is_compatible_region(area.type, region.type):
            self._hover_cursor(context, "outside")
            return {"PASS_THROUGH"}
        mouse = region_local_mouse(event.mouse_x, event.mouse_y, region.x, region.y)
        layout = displayed_layout(
            x=float(settings.preview_position_x),
            y=float(settings.preview_position_y),
            width=float(settings.preview_width),
            height=float(settings.preview_height),
            region_width=float(region.width),
            region_height=float(region.height),
        )
        zone = hit_test(layout, mouse[0], mouse[1])
        if event.type == "MOUSEMOVE":
            self._hover_cursor(context, zone)
        if event.type == "LEFTMOUSE" and event.value == "PRESS" and zone == "close":
            set_preview_enabled(settings, False)
            self._finish(context)
            return {"FINISHED"}
        if event.type == "LEFTMOUSE" and event.value == "PRESS" and _starts_move(zone, event):
            self._begin_drag("move", area, region, mouse, layout)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "PRESS" and zone == "resize":
            self._begin_drag("resize", area, region, mouse, layout)
            return {"RUNNING_MODAL"}
        if self._control_event(context, settings, event, zone):
            return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def _modal_drag(self, context, settings, event):
        if event.type == "ESC" and event.value == "PRESS":
            self._cancel_drag(context, settings)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            self._end_drag(context)
            return {"RUNNING_MODAL"}
        if event.type == "MOUSEMOVE":
            self._apply_drag(context, settings, event)
        return {"RUNNING_MODAL"}

    def _begin_drag(self, mode, area, region, mouse, layout) -> None:
        self._drag = {
            "mode": mode,
            "origin": mouse,
            "start": layout,
        }
        self._drag_area = area
        self._drag_region = region
        self._set_drag_cursor(mode)

    def _end_drag(self, context) -> None:
        self._drag = None
        self._drag_area = None
        self._drag_region = None
        self._hover_cursor_name = None
        self._restore_cursor(context)

    def _cancel_drag(self, context, settings) -> None:
        start = self._drag["start"]
        area = self._drag_area
        settings.preview_position_x = int(round(start.x))
        settings.preview_position_y = int(round(start.y))
        settings.preview_width = int(round(start.width))
        settings.preview_height = int(round(start.height))
        self._end_drag(context)
        _redraw(area)

    def _apply_drag(self, context, settings, event) -> None:
        region = self._drag_region
        if region is None or self._drag is None:
            self._end_drag(context)
            return
        try:
            region_width = float(region.width)
            region_height = float(region.height)
            mouse = region_local_mouse(event.mouse_x, event.mouse_y, region.x, region.y)
        except Exception:
            self._end_drag(context)
            return
        x, y, width, height = apply_window_drag(
            self._drag["mode"],
            self._drag["origin"],
            mouse,
            self._drag["start"],
            region_width,
            region_height,
            MIN_PREVIEW_SIZE,
            MAX_PREVIEW_SIZE,
        )
        settings.preview_position_x = x
        settings.preview_position_y = y
        if self._drag["mode"] == "resize":
            settings.preview_width = width
            settings.preview_height = height
        _redraw(self._drag_area)

    def _set_drag_cursor(self, mode) -> None:
        window = getattr(bpy.context, "window", None)
        if window is None:
            return
        try:
            window.cursor_modal_set("HAND" if mode == "move" else "SCROLL_XY")
            self._cursor_modal = True
        except Exception:
            self._cursor_modal = False

    def _hover_cursor(self, context, zone: str) -> None:
        if self._cursor_modal:
            return
        if zone in {"header", "body"}:
            cursor = "HAND"
        elif zone == "resize":
            cursor = "SCROLL_XY"
        elif getattr(self, "_hover_cursor_name", None) not in (None, "DEFAULT"):
            cursor = "DEFAULT"
        else:
            return
        if cursor == getattr(self, "_hover_cursor_name", None):
            return
        window = getattr(context, "window", None)
        if window is None:
            return
        try:
            window.cursor_set(cursor)
            self._hover_cursor_name = cursor
        except Exception:
            pass

    def _restore_cursor(self, context) -> None:
        if not getattr(self, "_cursor_modal", False):
            return
        window = getattr(context, "window", None)
        if window is not None:
            try:
                window.cursor_modal_restore()
            except Exception:
                pass
        self._cursor_modal = False

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


def _invoke_session(context) -> None:
    """Invoke from a 3D View so the modal handler is attached to a real window."""
    window = getattr(context, "window", None)
    screen = getattr(window, "screen", None) if window is not None else None
    for area in getattr(screen, "areas", ()) or ():
        if not is_view3d_area(getattr(area, "type", None)):
            continue
        region = window_region(area)
        if region is None or not hasattr(context, "temp_override"):
            continue
        with context.temp_override(window=window, area=area, region=region):
            bpy.ops.camera_preview.session("INVOKE_DEFAULT")
        return
    bpy.ops.camera_preview.session("INVOKE_DEFAULT")


def _starts_move(zone: str, event) -> bool:
    """Header always moves. The image moves unless Ctrl is held for orbit."""
    if zone == "header":
        return True
    return zone == "body" and not getattr(event, "ctrl", False)


def _region_under_mouse(context, event):
    window = getattr(context, "window", None)
    screen = getattr(window, "screen", None) if window is not None else None
    if screen is None:
        screen = getattr(context, "screen", None)
    areas = getattr(screen, "areas", None) if screen is not None else None
    return find_view3d_window(areas, event.mouse_x, event.mouse_y)


def _redraw(area) -> None:
    tag = getattr(area, "tag_redraw", None)
    if callable(tag):
        tag()


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
