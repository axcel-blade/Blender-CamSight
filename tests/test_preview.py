"""Preview geometry, hit testing, and redraw throttling."""

from blender_camsight.preview import (
    PreviewLayout,
    PreviewRuntime,
    clamp_layout,
    crosshair_lines,
    fit_aspect,
    hit_test,
    inset_rect,
    should_refresh,
    thirds_lines,
)


def test_fit_aspect_letterboxes_wide_frame():
    frame = fit_aspect((0, 0, 100, 100), 2.0)
    assert frame[2] == 100
    assert frame[3] == 50
    assert frame[1] == 25


def test_fit_aspect_pillarboxes_tall_frame():
    frame = fit_aspect((10, 0, 100, 50), 1.0)
    assert frame[2] == 50
    assert frame[3] == 50
    assert frame[0] == 35


def test_thirds_and_safe_areas():
    lines = thirds_lines((0, 0, 90, 90))
    assert lines[0][0] == (30, 0)
    assert lines[2][0][1] == 30
    safe = inset_rect((0, 0, 100, 50), 0.9)
    assert abs(safe[2] - 90) < 1e-6
    assert abs(safe[0] - 5) < 1e-6


def test_crosshair_is_centered():
    lines = crosshair_lines((0, 0, 80, 40), arm=10)
    assert lines[0][0] == (30, 20)
    assert lines[0][1] == (50, 20)


def test_hit_regions():
    layout = PreviewLayout(x=0, y=0, width=200, height=100, header=28)
    assert hit_test(layout, 10, 10) == "body"
    assert hit_test(layout, 10, 110) == "header"
    assert hit_test(layout, 190, 110) == "close"
    assert hit_test(layout, 195, 4) == "resize"
    assert hit_test(layout, -1, 10) == "outside"


def test_clamp_keeps_widget_inside_region():
    layout = PreviewLayout(x=500, y=500, width=480, height=270, header=28)
    clamped = clamp_layout(layout, 400, 300)
    assert clamped.x + clamped.width <= 400
    assert clamped.y + clamped.height + clamped.header <= 300


def test_refresh_throttle_and_dirty_flag():
    runtime = PreviewRuntime()
    assert should_refresh(runtime, ("a",), 1.0, 0.5) is True
    runtime.mark_clean(("a",), 1.0)
    assert should_refresh(runtime, ("a",), 1.2, 0.5) is False
    runtime.mark_dirty()
    assert should_refresh(runtime, ("a",), 1.2, 0.5) is False
    assert should_refresh(runtime, ("a",), 1.6, 0.5) is True
    assert should_refresh(runtime, ("b",), 2.2, 0.5) is True
