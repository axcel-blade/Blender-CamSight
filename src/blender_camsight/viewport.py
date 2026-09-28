"""3D Viewport discovery.

The preview is drawn only in ``VIEW_3D`` window regions. Other editors never
receive the SpaceView3D draw handler, and this filter is a second guard.
"""

from __future__ import annotations

from typing import Any, Iterable, List


def is_view3d_area(area_type: str | None) -> bool:
    return area_type == "VIEW_3D"


def is_window_region(region_type: str | None) -> bool:
    return region_type == "WINDOW"


def is_compatible_region(area_type: str | None, region_type: str | None) -> bool:
    return is_view3d_area(area_type) and is_window_region(region_type)


def iter_view3d_areas(screen: Any) -> Iterable[Any]:
    areas = getattr(screen, "areas", None) or ()
    for area in areas:
        if is_view3d_area(getattr(area, "type", None)):
            yield area


def find_view3d_space(window_manager: Any, *, prefer_camera_view: bool = False):
    """Return ``(window, area, region, space)`` for a 3D Viewport, if one exists."""
    found = None
    windows = getattr(window_manager, "windows", None) or ()
    for window in windows:
        for area in iter_view3d_areas(getattr(window, "screen", None)):
            region = window_region(area)
            spaces = getattr(area, "spaces", None)
            space = getattr(spaces, "active", None) if spaces is not None else None
            if region is None or space is None:
                continue
            candidate = (window, area, region, space)
            if not prefer_camera_view:
                return candidate
            perspective = getattr(getattr(space, "region_3d", None), "view_perspective", None)
            if perspective == "CAMERA":
                return candidate
            if found is None:
                found = candidate
    return found


def tag_view3d_redraws(window_manager: Any) -> int:
    """Request a redraw of every 3D Viewport. Returns how many areas were tagged."""
    count = 0
    windows = getattr(window_manager, "windows", None) or ()
    for window in windows:
        for area in iter_view3d_areas(getattr(window, "screen", None)):
            tag = getattr(area, "tag_redraw", None)
            if callable(tag):
                tag()
                count += 1
    return count


def region_local_mouse(
    mouse_x: float,
    mouse_y: float,
    region_x: float,
    region_y: float,
) -> tuple[float, float]:
    """Convert window coordinates to a region's bottom-left origin."""
    return (mouse_x - region_x, mouse_y - region_y)


def find_view3d_window(areas: Any, mouse_x: float, mouse_y: float):
    """Return the 3D View window region that contains a window-space point."""
    for area in areas or ():
        if not is_view3d_area(getattr(area, "type", None)):
            continue
        for region in getattr(area, "regions", None) or ():
            if not is_window_region(getattr(region, "type", None)):
                continue
            x = float(getattr(region, "x", 0))
            y = float(getattr(region, "y", 0))
            width = float(getattr(region, "width", 0))
            height = float(getattr(region, "height", 0))
            if x <= mouse_x < x + width and y <= mouse_y < y + height:
                return area, region
    return None, None


def window_region(area: Any) -> Any:
    for region in getattr(area, "regions", None) or ():
        if is_window_region(getattr(region, "type", None)):
            return region
    return None


def collect_view3d_regions(window_manager: Any) -> List[Any]:
    found: List[Any] = []
    windows = getattr(window_manager, "windows", None) or ()
    for window in windows:
        for area in iter_view3d_areas(getattr(window, "screen", None)):
            region = window_region(area)
            if region is not None:
                found.append(region)
    return found
