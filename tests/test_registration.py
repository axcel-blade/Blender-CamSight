"""Registration bookkeeping without Blender."""

import pytest

from blender_camsight.registration import add_unique, register_classes, remove_all, unregister_classes
from blender_camsight.viewport import find_view3d_window, is_compatible_region, region_local_mouse


class _Boom(Exception):
    pass


def test_register_and_unregister_order():
    seen = []

    def register(cls):
        seen.append(("reg", cls))

    def unregister(cls):
        seen.append(("unreg", cls))

    registered = register_classes(["A", "B", "C"], register)
    errors = unregister_classes(registered, unregister)
    assert errors == []
    assert seen == [
        ("reg", "A"),
        ("reg", "B"),
        ("reg", "C"),
        ("unreg", "C"),
        ("unreg", "B"),
        ("unreg", "A"),
    ]


def test_failed_register_rolls_back():
    live = []

    def register(cls):
        if cls == "B":
            raise _Boom()
        live.append(cls)

    def unregister(cls):
        live.remove(cls)

    register.unregister = unregister
    with pytest.raises(_Boom):
        register_classes(["A", "B"], register)
    assert live == []


def test_handlers_are_not_duplicated():
    collection = []
    assert add_unique(collection, "depsgraph") is True
    assert add_unique(collection, "depsgraph") is False
    assert collection == ["depsgraph"]
    assert remove_all(collection, "depsgraph") == 1
    assert remove_all(collection, "depsgraph") == 0


class _Region:
    def __init__(self, region_type, x, y, width, height):
        self.type = region_type
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class _Area:
    def __init__(self, area_type, regions):
        self.type = area_type
        self.regions = regions


def test_mouse_picks_the_3d_view_under_the_pointer():
    window = _Region("WINDOW", 100, 50, 400, 300)
    sidebar = _Region("UI", 500, 50, 200, 300)
    view = _Area("VIEW_3D", [sidebar, window])
    outliner = _Area("OUTLINER", [_Region("WINDOW", 0, 0, 80, 80)])
    area, region = find_view3d_window([outliner, view], 120, 80)
    assert area is view
    assert region is window
    assert region_local_mouse(120, 80, region.x, region.y) == (20, 30)
    assert find_view3d_window([outliner, view], 10, 10) == (None, None)
    assert find_view3d_window([outliner, view], 550, 80) == (None, None)


def test_preview_is_limited_to_view3d_windows():
    assert is_compatible_region("VIEW_3D", "WINDOW") is True
    assert is_compatible_region("VIEW_3D", "UI") is False
    for area in ("OUTLINER", "PROPERTIES", "TEXT_EDITOR", "NODE_EDITOR", "IMAGE_EDITOR"):
        assert is_compatible_region(area, "WINDOW") is False
