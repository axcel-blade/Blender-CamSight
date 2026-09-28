"""GPU drawing for the floating camera monitor.

The live image is produced by ``GPUOffScreen.draw_view3d`` using the camera
view and projection matrices. The main viewport's view matrix is never
replaced. The offscreen image is cached and blitted; it is rebuilt only when
the runtime is dirty and the redraw interval has elapsed.
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
from .viewport import is_compatible_region

_offscreen = None
_runtime = PreviewRuntime()


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


def _camera_matrices(context, camera_object, resolution_x: int, resolution_y: int):
    view_matrix = camera_object.matrix_world.inverted()
    projection = camera_object.calc_matrix_camera(
        context.evaluated_depsgraph_get(),
        x=resolution_x,
        y=resolution_y,
    )
    return view_matrix, projection


def _refresh_offscreen(context, camera_object, snapshot, frame) -> bool:
    import time

    token = snapshot.token()
    now = time.monotonic()
    if not should_refresh_now(token, now) and _offscreen is not None:
        return _offscreen is not None
    width = max(1, int(frame[2]))
    height = max(1, int(frame[3]))
    try:
        buffer = _ensure_offscreen(width, height)
        view_matrix, projection = _camera_matrices(
            context, camera_object, snapshot.resolution_x, snapshot.resolution_y
        )
        space = context.space_data
        region = context.region
        # Nested viewport draws re-enter this handler. The guard in draw_callback
        # skips them so the monitor is not baked into its own texture.
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
        _runtime.mark_clean(token, now)
        _runtime.error_reported = False
        return True
    except Exception as exc:
        if not _runtime.error_reported:
            _runtime.error_reported = True
            print(f"Camera Preview: offscreen draw failed ({exc})")
        return False


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
        _draw_rect_outline(layout.bounds, COLOR_BORDER, region_width, region_height)
        return

    frame = fit_aspect(layout.body, snapshot.aspect)
    _draw_rect(*frame, COLOR_EMPTY)
    if _refresh_offscreen(context, camera_object, snapshot, frame) and _offscreen is not None:
        gpu.state.depth_mask_set(False)
        draw_texture_2d(_offscreen.texture_color, (frame[0], frame[1]), frame[2], frame[3])

    _draw_overlays(settings, snapshot, frame, region_width, region_height)
    _draw_rect_outline(layout.bounds, COLOR_BORDER, region_width, region_height)


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
