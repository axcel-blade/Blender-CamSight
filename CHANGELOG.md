# Changelog

All notable changes to Blender-CamSight are documented here.

## 1.0.0

- Add a floating camera monitor that leaves the main 3D Viewport in free view.
- Draw the monitor with `GPUOffScreen.draw_view3d` and the active camera's view and projection matrices.
- Match lens, sensor, shift, clipping, orthographic scale, and render resolution, including resolution percentage.
- Add sidebar controls for camera choice, size, position, overlays, and optional camera control.
- Register Shift+C on the add-on keymap and remove it when the add-on is disabled.
- Package the add-on as `dist/Blender-CamSight.zip` with the importable module `blender_camsight`. Blender lists it as Blender-CamSight.
- Run unit tests with uv, and provide Docker targets for pytest and a headless Blender 4.5.14 register check.
