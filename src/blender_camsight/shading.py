"""Choose the shading type drawn into the camera preview.

These helpers do not touch Blender. A shading change is rendered after the
viewport draw finishes, so Camera View is not asked to draw itself again.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from .constants import DEFAULT_SHADING, SHADING_ITEMS

SHADING_TYPES = tuple(item[0] for item in SHADING_ITEMS)


def normalize_shading(mode: Optional[str]) -> str:
    """Map a viewport or menu value onto a mode ``draw_view3d`` can show."""
    if mode in SHADING_TYPES:
        return str(mode)
    return DEFAULT_SHADING


def resolve_preview_shading(follow_viewport: bool, manual_mode: str, viewport_shading: str) -> str:
    """Follow the 3D Viewport, or keep the sidebar choice when follow is off."""
    if follow_viewport:
        return normalize_shading(viewport_shading)
    return normalize_shading(manual_mode)


def shading_cache_token(camera_token: Tuple[Any, ...], shading: str) -> Tuple[Any, ...]:
    """Cache identity for the camera plus the shading actually drawn."""
    return (camera_token, normalize_shading(shading))


def cached_shading(token: Optional[Tuple[Any, ...]]) -> Optional[str]:
    """Return the shading stored on a preview cache token."""
    if not token:
        return None
    shading = token[-1]
    if shading in SHADING_TYPES:
        return str(shading)
    return None


def uses_workbench(shading: str) -> bool:
    """Solid and Wireframe are drawn by Workbench, not the render engine."""
    return normalize_shading(shading) in ("SOLID", "WIREFRAME")


def workbench_needs_user_view(view_perspective: Optional[str], shading: str) -> bool:
    """Camera View makes Workbench ignore the matrices passed to ``draw_view3d``."""
    return view_perspective == "CAMERA" and uses_workbench(shading)


def refresh_must_leave_draw(
    viewport_shading: str,
    preview_shading: str,
    previous_shading: Optional[str],
    *,
    in_camera_view: bool = False,
) -> bool:
    """True when the offscreen pass must not run inside the viewport draw.

    Drawing the scene, or writing ``SpaceView3D.shading``, while Blender is
    already redrawing that viewport locks the UI. Camera View is included:
    its redraw is the viewport draw, so a shading change there must wait.
    """
    if in_camera_view:
        return True
    if viewport_shading != preview_shading:
        return True
    if previous_shading is None:
        return False
    return previous_shading != preview_shading
