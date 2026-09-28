"""Scene properties for the camera preview."""

from __future__ import annotations

import bpy

from .constants import (
    DEFAULT_CAMERA_CONTROL,
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
    MAX_PREVIEW_SIZE,
    MIN_PREVIEW_SIZE,
    SCENE_POINTER,
    SHADING_ITEMS,
)

_syncing = False


def _poll_camera(_settings, obj) -> bool:
    return getattr(obj, "type", None) == "CAMERA"


def _on_preview_enabled(self, context) -> None:
    global _syncing
    if _syncing:
        return
    from .drawing import runtime

    runtime().mark_dirty()
    if self.preview_enabled:
        from .operators import ensure_session

        ensure_session()
    else:
        runtime().stop_requested = True
    _tag(context)


def _on_changed(self, context) -> None:
    from .drawing import runtime

    runtime().mark_dirty()
    _tag(context)


def _on_position_changed(self, context) -> None:
    """Redraw the overlay without rebuilding the cached camera image."""
    _tag(context)


def _viewport_shading(context) -> str:
    space = getattr(context, "space_data", None)
    shading = getattr(space, "shading", None) if space is not None else None
    return getattr(shading, "type", "") or ""


def _on_shading_follow_changed(self, context) -> None:
    """Start a manual choice from the viewport shading so the preview does not jump."""
    if not self.shading_follow_viewport:
        current = _viewport_shading(context)
        manual_modes = {item[0] for item in SHADING_ITEMS}
        if current in manual_modes and self.shading_mode != current:
            self.shading_mode = current
            return
    _on_changed(self, context)


def _tag(context) -> None:
    from .viewport import tag_view3d_redraws

    window_manager = getattr(context, "window_manager", None)
    if window_manager is not None:
        tag_view3d_redraws(window_manager)


def set_preview_enabled(settings, value: bool) -> None:
    """Write the enable flag without re-entering the update callback."""
    global _syncing
    _syncing = True
    try:
        settings.preview_enabled = value
    finally:
        _syncing = False


class CameraPreviewSettings(bpy.types.PropertyGroup):
    preview_enabled: bpy.props.BoolProperty(
        name="Enable Preview",
        description="Show the live camera monitor in 3D Viewports",
        default=False,
        update=_on_preview_enabled,
    )
    selected_camera: bpy.props.PointerProperty(
        name="Camera",
        description="Camera used by the preview. Empty uses the scene camera",
        type=bpy.types.Object,
        poll=_poll_camera,
        update=_on_changed,
    )
    preview_width: bpy.props.IntProperty(
        name="Width",
        default=DEFAULT_PREVIEW_WIDTH,
        min=MIN_PREVIEW_SIZE,
        max=MAX_PREVIEW_SIZE,
        update=_on_changed,
    )
    preview_height: bpy.props.IntProperty(
        name="Height",
        default=DEFAULT_PREVIEW_HEIGHT,
        min=MIN_PREVIEW_SIZE,
        max=MAX_PREVIEW_SIZE,
        update=_on_changed,
    )
    preview_position_x: bpy.props.IntProperty(
        name="X",
        description="Distance from the left of the 3D Viewport",
        default=DEFAULT_PREVIEW_X,
        min=0,
        max=10000,
        update=_on_position_changed,
    )
    preview_position_y: bpy.props.IntProperty(
        name="Y",
        description="Distance from the bottom of the 3D Viewport",
        default=DEFAULT_PREVIEW_Y,
        min=0,
        max=10000,
        update=_on_position_changed,
    )
    shading_follow_viewport: bpy.props.BoolProperty(
        name="Auto Shading",
        description=(
            "Match the camera preview to this 3D Viewport's shading. "
            "Turn off to choose Solid, Wireframe, Material Preview, or Rendered "
            "for the preview only"
        ),
        default=DEFAULT_SHADING_FOLLOW,
        update=_on_shading_follow_changed,
    )
    shading_mode: bpy.props.EnumProperty(
        name="Shading",
        description=(
            "Shading drawn in the camera preview when Auto Shading is off. "
            "The main 3D Viewport is restored after each preview draw"
        ),
        items=SHADING_ITEMS,
        default=DEFAULT_SHADING,
        update=_on_changed,
    )
    show_camera_frame: bpy.props.BoolProperty(
        name="Camera Frame",
        default=DEFAULT_SHOW_FRAME,
        update=_on_changed,
    )
    show_crosshair: bpy.props.BoolProperty(
        name="Crosshair",
        default=DEFAULT_SHOW_CROSSHAIR,
        update=_on_changed,
    )
    show_rule_of_thirds: bpy.props.BoolProperty(
        name="Rule of Thirds",
        default=DEFAULT_SHOW_THIRDS,
        update=_on_changed,
    )
    show_safe_areas: bpy.props.BoolProperty(
        name="Safe Areas",
        default=DEFAULT_SHOW_SAFE,
        update=_on_changed,
    )
    show_horizon: bpy.props.BoolProperty(
        name="Horizon Line",
        default=DEFAULT_SHOW_HORIZON,
        update=_on_changed,
    )
    show_camera_info: bpy.props.BoolProperty(
        name="Camera Information",
        default=DEFAULT_SHOW_INFO,
        update=_on_changed,
    )
    camera_control_enabled: bpy.props.BoolProperty(
        name="Camera Control",
        description="Pointer over the preview orbits, dollies, and flies the camera",
        default=DEFAULT_CAMERA_CONTROL,
        update=_on_changed,
    )
    camera_lock: bpy.props.BoolProperty(
        name="Camera Lock",
        description="Keep showing the preview but ignore camera control input",
        default=False,
        update=_on_changed,
    )


def register_properties() -> None:
    bpy.types.Scene.camera_preview = bpy.props.PointerProperty(type=CameraPreviewSettings)


def unregister_properties() -> None:
    pointer = getattr(bpy.types.Scene, SCENE_POINTER, None)
    if pointer is not None:
        del bpy.types.Scene.camera_preview
