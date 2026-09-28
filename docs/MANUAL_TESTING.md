# Manual testing

Unit tests do not start Blender. Use this pass after installing `dist/Blender-CamSight.zip`.

1. Enable the add-on and confirm the **Blender-CamSight** tab is in the 3D Viewport sidebar.
2. Add a camera and a few objects. Enable the preview. Orbit the main view with the middle mouse button. The navigation gizmo should still orbit. Do not press Numpad 0.
3. Move and rotate the camera. The monitor should follow.
4. Change lens, sensor fit, shift, clip start, clip end, and orthographic scale. Compare with Camera View, then leave Camera View.
5. Change the render resolution and the resolution percentage. The letterbox and the info line should update.
6. Drag the header, drag the corner, and close the monitor.
7. Split the window into two 3D Viewports. Both should show the monitor. The Outliner, Properties, Shader Editor, and Image Editor should not.
8. Press Shift+C to hide and show the monitor. Disable the add-on and confirm the monitor and the shortcut are gone. Enable it again and confirm there is one monitor.
9. Enable **Camera Control**. Over the image, Ctrl-drag orbits, the wheel dollies, and WASD moves the camera. **Camera Lock** stops that input. Input outside the monitor still navigates the main view.

Record the Blender version from Help → About in the pull request.
