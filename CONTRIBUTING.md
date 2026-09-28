# Contributing to Blender-CamSight

Thanks for working on Blender-CamSight. The add-on keeps the main 3D Viewport free and shows a separate live camera monitor.

## Setup

Python 3.11 matches Blender 4.2 through 4.5.

```text
uv sync
uv run pytest
uv run python main.py zip
```

Docker:

```text
docker compose run --rm test
docker compose --profile blender run --rm blender
```

The Blender image registers and unregisters the add-on in Blender 4.5.14. Command details are in [docs/TESTING.md](docs/TESTING.md). That does not replace the manual viewport check in [docs/MANUAL_TESTING.md](docs/MANUAL_TESTING.md).

## Project layout

- `addon.py` and `__init__.py` are the Blender entry points. Keep them thin.
- Put implementation in `src/blender_camsight/`, split by responsibility (camera, preview, drawing, handlers, operators, UI).
- Put logic that can run without Blender in pure functions and cover it from `tests/`.
- Do not add web servers, databases, or other third-party runtime services. The add-on uses Blender's Python API.

The install zip folder must stay a valid Python module name. `Blender-CamSight` cannot be imported because of the hyphen, so the packaged module remains `blender_camsight`.

## Git Flow

| Branch | Role |
| --- | --- |
| `main` | Released add-on only |
| `develop` | Integration branch for the next version |
| `feature/*` | New work, branched from `develop` and merged back into `develop` |
| `release/*` | Stabilization for a version, branched from `develop`, then merged into `main` and `develop` |
| `hotfix/*` | Urgent fix, branched from `main`, then merged into `main` and `develop` |

Start features from `develop`:

```text
git checkout develop
git checkout -b feature/short-name
```

Open pull requests into `develop`. `main` receives merges from `release/*` and `hotfix/*` only.

## Pull requests

1. Branch from `develop` as `feature/*`, unless you are cutting a `release/*` or fixing production with a `hotfix/*`.
2. Describe the user-visible change and how you tested it.
3. Run `uv run pytest` before opening the pull request. The commands are in [docs/TESTING.md](docs/TESTING.md).
4. If you change drawing, registration, or keymap behavior, also follow [docs/MANUAL_TESTING.md](docs/MANUAL_TESTING.md).

Use the pull request template. Keep the diff limited to the change you are making.

## Code

- Prefer small functions and the existing module boundaries.
- Keep constants in `src/blender_camsight/constants.py`.
- Register and unregister handlers, keymaps, draw callbacks, and GPU buffers so a reload does not leak them.
- Do not call `bpy.ops.view3d.view_camera()`. That would replace the user's view.
- Do not call `GPUOffScreen.draw_view3d` from the `POST_PIXEL` draw handler. Capture from the timer. A capture inside the viewport draw re-enters Camera View and locks Blender.
- New shading modes must not leave the main viewport's shading or view perspective changed. Apply them for the capture and restore them before the timer returns.
