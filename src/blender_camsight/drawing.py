"""GPU drawing for the floating camera monitor.

The live image is produced by ``GPUOffScreen.draw_view3d`` using the camera
view and projection matrices. The main viewport's view matrix is never
replaced. The viewport draw callback only blits. The scene capture runs from
the add-on timer, outside that draw, so a shading change cannot re-enter
Camera View and lock Blender. Solid and Wireframe temporarily leave Camera
View for that one capture so Workbench uses the camera matrices, then the
view and any manual shading are restored.
The offscreen image is cached and blitted; it is rebuilt only when the
runtime is dirty and the redraw interval has elapsed.
"""

from __future__ import annotations

from typing import Optional

import gpu
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_texture_2d

from . import camera as camera_mod
from .constants import (
    COLOR_BORDER,
    COLOR_CHROME,
    COLOR_CROSSHAIR,
    COLOR_EMPTY,
    COLOR_HEADER,
    COLOR_HORIZON,
    COLOR_MUTED,
    COLOR_SAFE_ACTION,
    COLOR_SAFE_TITLE,
    COLOR_TEXT,
    COLOR_THIRDS,
    FONT_SIZE,
    MAX_OFFSCREEN_DIMENSION,
    MIN_REDRAW_INTERVAL,
    OVERLAY_LINE_WIDTH,
    RESIZE_HANDLE,
    SAFE_ACTION,
    SAFE_TITLE,
)
from .preview import (
    PreviewLayout,
    PreviewRuntime,
    crosshair_lines,
    fit_aspect,
    inset_rect,
    thirds_lines,
)
from .shading import (
    resolve_preview_shading,
    shading_cache_token,
    workbench_needs_user_view,
)
from .viewport import is_compatible_region

_offscreen = None
_runtime = PreviewRuntime()
# Ignores dependency-graph echoes caused by swapping shading for one offscreen draw.
_SHADING_SUPPRESS_SECONDS = 0.15
_shading_suppress_until = 0.0


def runtime() -> PreviewRuntime:
    return _runtime


def reset_runtime() -> None:
    global _runtime
    _runtime = PreviewRuntime()


def free_offscreen() -> None:
    global _offscreen
    if _offscreen is not None:
        try:
            _offscreen.free()
        except Exception:
            pass
        _offscreen = None


def _shader(name: str):
    return gpu.shader.from_builtin(name)


def _rect_batch(x: float, y: float, width: float, height: float):
    shader = _shader("UNIFORM_COLOR")
    batch = batch_for_shader(
        shader,
        "TRIS",
        {
            "pos": (
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y),
                (x + width, y + height),
                (x, y + height),
            )
        },
    )
    return shader, batch


def _draw_rect(x: float, y: float, width: float, height: float, color) -> None:
    if width <= 0 or height <= 0:
        return
    shader, batch = _rect_batch(x, y, width, height)
    gpu.state.blend_set("ALPHA")
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_line(start, end, color, region_width: float, region_height: float) -> None:
    shader = _shader("POLYLINE_UNIFORM_COLOR")
    batch = batch_for_shader(shader, "LINES", {"pos": (start, end)})
    shader.bind()
    shader.uniform_float("color", color)
    shader.uniform_float("lineWidth", OVERLAY_LINE_WIDTH)
    shader.uniform_float("viewport", (region_width, region_height))
    batch.draw(shader)


def _draw_rect_outline(rect, color, region_width: float, region_height: float) -> None:
    x, y, width, height = rect
    corners = (
        ((x, y), (x + width, y)),
        ((x + width, y), (x + width, y + height)),
        ((x + width, y + height), (x, y + height)),
        ((x, y + height), (x, y)),
    )
    for start, end in corners:
        _draw_line(start, end, color, region_width, region_height)


def _draw_text(x: float, y: float, text: str, color=COLOR_TEXT, size: int = FONT_SIZE) -> None:
    import blf

    font_id = 0
    blf.color(font_id, color[0], color[1], color[2], color[3])
    blf.size(font_id, size)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)


def _ensure_offscreen(width: int, height: int):
    global _offscreen
    width = max(1, min(int(width), MAX_OFFSCREEN_DIMENSION))
    height = max(1, min(int(height), MAX_OFFSCREEN_DIMENSION))
    if _offscreen is not None and (_offscreen.width != width or _offscreen.height != height):
        free_offscreen()
    if _offscreen is None:
        _offscreen = gpu.types.GPUOffScreen(width, height)
    return _offscreen


def shading_override_active() -> bool:
    """True while a preview draw has temporarily replaced viewport shading."""
    import time

    return time.monotonic() < _shading_suppress_until


def _arm_shading_suppress() -> None:
    """Cover the dependency-graph notice that follows a shading swap and restore."""
    import time

    global _shading_suppress_until
    _shading_suppress_until = time.monotonic() + _SHADING_SUPPRESS_SECONDS


def _viewport_shading_type(space) -> str:
    shading = getattr(space, "shading", None)
    return getattr(shading, "type", "") or ""


def _preview_shading_for_space(settings, space) -> str:
    return resolve_preview_shading(
        bool(getattr(settings, "shading_follow_viewport", True)),
        str(getattr(settings, "shading_mode", "SOLID")),
        _viewport_shading_type(space),
    )


def _preview_shading(context, settings) -> str:
    return _preview_shading_for_space(settings, getattr(context, "space_data", None))


def _queue_shading_refresh(width: int, height: int, shading_type: str) -> None:
    """Remember a stale image. The timer captures it, never this draw callback."""
    _runtime.pending_width = max(1, int(width))
    _runtime.pending_height = max(1, int(height))
    _runtime.pending_shading = shading_type
    _runtime.ready_to_capture = True
    _runtime.shading_refresh_pending = True
    _ensure_deferred_service()


def _ensure_deferred_service() -> None:
    try:
        import bpy

        if not bpy.app.timers.is_registered(_run_deferred_shading):
            bpy.app.timers.register(_run_deferred_shading, first_interval=0.0)
    except Exception:
        return


def _run_deferred_shading():
    import bpy

    service_deferred_shading(bpy.context)
    if _runtime.ready_to_capture and not _runtime.offscreen_rendering:
        return 0.05
    return None


def service_deferred_shading(context) -> None:
    """Capture one offscreen image outside the viewport draw callback."""
    if not _runtime.ready_to_capture or _runtime.offscreen_rendering:
        return
    if getattr(draw_callback, "_inside", False):
        return
    settings = _settings(context)
    if settings is None or not settings.preview_enabled:
        _runtime.ready_to_capture = False
        _runtime.shading_refresh_pending = False
        return
    window_manager = getattr(context, "window_manager", None)
    if window_manager is None:
        return
    from .viewport import find_view3d_space

    target = find_view3d_space(window_manager, prefer_camera_view=False)
    if target is None:
        return
    window, area, region, space = target
    drew = False
    _runtime.offscreen_rendering = True
    _runtime.ready_to_capture = False
    _runtime.shading_refresh_pending = False
    draw_callback._inside = True
    try:
        override = getattr(context, "temp_override", None)
        if callable(override):
            with context.temp_override(window=window, area=area, region=region):
                drew = _capture_offscreen(context, space, region)
        else:
            drew = _capture_offscreen(context, space, region)
    finally:
        draw_callback._inside = False
        _runtime.offscreen_rendering = False
    if drew:
        _tag_redraw(context)


def _capture_offscreen(context, space, region) -> bool:
    import time

    settings = _settings(context)
    if settings is None or not settings.preview_enabled:
        return False
    camera_object = _resolve_camera(context, settings)
    scene = getattr(context, "scene", None)
    render = getattr(scene, "render", None)
    if camera_object is None or render is None:
        return False
    snapshot = camera_mod.extract_camera_snapshot(
        camera_object,
        resolution_x=int(render.resolution_x),
        resolution_y=int(render.resolution_y),
        resolution_percentage=float(render.resolution_percentage),
    )
    if snapshot is None:
        return False
    shading_type = _runtime.pending_shading or _preview_shading_for_space(settings, space)
    token = shading_cache_token(snapshot.token(), shading_type)
    now = time.monotonic()
    if not should_refresh_now(token, now) and _offscreen is not None:
        _runtime.ready_to_capture = True
        _runtime.shading_refresh_pending = True
        return False
    width = _runtime.pending_width or int(settings.preview_width)
    height = _runtime.pending_height or int(settings.preview_height)
    _arm_shading_suppress()
    try:
        _draw_offscreen(context, camera_object, snapshot, width, height, space, region, shading_type)
        _runtime.mark_clean(token, now)
        _runtime.error_reported = False
        return True
    except Exception as exc:
        if not _runtime.error_reported:
            _runtime.error_reported = True
            print(f"Camera Preview: offscreen draw failed ({exc})")
        return False
    finally:
        _arm_shading_suppress()


def _tag_redraw(context) -> None:
    from .viewport import tag_view3d_redraws

    window_manager = getattr(context, "window_manager", None)
    if window_manager is not None:
        tag_view3d_redraws(window_manager)


def _remember_view(region_3d) -> dict:
    state = {"view_perspective": region_3d.view_perspective}
    if hasattr(region_3d, "view_distance"):
        state["view_distance"] = region_3d.view_distance
    for name in ("view_location", "view_rotation"):
        value = getattr(region_3d, name, None)
        if value is not None and hasattr(value, "copy"):
            state[name] = value.copy()
    return state


def _restore_view(region_3d, state) -> None:
    try:
        region_3d.view_perspective = state["view_perspective"]
        if "view_distance" in state:
            region_3d.view_distance = state["view_distance"]
        for name in ("view_location", "view_rotation"):
            if name in state:
                setattr(region_3d, name, state[name])
    except Exception as exc:
        print(f"Camera Preview: could not restore the viewport ({exc})")


def _draw_offscreen(context, camera_object, snapshot, width, height, space, region, shading_type: str) -> None:
    buffer = _ensure_offscreen(width, height)
    view_matrix, projection = _camera_matrices(
        context, camera_object, snapshot.resolution_x, snapshot.resolution_y
    )

    def _draw() -> None:
        region_3d = getattr(space, "region_3d", None)
        perspective = getattr(region_3d, "view_perspective", None)
        suspend = region_3d is not None and workbench_needs_user_view(perspective, shading_type)
        saved = _remember_view(region_3d) if suspend else None
        if suspend:
            region_3d.view_perspective = "PERSP"
        try:
            buffer.draw_view3d(
                context.scene,
                context.view_layer,
                space,
                region,
                view_matrix,
                projection,
                do_color_management=True,
                draw_background=True,
            )
        finally:
            if saved is not None:
                _restore_view(region_3d, saved)

    _draw_with_shading(space, shading_type, _draw)


def _draw_with_shading(space, shading_type: str, draw) -> None:
    """Draw once with ``shading_type``, then put the 3D Viewport shading back."""
    shading = getattr(space, "shading", None)
    current = _viewport_shading_type(space) if shading is not None else ""
    if shading is None or current == shading_type:
        draw()
        return
    previous = current
    _arm_shading_suppress()
    try:
        shading.type = shading_type
        draw()
    finally:
        try:
            if _viewport_shading_type(space) != previous:
                shading.type = previous
        except Exception as exc:
            print(f"Camera Preview: could not restore viewport shading ({exc})")
        _arm_shading_suppress()


def _camera_matrices(context, camera_object, resolution_x: int, resolution_y: int):
    view_matrix = camera_object.matrix_world.inverted()
    projection = camera_object.calc_matrix_camera(
        context.evaluated_depsgraph_get(),
        x=resolution_x,
        y=resolution_y,
    )
    return view_matrix, projection


def _refresh_offscreen(context, camera_object, snapshot, frame, shading_type: str) -> bool:
    """Blit path. Never calls ``draw_view3d`` — that re-enters the viewport and locks Blender."""
    import time

    if _runtime.offscreen_rendering:
        return _offscreen is not None
    token = shading_cache_token(snapshot.token(), shading_type)
    now = time.monotonic()
    if shading_override_active() and _offscreen is not None:
        return True
    stale = _runtime.dirty or _runtime.last_token != token or _runtime.last_token is None
    if not should_refresh_now(token, now) and _offscreen is not None:
        if stale:
            _runtime.mark_dirty()
            _queue_shading_refresh(int(frame[2]), int(frame[3]), shading_type)
        return True
    _queue_shading_refresh(int(frame[2]), int(frame[3]), shading_type)
    return _offscreen is not None


def should_refresh_now(token, now: float) -> bool:
    from .preview import should_refresh

    return should_refresh(_runtime, token, now, MIN_REDRAW_INTERVAL)


def _settings(context):
    return getattr(context.scene, "camera_preview", None)


def _resolve_camera(context, settings):
    selected = getattr(settings, "selected_camera", None) if settings else None
    return camera_mod.select_camera(context.scene.camera, selected)


def draw_callback() -> None:
    """POST_PIXEL callback. Installed once for every 3D View."""
    import bpy

    if _runtime.draw_handler is None:
        return
    context = bpy.context
    area = getattr(context, "area", None)
    region = getattr(context, "region", None)
    if area is None or region is None:
        return
    if not is_compatible_region(area.type, region.type):
        return
    settings = _settings(context)
    if settings is None or not settings.preview_enabled:
        return
    if getattr(draw_callback, "_inside", False):
        return

    draw_callback._inside = True
    try:
        _draw_widget(context, settings, region.width, region.height)
    finally:
        draw_callback._inside = False
        gpu.state.blend_set("NONE")
        gpu.state.depth_test_set("LESS_EQUAL")


def _draw_widget(context, settings, region_width: int, region_height: int) -> None:
    from .preview import clamp_layout

    layout = clamp_layout(
        PreviewLayout(
            x=float(settings.preview_position_x),
            y=float(settings.preview_position_y),
            width=float(settings.preview_width),
            height=float(settings.preview_height),
        ),
        region_width,
        region_height,
    )
    _draw_rect(layout.x, layout.y, layout.width, layout.height, COLOR_CHROME)
    header_x, header_y, header_w, header_h = layout.header_rect
    _draw_rect(header_x, header_y, header_w, header_h, COLOR_HEADER)
    _draw_text(header_x + 8, header_y + 8, "Camera Preview")
    _draw_text(header_x + header_w - 22, header_y + 8, "×")

    camera_object = _resolve_camera(context, settings)
    scene = context.scene
    render = scene.render
    snapshot = camera_mod.extract_camera_snapshot(
        camera_object,
        resolution_x=int(render.resolution_x),
        resolution_y=int(render.resolution_y),
        resolution_percentage=float(render.resolution_percentage),
    )
    if snapshot is None:
        _draw_text(layout.x + 16, layout.y + layout.height * 0.55, "No Active Camera", COLOR_TEXT, 16)
        _draw_text(
            layout.x + 16,
            layout.y + layout.height * 0.55 - 22,
            "Create or select a camera",
            COLOR_MUTED,
        )
        _draw_text(
            layout.x + 16,
            layout.y + layout.height * 0.55 - 40,
            "to enable the preview.",
            COLOR_MUTED,
        )
        _draw_chrome(layout, region_width, region_height)
        return

    frame = fit_aspect(layout.body, snapshot.aspect)
    _draw_rect(*frame, COLOR_EMPTY)
    shading_type = _preview_shading(context, settings)
    if _refresh_offscreen(context, camera_object, snapshot, frame, shading_type) and _offscreen is not None:
        gpu.state.depth_mask_set(False)
        draw_texture_2d(_offscreen.texture_color, (frame[0], frame[1]), frame[2], frame[3])

    _draw_overlays(settings, snapshot, frame, region_width, region_height)
    _draw_chrome(layout, region_width, region_height)


def _draw_chrome(layout, region_width: float, region_height: float) -> None:
    _draw_rect_outline(layout.bounds, COLOR_BORDER, region_width, region_height)
    _draw_resize_grip(layout, region_width, region_height)


def _draw_resize_grip(layout, region_width: float, region_height: float) -> None:
    """Diagonal marks in the bottom-right corner, matching the resize hit zone."""
    right = layout.x + layout.width
    bottom = layout.y
    grip = min(float(RESIZE_HANDLE), layout.width, layout.height)
    for inset in (4.0, 8.0, 12.0):
        if inset >= grip:
            continue
        _draw_line(
            (right - inset - 1.0, bottom + 2.0),
            (right - 2.0, bottom + inset + 1.0),
            COLOR_BORDER,
            region_width,
            region_height,
        )


def _draw_overlays(settings, snapshot, frame, region_width: float, region_height: float) -> None:
    if settings.show_camera_frame:
        _draw_rect_outline(frame, COLOR_BORDER, region_width, region_height)
    if settings.show_rule_of_thirds:
        for start, end in thirds_lines(frame):
            _draw_line(start, end, COLOR_THIRDS, region_width, region_height)
    if settings.show_safe_areas:
        _draw_rect_outline(inset_rect(frame, SAFE_ACTION), COLOR_SAFE_ACTION, region_width, region_height)
        _draw_rect_outline(inset_rect(frame, SAFE_TITLE), COLOR_SAFE_TITLE, region_width, region_height)
    if settings.show_crosshair:
        for start, end in crosshair_lines(frame):
            _draw_line(start, end, COLOR_CROSSHAIR, region_width, region_height)
    if settings.show_horizon:
        _draw_horizon(snapshot, frame, region_width, region_height)
    if settings.show_camera_info:
        x, y, _width, height = frame
        cursor_y = y + height - 18
        for line in camera_mod.info_lines(snapshot):
            _draw_text(x + 8, cursor_y, line, COLOR_TEXT, 12)
            cursor_y -= 16


def _draw_horizon(snapshot, frame, region_width: float, region_height: float) -> None:
    matrix = _matrix_from_flat(snapshot.matrix)
    if matrix is None:
        return
    direction = camera_mod.horizon_direction(matrix)
    if direction is None:
        return
    dir_x, dir_y, offset = direction
    x, y, width, height = frame
    cx = x + width * 0.5
    cy = y + height * 0.5 + offset * height
    span = max(width, height)
    start = (cx - dir_x * span, cy - dir_y * span)
    end = (cx + dir_x * span, cy + dir_y * span)
    _draw_line(start, end, COLOR_HORIZON, region_width, region_height)


def _matrix_from_flat(flat) -> Optional[list]:
    if len(flat) != 16:
        return None
    return [list(flat[i * 4 : i * 4 + 4]) for i in range(4)]
