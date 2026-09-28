"""Preview geometry, hit testing, and redraw throttling."""

from blender_camsight.preview import (
    PreviewLayout,
    PreviewRuntime,
    apply_window_drag,
    clamp_layout,
    crosshair_lines,
    displayed_layout,
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


def test_move_follows_the_pointer_and_stays_on_screen():
    start = PreviewLayout(x=20, y=40, width=200, height=100, header=28)
    assert apply_window_drag("move", (0, 0), (15, -10), start, 800, 600, 160, 1280) == (35, 30, 200, 100)
    assert apply_window_drag("move", (0, 0), (-100, -100), start, 800, 600, 160, 1280) == (0, 0, 200, 100)
    moved_up = apply_window_drag("move", (0, 0), (0, 1000), start, 800, 600, 160, 1280)
    assert moved_up[0] == 20
    assert moved_up[1] + moved_up[3] + 28 <= 600


def test_resize_from_the_bottom_right_keeps_the_top_fixed():
    start = PreviewLayout(x=20, y=40, width=200, height=100, header=28)
    grown = apply_window_drag("resize", (100, 100), (150, 70), start, 800, 600, 50, 1280)
    assert grown == (20, 10, 250, 130)
    assert grown[1] + grown[3] == 140

    shrunk = apply_window_drag("resize", (0, 0), (0, 25), start, 800, 600, 50, 1280)
    assert shrunk == (20, 65, 200, 75)
    assert shrunk[1] + shrunk[3] == 140


def test_resize_stops_at_the_region_edge_and_size_limits():
    start = PreviewLayout(x=20, y=40, width=200, height=100, header=28)
    limited = apply_window_drag("resize", (0, 0), (-500, 500), start, 800, 600, 160, 1280)
    assert limited[2] == 160
    assert limited[3] == 160

    high = PreviewLayout(x=20, y=400, width=200, height=200, header=28)
    capped = apply_window_drag("resize", (0, 0), (5000, -5000), high, 2000, 2000, 160, 480)
    assert capped[2] == 480
    assert capped[3] == 480
    assert capped[1] + capped[3] == 600

    pinned = apply_window_drag(
        "resize",
        (0, 0),
        (0, -300),
        PreviewLayout(x=20, y=50, width=200, height=200, header=28),
        800,
        600,
        50,
        1280,
    )
    assert pinned[1] == 0
    assert pinned[1] + pinned[3] == 250


def test_hit_test_matches_the_drawn_widget_when_stored_position_is_offscreen():
    layout = displayed_layout(500, 500, 480, 270, 400, 300)
    assert hit_test(layout, layout.x + 8, layout.y + layout.height + 4) == "header"
    assert hit_test(layout, layout.x + layout.width - 4, layout.y + 4) == "resize"
    assert layout.x + layout.width <= 400
    assert layout.y + layout.height + layout.header <= 300


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
