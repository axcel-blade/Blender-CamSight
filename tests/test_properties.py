"""Default preview settings live in one place and match the sidebar."""

from blender_camsight.constants import (
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
    SHADING_ITEMS,
)


def test_sidebar_defaults():
    assert DEFAULT_PREVIEW_WIDTH == 480
    assert DEFAULT_PREVIEW_HEIGHT == 270
    assert DEFAULT_PREVIEW_X == 20
    assert DEFAULT_PREVIEW_Y == 20
    assert DEFAULT_SHADING == "SOLID"
    assert DEFAULT_SHADING_FOLLOW is True
    assert DEFAULT_SHOW_FRAME is True
    assert DEFAULT_SHOW_CROSSHAIR is True
    assert DEFAULT_SHOW_THIRDS is False
    assert DEFAULT_SHOW_SAFE is False
    assert DEFAULT_SHOW_HORIZON is False
    assert DEFAULT_SHOW_INFO is True
    assert DEFAULT_CAMERA_CONTROL is False


def test_size_limits_and_shading_modes():
    assert MIN_PREVIEW_SIZE < DEFAULT_PREVIEW_WIDTH < MAX_PREVIEW_SIZE
    identifiers = [item[0] for item in SHADING_ITEMS]
    assert identifiers == ["SOLID", "WIREFRAME", "MATERIAL", "RENDERED"]
