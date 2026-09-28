# Blender-CamSight

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](CHANGELOG.md)
[![Release](https://img.shields.io/github/v/release/axcel-blade/Blender-CamSight)](https://github.com/axcel-blade/Blender-CamSight/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.md)

A Blender add-on that keeps the main 3D Viewport in its normal free view and shows a separate live monitor of what the active camera sees.

This add-on does not force the user's main viewport into Camera View. It provides a separate live camera perspective while preserving the user's normal viewport.

```text
                    NORMAL USER VIEW
┌──────────────────────────────────────────────────────┐
│                         Cube                         │
│       Camera                                         │
│         📷 ───────────────────────────►              │
│                              ┌────────────────────┐  │
│                              │   CAMERA VIEW      │  │
│                              │   First Person     │  │
│                              └────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## Features

- Floating camera monitor drawn inside 3D Viewports only
- Live view and projection from the scene camera or a chosen camera
- Respects lens, sensor, shift, clips, ortho scale, and render resolution
- Move, resize, and close the monitor without covering the rest of Blender
- Overlays: camera frame, crosshair, rule of thirds, safe areas, horizon, camera info
- Sidebar controls and a removable Shift+C toggle
- Optional camera control (orbit, dolly, WASD) when the pointer is over the monitor

## Requirements

- Blender 4.2 or newer. The offscreen viewport call is the one documented in the Blender 4.5 Python API (`gpu.types.GPUOffScreen.draw_view3d`).
- No third-party Python packages. The add-on uses `bpy`, `gpu`, `gpu_extras`, and `blf`.

## Installation

Install a zip, not this repository folder. `Blender-CamSight` contains a hyphen, so Blender cannot import that folder as an add-on.

### Download from release

1. Download `Blender-CamSight.zip` from the [latest release](https://github.com/axcel-blade/Blender-CamSight/releases/latest).
2. In Blender 4.2 or newer, choose Edit → Preferences → Add-ons → Install from Disk and select the zip.
3. Enable **Blender-CamSight**.

### Zip from repo

1. From the repository root, build the zip:

```text
uv run python main.py zip
```

2. In Blender, choose Edit → Preferences → Add-ons → Install from Disk and select `dist/Blender-CamSight.zip`.
3. Enable **Blender-CamSight**.

The packaged module is named `blender_camsight`. Blender lists the add-on as **Blender-CamSight**.

## Usage

1. Open the 3D Viewport sidebar (N) and choose the **Blender-CamSight** tab.
2. Enable **Enable Preview**, or press Shift+C.
3. Orbit, pan, zoom, and edit the scene in the main view. The monitor keeps showing the camera.

If the scene has no camera, the monitor shows **No Active Camera** instead of raising an error.

## Camera Preview

The monitor is a 2D overlay in the 3D Viewport window region. Its image is a cached offscreen draw of the viewport, using:

- view matrix: `camera.matrix_world.inverted()`
- projection matrix: `camera.calc_matrix_camera(...)` with the render resolution (including resolution percentage)

The image is letterboxed to the render aspect ratio inside the widget. Drag the header to move it. Drag the bottom-right corner to resize it. The × button hides it. Position values are measured from the bottom-left of the 3D region, which is the GPU origin.

The offscreen image is rebuilt when the dependency graph updates (camera, objects, lens, sensor, resolution) and at most about 24 times per second. Orbiting the main view only blits the cached image.

## Controls

| Action | Input |
| --- | --- |
| Toggle the monitor | Shift+C (change this in add-on preferences) |
| Move the monitor | Drag the header |
| Resize the monitor | Drag the bottom-right corner |
| Hide the monitor | × on the header, the sidebar checkbox, or Shift+C |
| Orbit the camera | Enable Camera Control, hover the image, Ctrl-drag |
| Dolly the camera | Mouse wheel over the monitor |
| Fly the camera | W A S D, Q down, E up. Hold Shift to move faster |
| Lock the camera | Camera Lock while control is enabled |

Camera control does not run unless **Camera Control** is on, so the basic monitor stays passive.

Shift+C is registered on the add-on keymap for the 3D View and is removed on disable. While the add-on is enabled it takes the place of Blender's Frame All shortcut. Change the key in Preferences → Add-ons → Blender-CamSight.

## Configuration

Sidebar fields:

- Enable Preview
- Camera (empty means the scene camera)
- Width, height, X, Y
- Auto Shading, and Shading when Auto Shading is off
- Camera Frame, Crosshair, Rule of Thirds, Safe Areas, Horizon Line
- Camera Information
- Camera Control and Camera Lock

**Reset Camera Preview** copies size, position, shading, and overlay defaults from add-on preferences onto the current scene.

**Auto Shading** is on by default. The preview follows the 3D Viewport header: Solid, Wireframe, Material Preview, or Rendered. Turn **Auto Shading** off to use the **Shading** menu for the preview only. Changing the header then leaves the preview on the menu choice.

The new image is captured from a timer, not from inside the viewport draw, so changing shading does not lock Blender. A manual mode is written onto the viewport for that capture and restored before the timer returns. Solid and Wireframe step out of Camera View only for that capture, then Camera View is restored.

## Development

```text
src/blender_camsight/   add-on package
addon.py                install bridge and bl_info
__init__.py             folder install entry
main.py                 unit tests and zip builder
tests/                  tests that run outside Blender
```

```text
uv sync
uv run pytest
uv run python main.py zip
```

Python 3.11 matches Blender 4.2–4.5. `uv sync` installs the package and the dev group (pytest) from `uv.lock`.

Docker runs the same tests, and a second image loads the add-on in Blender 4.5.14:

```text
docker compose run --rm test
docker compose --profile blender run --rm blender
```

## Testing

How to run the unit tests, Docker, and the in-Blender checklist is in [docs/TESTING.md](docs/TESTING.md).

Unit tests cover camera selection, snapshot extraction, preview shading, aspect fitting, overlay geometry, hit testing, redraw throttling, handler de-duplication, and register/unregister order. They do not start Blender.

Manual check after installing the zip:

1. Enable the add-on and confirm the Blender-CamSight sidebar tab appears.
2. Add a camera and a few objects. Enable the preview. Confirm the main view stays in free orbit (Numpad 0 is not pressed, the navigation gizmo still orbits).
3. Move and rotate the camera. The monitor should follow within a frame or two.
4. Change lens, sensor fit, shift, clip, and ortho scale. The framing should match Camera View (compare briefly with Numpad 0, then leave it).
5. Change render resolution and resolution percentage. The letterbox and info line should update.
6. With **Auto Shading** on, switch the 3D Viewport header through Solid, Wireframe, Material Preview, and Rendered. The preview should follow each mode, Blender should stay responsive, and the header should stay on the mode you picked.
7. Turn **Auto Shading** off. Change **Shading** in the sidebar. The preview should switch and the header should stay where it was. Change the header again and confirm the preview stays on the sidebar choice.
8. Press Numpad 0 so the viewport is in Camera View, then change shading again. Blender should stay responsive, the preview should update, and leaving Camera View should return to free orbit.
9. Drag, resize, and close the monitor. Open a second 3D Viewport and confirm both show it. Confirm the Outliner, Properties, and other editors do not.
10. Toggle Shift+C. Disable the add-on and confirm the monitor, shortcut, and handlers are gone (enable again and confirm there is only one monitor).
11. Enable Camera Control and confirm Ctrl-drag, the wheel, and WASD move only that camera, and only while the pointer is over the monitor.

This workspace did not have the `blender` executable on PATH, so the zip was not loaded inside Blender here.

## Architecture

Blender does not offer a supported way to parent a second `VIEW_3D` editor inside an existing 3D region. Calling `bpy.ops.view3d.view_camera()` would replace the user's view, so the add-on does not call it.

The monitor uses the official offscreen path:

1. `SpaceView3D.draw_handler_add(..., 'WINDOW', 'POST_PIXEL')` draws the widget in 3D Viewports. That callback blits the cached image. It does not capture the scene.
2. When the image is stale, a timer calls `GPUOffScreen.draw_view3d` with the camera matrices. A re-entry guard stops that pass from drawing the monitor into itself. The timer then tags one redraw so the new image is blitted.
3. `gpu_extras.presets.draw_texture_2d` blits the texture. Overlays use the `UNIFORM_COLOR` and `POLYLINE_UNIFORM_COLOR` builtin shaders, not legacy OpenGL.
4. `depsgraph_update_post` marks the cache dirty and tags 3D View redraws. The handler is stored once and removed on unregister. Shading and view changes made only for the capture are ignored, so restoring the viewport does not count as a scene edit.

**Auto Shading** follows the 3D Viewport header. With it off, the sidebar shading is used for the capture and then the header mode is restored. Solid and Wireframe leave Camera View only during that capture.

GPU buffers are freed on disable. Keymap items are removed from the add-on keyconfig. Classes are unregistered in reverse order.

## Blender Compatibility

Targeted at Blender 4.2 and tested against the Blender 4.5 API documentation for `gpu.types.GPUOffScreen`, `Camera.calc_matrix_camera`, and `SpaceView3D` draw handlers. Builtin shader names used here (`UNIFORM_COLOR`, `POLYLINE_UNIFORM_COLOR`, and the image preset) are the ones documented for 4.5.

## Known Limitations

- The monitor is an offscreen viewport render, not a second interactive editor. It cannot host its own gizmos or independent viewport navigation.
- Overlays and object visibility come from the 3D Viewport used for the capture. **Auto Shading** uses that viewport's shading mode. With Auto Shading off, the sidebar shading is drawn into the preview and the viewport mode is restored.
- Solid and Wireframe use Workbench. When the viewport is in Camera View, the capture temporarily uses a perspective view so those modes keep the camera frame. The main view is restored before the next viewport draw.
- The preview keeps one shared image. With Auto Shading on, two 3D Viewports that use different shading show the mode of whichever viewport was captured most recently.
- The scene capture runs outside the viewport draw so changing shading does not lock Blender. A dirty scene is still re-rendered at a capped rate, and that pass walks the viewport drawing code. It is not a full Cycles still.
- `GPUOffScreen` belongs to the OpenGL context that created it. Closing the window frees it; the next redraw creates another.
- Camera control is a later interaction layer. It is off by default and only applies while the pointer is over the monitor.
- Safe areas use the common 90% action and 80% title fractions of the camera frame.

## License

MIT. See [LICENSE.md](LICENSE.md).
