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
