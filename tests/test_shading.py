"""Preview shading follows the viewport, or stays on the sidebar choice."""

from blender_camsight.shading import (
    normalize_shading,
    resolve_preview_shading,
    shading_cache_token,
)


def test_follow_viewport_uses_the_viewport_mode():
    assert resolve_preview_shading(True, "SOLID", "WIREFRAME") == "WIREFRAME"
    assert resolve_preview_shading(True, "RENDERED", "MATERIAL") == "MATERIAL"


def test_manual_shading_ignores_viewport_changes():
    assert resolve_preview_shading(False, "MATERIAL", "SOLID") == "MATERIAL"
    assert resolve_preview_shading(False, "WIREFRAME", "RENDERED") == "WIREFRAME"


def test_unknown_shading_falls_back_to_solid():
    assert normalize_shading("BOGUS") == "SOLID"
    assert resolve_preview_shading(True, "SOLID", "BOGUS") == "SOLID"
    assert resolve_preview_shading(False, "BOGUS", "WIREFRAME") == "SOLID"


def test_cache_token_changes_when_the_drawn_shading_changes():
    camera = ("Camera", 50.0)
    assert shading_cache_token(camera, "SOLID") != shading_cache_token(camera, "WIREFRAME")
    assert shading_cache_token(camera, "MATERIAL") == (camera, "MATERIAL")


def test_shading_changes_are_not_drawn_inside_the_viewport_redraw():
    from blender_camsight.shading import cached_shading, refresh_must_leave_draw

    assert refresh_must_leave_draw("SOLID", "WIREFRAME", "SOLID") is True
    assert refresh_must_leave_draw("MATERIAL", "MATERIAL", "SOLID") is True
    assert refresh_must_leave_draw("SOLID", "SOLID", "SOLID") is False
    assert refresh_must_leave_draw("SOLID", "SOLID", None) is False
    assert refresh_must_leave_draw("SOLID", "SOLID", "SOLID", in_camera_view=True) is True
    from blender_camsight.shading import uses_workbench, workbench_needs_user_view

    assert uses_workbench("SOLID") is True
    assert uses_workbench("WIREFRAME") is True
    assert uses_workbench("MATERIAL") is False
    assert workbench_needs_user_view("CAMERA", "SOLID") is True
    assert workbench_needs_user_view("CAMERA", "WIREFRAME") is True
    assert workbench_needs_user_view("CAMERA", "RENDERED") is False
    assert workbench_needs_user_view("PERSP", "SOLID") is False
    token = shading_cache_token(("Camera",), "RENDERED")
    assert cached_shading(token) == "RENDERED"
    assert cached_shading(None) is None
