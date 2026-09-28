# Changelog

All notable changes to Blender-CamSight are documented here.

## Unreleased

- Add **Auto Shading**, on by default, so the preview follows the 3D Viewport header: Solid, Wireframe, Material Preview, and Rendered.
- Add a manual **Shading** menu, used when Auto Shading is off, that changes the preview without leaving the main viewport on that mode.
- Capture the preview from a timer instead of from inside the viewport draw, so changing shading does not lock Blender.
- Draw Solid and Wireframe through the camera frame when the viewport is in Camera View, then restore that view.

## 1.0.0

- Add a floating camera monitor that leaves the main 3D Viewport in free view.
- Draw the monitor with `GPUOffScreen.draw_view3d` and the active camera's view and projection matrices.
- Match lens, sensor, shift, clipping, orthographic scale, and render resolution, including resolution percentage.
- Add sidebar controls for camera choice, size, position, overlays, and optional camera control.
- Register Shift+C on the add-on keymap and remove it when the add-on is disabled.
- Package the add-on as `dist/Blender-CamSight.zip` with the importable module `blender_camsight`. Blender lists it as Blender-CamSight.
- Import bundled modules as part of the extension package so Blender does not warn about `sys.path` or top-level module policy violations.
- Run unit tests with uv, and provide Docker targets for pytest and a headless Blender 4.5.14 register check.
