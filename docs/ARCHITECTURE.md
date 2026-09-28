# Architecture

Blender-CamSight does not put the main 3D Viewport into Camera View. Blender cannot parent a second `VIEW_3D` inside an existing region, so the monitor is an offscreen viewport image drawn on top of the free view.

## Entry

`__init__.py` is the extension entry. It loads `addon.py`, which imports `src/blender_camsight` relatively and calls `register`. Bundled modules stay inside the extension package. Blender reports a policy violation if an extension edits `sys.path` or imports those files as top-level modules. The zip module name is `blender_camsight` because that string is a valid Python identifier. Blender shows the add-on as Blender-CamSight.

## Package

| Module | Role |
| --- | --- |
| `addon.py` | Register classes, properties, handlers, and the keymap |
| `camera.py` | Choose a camera and read lens, sensor, shift, clips, and resolution |
| `preview.py` | Widget layout, hit testing, and redraw throttle |
| `shading.py` | Choose auto or manual preview shading |
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

1. `depsgraph_update_post` marks the preview dirty and tags 3D View redraws. Restoring the viewport after a manual shading capture is ignored, so that restore is not treated as a scene edit.
2. The `POST_PIXEL` draw handler blits the cached texture and draws overlays. It does not call `draw_view3d`.
3. When the image is stale, that handler queues a capture. The modal timer runs `GPUOffScreen.draw_view3d` at most about 24 times per second, with `camera.matrix_world.inverted()` and `camera.calc_matrix_camera(...)`, then tags one blit.
4. **Auto Shading** uses the 3D Viewport mode: Solid, Wireframe, Material Preview, or Rendered. With Auto Shading off, the sidebar **Shading** menu is applied for that capture and the viewport mode is restored before the timer returns.
5. Solid and Wireframe are Workbench draws. If the viewport is in Camera View, the capture uses a perspective view for that call so Workbench keeps the camera matrices, then Camera View is restored.
6. A re-entry guard skips the draw handler during the capture so the monitor is not painted into its own texture.

Orbiting the main view does not update the dependency graph, so it only blits.

## Tests

How to run the suite is in [TESTING.md](TESTING.md). `tests/` imports the pure helpers and does not start Blender. The Blender Docker target only checks registration.
