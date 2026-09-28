# Architecture

Blender-CamSight does not put the main 3D Viewport into Camera View. Blender cannot parent a second `VIEW_3D` inside an existing region, so the monitor is an offscreen viewport image drawn on top of the free view.

## Entry

`addon.py` adds `src/` to `sys.path` and calls `blender_camsight.register`. `__init__.py` re-exports that entry so a folder install still works. The zip module name is `camera_first_person_preview` because that string is a valid Python identifier.

## Package

| Module | Role |
| --- | --- |
| `addon.py` | Register classes, properties, handlers, and the keymap |
| `camera.py` | Choose a camera and read lens, sensor, shift, clips, and resolution |
| `preview.py` | Widget layout, hit testing, and redraw throttle |
| `viewport.py` | Limit drawing to `VIEW_3D` window regions |
| `drawing.py` | Offscreen camera image, blit, and overlays |
| `handlers.py` | Depsgraph updates and the draw handler |
| `operators.py` | Toggle, enable, disable, reset, and the modal session |
| `properties.py` | Scene settings for the sidebar |
| `panel.py` | 3D Viewport sidebar tab |
| `preferences.py` | Defaults and the shortcut |
| `constants.py` | Version, sizes, and colors |
| `registration.py` | Register and unregister order |

## Draw path

1. `depsgraph_update_post` marks the preview dirty and tags 3D View redraws.
2. The `POST_PIXEL` draw handler blits the cached texture.
3. When the cache is dirty, and at most about 24 times per second, `GPUOffScreen.draw_view3d` renders with `camera.matrix_world.inverted()` and `camera.calc_matrix_camera(...)`.
4. A re-entry guard stops that pass from painting the monitor into its own texture.

Orbiting the main view does not update the dependency graph, so it only blits.

## Tests

How to run the suite is in [TESTING.md](TESTING.md). `tests/` imports the pure helpers and does not start Blender. The Blender Docker target only checks registration.
