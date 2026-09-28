"""Project-wide constants for Blender-CamSight."""

from __future__ import annotations

ADDON_ID = "blender_camsight"
ADDON_NAME = "Blender-CamSight"
ADDON_VERSION = (1, 1, 0)
ADDON_VERSION_STRING = ".".join(str(part) for part in ADDON_VERSION)

# Documented against the Blender 4.5 Python API (gpu.types.GPUOffScreen.draw_view3d).
BLENDER_API_VERSION = (4, 5, 0)
MIN_BLENDER_VERSION = (4, 2, 0)

PACKAGE_NAME = "blender_camsight"
PANEL_CATEGORY = ADDON_NAME
SCENE_POINTER = "camera_preview"

# Preview widget defaults. Origin is the bottom-left of the 3D region.
DEFAULT_PREVIEW_WIDTH = 480
DEFAULT_PREVIEW_HEIGHT = 270
DEFAULT_PREVIEW_X = 20
DEFAULT_PREVIEW_Y = 20
MIN_PREVIEW_SIZE = 160
MAX_PREVIEW_SIZE = 1280

HEADER_HEIGHT = 28
RESIZE_HANDLE = 14
CLOSE_BUTTON = 18
WIDGET_MARGIN = 8

DEFAULT_SHADING = "SOLID"
DEFAULT_SHADING_FOLLOW = True
SHADING_ITEMS = (
    ("SOLID", "Solid", "Solid shading in the camera preview"),
    ("WIREFRAME", "Wireframe", "Wireframe shading in the camera preview"),
    ("MATERIAL", "Material Preview", "Material Preview shading in the camera preview"),
    ("RENDERED", "Rendered", "Rendered shading in the camera preview"),
)

DEFAULT_SHOW_FRAME = True
DEFAULT_SHOW_CROSSHAIR = True
DEFAULT_SHOW_THIRDS = False
DEFAULT_SHOW_SAFE = False
DEFAULT_SHOW_HORIZON = False
DEFAULT_SHOW_INFO = True
DEFAULT_CAMERA_CONTROL = False

# Action-safe and title-safe insets, as fractions of the camera frame.
SAFE_ACTION = 0.90
SAFE_TITLE = 0.80

# Offscreen redraw throttle. Navigation of the main view only blits the cache.
MIN_REDRAW_INTERVAL = 1.0 / 24.0
MAX_OFFSCREEN_DIMENSION = 960

# GPU overlay colors, RGBA.
COLOR_CHROME = (0.08, 0.08, 0.08, 0.88)
COLOR_HEADER = (0.12, 0.12, 0.12, 0.94)
COLOR_BORDER = (0.95, 0.95, 0.95, 0.90)
COLOR_CROSSHAIR = (1.0, 1.0, 1.0, 0.85)
COLOR_THIRDS = (1.0, 1.0, 1.0, 0.45)
COLOR_SAFE_ACTION = (1.0, 0.85, 0.2, 0.70)
COLOR_SAFE_TITLE = (0.3, 0.85, 1.0, 0.70)
COLOR_HORIZON = (0.4, 1.0, 0.55, 0.80)
COLOR_TEXT = (1.0, 1.0, 1.0, 0.95)
COLOR_MUTED = (0.75, 0.75, 0.75, 0.9)
COLOR_EMPTY = (0.15, 0.15, 0.15, 0.85)

OVERLAY_LINE_WIDTH = 1.0
FONT_SIZE = 13

# Camera interaction.
ORBIT_SENSITIVITY = 0.005
DOLLY_STEP = 0.25
MOVE_SPEED = 1.5
FAST_MOVE_MULTIPLIER = 3.0
CONTROL_TIMER_SECONDS = 0.016

DEFAULT_SHORTCUT_KEY = "C"
DEFAULT_SHORTCUT_SHIFT = True
DEFAULT_SHORTCUT_CTRL = False
DEFAULT_SHORTCUT_ALT = False

KEYMAP_NAME = "3D View"
KEYMAP_SPACE = "VIEW_3D"
TOGGLE_OPERATOR_ID = "camera_preview.toggle"
