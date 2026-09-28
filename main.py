"""Development helper: run unit tests or build an installable add-on zip.

Usage:
    uv run python main.py test
    uv run python main.py zip
"""

from __future__ import annotations

import argparse
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = "blender_camsight"
ZIP_NAME = "Blender-CamSight.zip"

INCLUDE = (
    "__init__.py",
    "addon.py",
    "blender_manifest.toml",
    "LICENSE.md",
    "README.md",
    "src/__init__.py",
    "src/blender_camsight",
)


def build_zip(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in INCLUDE:
            path = ROOT / relative
            if path.is_dir():
                for file in path.rglob("*.py"):
                    archive.write(file, f"{PACKAGE_DIR}/{file.relative_to(ROOT).as_posix()}")
            elif path.is_file():
                archive.write(path, f"{PACKAGE_DIR}/{relative}")
    return destination


def run_tests() -> int:
    return subprocess.call(["uv", "run", "pytest", "-q"], cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Blender-CamSight tools")
    parser.add_argument("command", choices=("test", "zip"))
    args = parser.parse_args()
    if args.command == "test":
        return run_tests()
    zip_path = build_zip(ROOT / "dist" / ZIP_NAME)
    print(zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
