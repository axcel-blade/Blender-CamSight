"""Camera lookup, validation, and property extraction.

Drawing does not belong in this module. Functions accept plain objects so the
math can be tested without Blender.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence, Tuple

CAMERA_TYPES = ("PERSP", "ORTHO", "PANO")
MatrixComponents = Tuple[float, ...]


@dataclass(frozen=True)
class CameraSnapshot:
    """Values the preview needs from one camera at one moment."""

    name: str
    lens: float
    sensor_width: float
    sensor_height: float
    sensor_fit: str
    shift_x: float
    shift_y: float
    clip_start: float
    clip_end: float
    camera_type: str
    ortho_scale: float
    resolution_x: int
    resolution_y: int
    matrix: MatrixComponents

    @property
    def aspect(self) -> float:
        if self.resolution_y <= 0:
            return 1.0
        return self.resolution_x / float(self.resolution_y)

    def token(self) -> Tuple[Any, ...]:
        """Identity used to detect camera, lens, and resolution changes."""
        return (
            self.name,
            round(self.lens, 4),
            round(self.sensor_width, 4),
            round(self.sensor_height, 4),
            self.sensor_fit,
            round(self.shift_x, 5),
            round(self.shift_y, 5),
            round(self.clip_start, 5),
            round(self.clip_end, 5),
            self.camera_type,
            round(self.ortho_scale, 5),
            self.resolution_x,
            self.resolution_y,
            self.matrix,
        )


def render_pixel_size(resolution_x: int, resolution_y: int, percentage: float) -> Tuple[int, int]:
    """Apply Blender's resolution percentage and keep both axes at least 1."""
    scale = max(0.01, float(percentage)) / 100.0
    return (
        max(1, int(round(resolution_x * scale))),
        max(1, int(round(resolution_y * scale))),
    )


def _matrix_components(matrix: Any) -> MatrixComponents:
    if matrix is None:
        return tuple()
    rows: list[float] = []
    try:
        for row in matrix:
            for value in row:
                rows.append(round(float(value), 5))
    except TypeError:
        return tuple()
    return tuple(rows)


def is_camera_object(obj: Any) -> bool:
    if obj is None:
        return False
    if getattr(obj, "type", None) != "CAMERA":
        return False
    data = getattr(obj, "data", None)
    return data is not None and hasattr(data, "lens")


def select_camera(scene_camera: Any, selected_camera: Any) -> Optional[Any]:
    """Prefer the user's pick, then the scene camera. Never raises."""
    if is_camera_object(selected_camera):
        return selected_camera
    if is_camera_object(scene_camera):
        return scene_camera
    return None


def extract_camera_snapshot(
    camera: Any,
    *,
    resolution_x: int,
    resolution_y: int,
    resolution_percentage: float,
) -> Optional[CameraSnapshot]:
    """Read framing-related camera data. Returns None when the object is unusable."""
    if not is_camera_object(camera):
        return None
    data = camera.data
    camera_type = getattr(data, "type", "PERSP")
    if camera_type not in CAMERA_TYPES:
        camera_type = "PERSP"
    width, height = render_pixel_size(resolution_x, resolution_y, resolution_percentage)
    try:
        return CameraSnapshot(
            name=str(getattr(camera, "name", "Camera")),
            lens=float(getattr(data, "lens", 50.0)),
            sensor_width=float(getattr(data, "sensor_width", 36.0)),
            sensor_height=float(getattr(data, "sensor_height", 24.0)),
            sensor_fit=str(getattr(data, "sensor_fit", "AUTO")),
            shift_x=float(getattr(data, "shift_x", 0.0)),
            shift_y=float(getattr(data, "shift_y", 0.0)),
            clip_start=float(getattr(data, "clip_start", 0.1)),
            clip_end=float(getattr(data, "clip_end", 1000.0)),
            camera_type=camera_type,
            ortho_scale=float(getattr(data, "ortho_scale", 1.0)),
            resolution_x=width,
            resolution_y=height,
            matrix=_matrix_components(getattr(camera, "matrix_world", None)),
        )
    except (TypeError, ValueError):
        return None


def snapshots_differ(previous: Optional[CameraSnapshot], current: Optional[CameraSnapshot]) -> bool:
    if previous is None or current is None:
        return previous is not current
    return previous.token() != current.token()


def projection_arguments(snapshot: CameraSnapshot) -> Tuple[int, int]:
    """Pixel size passed to ``Camera.calc_matrix_camera`` so aspect matches the render."""
    return snapshot.resolution_x, snapshot.resolution_y


def info_lines(snapshot: CameraSnapshot) -> Sequence[str]:
    lens = f"{snapshot.ortho_scale:.3f}" if snapshot.camera_type == "ORTHO" else f"{snapshot.lens:.1f}mm"
    label = "ORTHO" if snapshot.camera_type == "ORTHO" else "LENS"
    return (
        f"CAMERA: {snapshot.name}",
        f"{label}: {lens}",
        f"RESOLUTION: {snapshot.resolution_x} × {snapshot.resolution_y}",
    )


def horizon_direction(matrix: Sequence[Sequence[float]]) -> Optional[Tuple[float, float, float]]:
    """Screen-space world horizon inside the camera frame.

    Blender cameras look down local -Z, with local +Y as sensor up.
    Returns ``(dir_x, dir_y, offset)`` in normalized frame coordinates
    (0–1, origin bottom-left). ``offset`` is the vertical shift of the
    horizon from the frame center, in the same normalized units.
    Returns None when the world up vector is not available.
    """
    if len(matrix) < 3:
        return None
    try:
        right = (float(matrix[0][0]), float(matrix[1][0]), float(matrix[2][0]))
        up = (float(matrix[0][1]), float(matrix[1][1]), float(matrix[2][1]))
        back = (float(matrix[0][2]), float(matrix[1][2]), float(matrix[2][2]))
    except (IndexError, TypeError, ValueError):
        return None
    world_up = (0.0, 0.0, 1.0)
    screen_x = right[0] * world_up[0] + right[1] * world_up[1] + right[2] * world_up[2]
    screen_y = up[0] * world_up[0] + up[1] * world_up[1] + up[2] * world_up[2]
    forward_z = -(back[0] * world_up[0] + back[1] * world_up[1] + back[2] * world_up[2])
    length = (screen_x * screen_x + screen_y * screen_y) ** 0.5
    if length < 1e-6:
        return None
    # Horizon is perpendicular to the projected world-up vector.
    dir_x = -screen_y / length
    dir_y = screen_x / length
    offset = max(-1.5, min(1.5, forward_z * 0.5))
    return (dir_x, dir_y, offset)
