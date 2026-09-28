"""The install package must be something Blender's add-on scanner can list."""

import ast
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import addon  # noqa: E402
from main import PACKAGE_DIR, build_zip  # noqa: E402


def _literal_bl_info(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        if getattr(node.targets[0], "id", None) != "bl_info":
            continue
        return ast.literal_eval(node.value)
    raise AssertionError(f"{path} has no literal bl_info dict")


def test_init_bl_info_is_a_literal_blender_can_scan():
    info = _literal_bl_info(ROOT / "__init__.py")
    assert info == addon.bl_info
    assert info["name"] == "Blender-CamSight"
    assert info["blender"][0] >= 4


def test_zip_contains_manifest_and_literal_bl_info(tmp_path: Path):
    archive_path = build_zip(tmp_path / "Blender-CamSight.zip")
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert f"{PACKAGE_DIR}/__init__.py" in names
        assert f"{PACKAGE_DIR}/blender_manifest.toml" in names
        init_text = archive.read(f"{PACKAGE_DIR}/__init__.py").decode("utf-8")
        manifest = archive.read(f"{PACKAGE_DIR}/blender_manifest.toml").decode("utf-8")

    info = ast.literal_eval(
        next(
            node.value
            for node in ast.parse(init_text).body
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "bl_info"
        )
    )
    assert info["name"] == "Blender-CamSight"
    assert 'id = "blender_camsight"' in manifest
    assert 'name = "Blender-CamSight"' in manifest
    assert 'tags = ["3D View"]' in manifest
    assert 'type = "add-on"' in manifest
