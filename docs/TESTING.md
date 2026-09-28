# Testing

Run these commands from the repository root. Python 3.11 matches Blender 4.2 through 4.5. [uv](https://docs.astral.sh/uv/) installs pytest from the `dev` group in `uv.lock`.

## Unit tests

```text
uv sync
uv run pytest
```

The same suite can be started through the project helper:

```text
uv run python main.py test
```

`uv run pytest` and `uv run python main.py test` both run the tests in `tests/`. Those tests cover camera selection, snapshot extraction, preview shading, aspect fitting, overlay geometry, hit testing, redraw throttling, and register/unregister order. They do not start Blender.

A quiet run:

```text
uv run pytest -q
```

One file:

```text
uv run pytest tests/test_camera.py
```

## Docker

The Docker daemon must be running.

Unit tests in the `test` image:

```text
docker compose run --rm test
```

Headless Blender 4.5.14 register and unregister check:

```text
docker compose --profile blender run --rm blender
```

That Blender container only checks that the add-on registers and then unregisters. It does not draw the camera monitor.

## Manual test in Blender

After `uv run python main.py zip`, install `dist/Blender-CamSight.zip` and follow [MANUAL_TESTING.md](MANUAL_TESTING.md).
