# Installation

Blender-CamSight installs from a zip. The git folder is named `Blender-CamSight`, and Blender cannot import a module whose name contains a hyphen.

## Download from release

1. Download `Blender-CamSight.zip` from the [latest GitHub release](https://github.com/axcel-blade/Blender-CamSight/releases/latest).
2. In Blender 4.2 or newer, choose Edit → Preferences → Add-ons → Install from Disk and select the zip.
3. Enable **Blender-CamSight**.

Open a 3D Viewport, press N, and choose **Blender-CamSight**.

## Zip from repo

From the repository root, with [uv](https://docs.astral.sh/uv/) installed:

```text
uv sync
uv run python main.py zip
```

The file is `dist/Blender-CamSight.zip`. Inside it, the add-on folder is `blender_camsight`, with a literal `bl_info` in `__init__.py` and a `blender_manifest.toml`. Blender lists it as **Blender-CamSight** under the 3D View tag. A checkout whose `bl_info` is assigned from another module never appears in the list.

1. Use Blender 4.2 or newer.
2. Edit → Preferences → Add-ons → Install from Disk.
3. Select `dist/Blender-CamSight.zip`.
4. Enable **Blender-CamSight**.

## Tests

Unit tests, the Docker images, and the in-Blender checklist are in [TESTING.md](TESTING.md).

## Uninstall

Disable **Blender-CamSight** in Preferences, then remove it. Disabling deletes the draw handler, the depsgraph handler, the Shift+C keymap item, and the offscreen GPU buffer.
