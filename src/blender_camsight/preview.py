"""Preview layout, hit testing, and runtime flags.

This module does not talk to Blender. Operators and the draw callback keep a
single ``PreviewRuntime`` in sync with scene properties.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .constants import (
    CLOSE_BUTTON,
    HEADER_HEIGHT,
    RESIZE_HANDLE,
    WIDGET_MARGIN,
)

Rect = Tuple[float, float, float, float]


@dataclass
class PreviewLayout:
    x: float
    y: float
    width: float
    height: float
    header: float = HEADER_HEIGHT

    @property
    def bounds(self) -> Rect:
        return (self.x, self.y, self.width, self.height + self.header)

    @property
    def body(self) -> Rect:
        return (self.x, self.y, self.width, self.height)

    @property
    def header_rect(self) -> Rect:
        return (self.x, self.y + self.height, self.width, self.header)


@dataclass
class PreviewRuntime:
    """Process-local state that must not be stored on Blender RNA."""

    dirty: bool = True
    modal_running: bool = False
    session_pending: bool = False
    stop_requested: bool = False
    last_token: Optional[tuple] = None
    last_draw_time: float = 0.0
    draw_handler: Optional[object] = None
    error_reported: bool = False

    def mark_dirty(self) -> None:
        self.dirty = True

    def mark_clean(self, token: Optional[tuple], now: float) -> None:
        self.dirty = False
        self.last_token = token
        self.last_draw_time = now


def displayed_layout(
    x: float,
    y: float,
    width: float,
    height: float,
    region_width: float,
    region_height: float,
    header: float = HEADER_HEIGHT,
) -> PreviewLayout:
    """Layout actually drawn, after the widget is kept inside the region."""
    return clamp_layout(
        PreviewLayout(x=x, y=y, width=width, height=height, header=header),
        region_width,
        region_height,
    )


def apply_window_drag(
    mode: str,
    origin: Tuple[float, float],
    mouse: Tuple[float, float],
    start: PreviewLayout,
    region_width: float,
    region_height: float,
    min_size: float,
    max_size: float,
) -> Tuple[int, int, int, int]:
    """Move or resize from the bottom-right corner. Returns x, y, width, height.

    Move follows the pointer and keeps the widget, including its header, inside
    the region. Resize keeps the left edge and the top of the image fixed, so
    dragging the bottom-right grip down and right grows the window.
    """
    dx = mouse[0] - origin[0]
    dy = mouse[1] - origin[1]
    if mode == "move":
        moved = clamp_layout(
            PreviewLayout(
                x=start.x + dx,
                y=start.y + dy,
                width=start.width,
                height=start.height,
                header=start.header,
            ),
            region_width,
            region_height,
        )
        return _layout_box(moved)

    width = _clamp_size(start.width + dx, min_size, max_size)
    height = _clamp_size(start.height - dy, min_size, max_size)
    body_top = start.y + start.height
    room_above_bottom = body_top
    if room_above_bottom >= min_size:
        height = min(height, room_above_bottom)
    room_to_the_right = region_width - start.x
    if room_to_the_right >= min_size:
        width = min(width, room_to_the_right)
    y = body_top - height
    if y < 0:
        y = 0.0
    resized = clamp_layout(
        PreviewLayout(x=start.x, y=y, width=width, height=height, header=start.header),
        region_width,
        region_height,
    )
    return _layout_box(resized)


def _clamp_size(value: float, min_size: float, max_size: float) -> float:
    return min(max(value, min_size), max_size)


def _layout_box(layout: PreviewLayout) -> Tuple[int, int, int, int]:
    return (
        int(round(layout.x)),
        int(round(layout.y)),
        int(round(layout.width)),
        int(round(layout.height)),
    )


def clamp_layout(layout: PreviewLayout, region_width: float, region_height: float) -> PreviewLayout:
    """Keep the widget inside the region, including the header."""
    width = min(layout.width, max(1.0, region_width - 2.0))
    height = min(layout.height, max(1.0, region_height - layout.header - 2.0))
    total_h = height + layout.header
    x = min(max(0.0, layout.x), max(0.0, region_width - width))
    y = min(max(0.0, layout.y), max(0.0, region_height - total_h))
    return PreviewLayout(x=x, y=y, width=width, height=height, header=layout.header)


def fit_aspect(body: Rect, aspect: float) -> Rect:
    """Letterbox a camera frame of ``aspect`` (width/height) inside ``body``."""
    x, y, width, height = body
    if width <= 0 or height <= 0:
        return body
    safe_aspect = aspect if aspect > 0 else 1.0
    box_aspect = width / height
    if box_aspect > safe_aspect:
        fitted_h = height
        fitted_w = fitted_h * safe_aspect
        return (x + (width - fitted_w) * 0.5, y, fitted_w, fitted_h)
    fitted_w = width
    fitted_h = fitted_w / safe_aspect
    return (x, y + (height - fitted_h) * 0.5, fitted_w, fitted_h)


def inset_rect(rect: Rect, fraction: float) -> Rect:
    """Shrink ``rect`` so the result is ``fraction`` of its size, centered."""
    x, y, width, height = rect
    fitted_w = width * fraction
    fitted_h = height * fraction
    return (
        x + (width - fitted_w) * 0.5,
        y + (height - fitted_h) * 0.5,
        fitted_w,
        fitted_h,
    )


def thirds_lines(rect: Rect) -> Tuple[Tuple[Tuple[float, float], Tuple[float, float]], ...]:
    x, y, width, height = rect
    x1 = x + width / 3.0
    x2 = x + 2.0 * width / 3.0
    y1 = y + height / 3.0
    y2 = y + 2.0 * height / 3.0
    return (
        ((x1, y), (x1, y + height)),
        ((x2, y), (x2, y + height)),
        ((x, y1), (x + width, y1)),
        ((x, y2), (x + width, y2)),
    )


def crosshair_lines(rect: Rect, arm: float = 10.0) -> Tuple[Tuple[Tuple[float, float], Tuple[float, float]], ...]:
    x, y, width, height = rect
    cx = x + width * 0.5
    cy = y + height * 0.5
    return (
        ((cx - arm, cy), (cx + arm, cy)),
        ((cx, cy - arm), (cx, cy + arm)),
    )


def hit_test(layout: PreviewLayout, mouse_x: float, mouse_y: float) -> str:
    """Return which part of the widget contains a region-space point."""
    x, y, width, height = layout.x, layout.y, layout.width, layout.height
    if not (x <= mouse_x <= x + width and y <= mouse_y <= y + height + layout.header):
        return "outside"
    close_x = x + width - CLOSE_BUTTON - WIDGET_MARGIN * 0.5
    header_bottom = y + height
    if (
        mouse_y >= header_bottom
        and close_x <= mouse_x <= close_x + CLOSE_BUTTON
        and header_bottom <= mouse_y <= header_bottom + layout.header
    ):
        return "close"
    handle = RESIZE_HANDLE
    if mouse_x >= x + width - handle and mouse_y <= y + handle:
        return "resize"
    if mouse_y >= header_bottom:
        return "header"
    return "body"


def should_refresh(runtime: PreviewRuntime, token: Optional[tuple], now: float, interval: float) -> bool:
    """Refresh the offscreen image when content changed and the throttle allows it."""
    if runtime.dirty or runtime.last_token != token:
        return (now - runtime.last_draw_time) >= interval or runtime.last_token is None
    return False
