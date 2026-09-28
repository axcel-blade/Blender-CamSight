"""Camera selection and property extraction without Blender."""

from blender_camsight.camera import (
    extract_camera_snapshot,
    horizon_direction,
    info_lines,
    is_camera_object,
    render_pixel_size,
    select_camera,
    snapshots_differ,
)


class _Data:
    def __init__(self, **kwargs):
        self.lens = kwargs.get("lens", 50.0)
        self.sensor_width = kwargs.get("sensor_width", 36.0)
        self.sensor_height = kwargs.get("sensor_height", 24.0)
        self.sensor_fit = kwargs.get("sensor_fit", "AUTO")
        self.shift_x = kwargs.get("shift_x", 0.0)
        self.shift_y = kwargs.get("shift_y", 0.0)
        self.clip_start = kwargs.get("clip_start", 0.1)
        self.clip_end = kwargs.get("clip_end", 100.0)
        self.type = kwargs.get("camera_type", "PERSP")
        self.ortho_scale = kwargs.get("ortho_scale", 6.0)


class _Object:
    def __init__(self, name, obj_type="CAMERA", **data):
        self.name = name
        self.type = obj_type
        self.data = _Data(**data) if obj_type == "CAMERA" else None
        self.matrix_world = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )


def test_render_pixel_size_applies_percentage():
    assert render_pixel_size(1920, 1080, 50) == (960, 540)
    assert render_pixel_size(1, 1, 1) == (1, 1)


def test_rejects_non_cameras():
    light = _Object("Sun", obj_type="LIGHT")
    assert not is_camera_object(light)
    assert extract_camera_snapshot(light, resolution_x=1920, resolution_y=1080, resolution_percentage=100) is None
    assert extract_camera_snapshot(None, resolution_x=1920, resolution_y=1080, resolution_percentage=100) is None


def test_selects_override_then_scene_camera():
    scene = _Object("SceneCam")
    picked = _Object("Picked")
    assert select_camera(scene, picked) is picked
    assert select_camera(scene, None) is scene
    assert select_camera(None, _Object("Lamp", obj_type="LIGHT")) is None


def test_snapshot_reads_framing_fields():
    camera = _Object("Hero", lens=35.0, shift_x=0.1, shift_y=-0.2, camera_type="PERSP")
    snapshot = extract_camera_snapshot(
        camera, resolution_x=1920, resolution_y=1080, resolution_percentage=100
    )
    assert snapshot is not None
    assert snapshot.name == "Hero"
    assert snapshot.lens == 35.0
    assert snapshot.shift_x == 0.1
    assert snapshot.resolution_x == 1920
    assert snapshot.aspect == 1920 / 1080
    lines = info_lines(snapshot)
    assert lines[0] == "CAMERA: Hero"
    assert "35.0mm" in lines[1]
    assert "1920" in lines[2]


def test_snapshot_token_changes_with_lens_and_transform():
    camera = _Object("Hero", lens=50.0)
    first = extract_camera_snapshot(camera, resolution_x=1920, resolution_y=1080, resolution_percentage=100)
    camera.data.lens = 85.0
    second = extract_camera_snapshot(camera, resolution_x=1920, resolution_y=1080, resolution_percentage=100)
    assert snapshots_differ(first, second)
    camera.data.lens = 50.0
    camera.matrix_world = (
        (1.0, 0.0, 0.0, 2.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
    moved = extract_camera_snapshot(camera, resolution_x=1920, resolution_y=1080, resolution_percentage=100)
    assert snapshots_differ(first, moved)


def test_ortho_info_uses_scale():
    camera = _Object("Top", camera_type="ORTHO", ortho_scale=4.5)
    snapshot = extract_camera_snapshot(camera, resolution_x=100, resolution_y=100, resolution_percentage=100)
    assert snapshot.camera_type == "ORTHO"
    assert "ORTHO" in info_lines(snapshot)[1]


def test_horizon_is_level_when_camera_up_matches_world_up():
    matrix = (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
    direction = horizon_direction(matrix)
    assert direction is not None
    dir_x, dir_y, _offset = direction
    assert abs(dir_y) < 1e-6
    assert abs(abs(dir_x) - 1.0) < 1e-6
