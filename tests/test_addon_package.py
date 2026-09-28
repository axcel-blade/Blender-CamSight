"""The install package must be something Blender's add-on scanner can list."""

import ast
import importlib.util
import sys
import types
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import addon  # noqa: E402
from main import PACKAGE_DIR, build_zip  # noqa: E402

EXTENSION_NAME = "bl_ext.user_default.blender_camsight"


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
        assert f"{PACKAGE_DIR}/src/__init__.py" in names
        assert f"{PACKAGE_DIR}/blender_manifest.toml" in names
        init_text = archive.read(f"{PACKAGE_DIR}/__init__.py").decode("utf-8")
        addon_text = archive.read(f"{PACKAGE_DIR}/addon.py").decode("utf-8")
        manifest = archive.read(f"{PACKAGE_DIR}/blender_manifest.toml").decode("utf-8")

    info = ast.literal_eval(
        next(
            node.value
            for node in ast.parse(init_text).body
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "bl_info"
        )
    )
    assert info["name"] == "Blender-CamSight"
    assert not _imports_sys(addon_text)
    assert "from .src import blender_camsight" in addon_text
    assert 'id = "blender_camsight"' in manifest
    assert 'name = "Blender-CamSight"' in manifest
    assert 'tags = ["3D View"]' in manifest
    assert 'type = "add-on"' in manifest


def _imports_sys(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "sys" for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "sys":
            return True
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
            and node.attr == "path"
        ):
            return True
    return False


def _ensure_parent_packages(name: str) -> list[str]:
    """Blender already provides ``bl_ext`` and the repository package."""
    created = []
    parts = name.split(".")
    for index in range(1, len(parts)):
        parent = ".".join(parts[:index])
        if parent in sys.modules:
            continue
        module = types.ModuleType(parent)
        module.__path__ = []
        module.__package__ = parent
        sys.modules[parent] = module
        created.append(parent)
    return created


def _load_extension_package():
    """Load this repo the way Blender loads an installed extension."""
    spec = importlib.util.spec_from_file_location(
        EXTENSION_NAME,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    if spec is None or spec.loader is None:
        raise AssertionError("could not load the extension package")
    module = importlib.util.module_from_spec(spec)
    sys.modules[EXTENSION_NAME] = module
    spec.loader.exec_module(module)
    return module


def test_extension_import_stays_inside_its_package():
    path_before = list(sys.path)
    modules_before = set(sys.modules)
    parents = _ensure_parent_packages(EXTENSION_NAME)
    try:
        module = _load_extension_package()
        package = module.addon._implementation()
        assert package.__name__ == f"{EXTENSION_NAME}.src.blender_camsight"
        assert sys.path == path_before
        for name in set(sys.modules) - modules_before:
            if name in parents:
                continue
            assert name == EXTENSION_NAME or name.startswith(EXTENSION_NAME + "."), name
            module_file = getattr(sys.modules[name], "__file__", None)
            if module_file:
                assert Path(module_file).resolve().is_relative_to(ROOT.resolve())
    finally:
        removable = [
            name
            for name in sys.modules
            if name == EXTENSION_NAME or name.startswith(EXTENSION_NAME + ".") or name in parents
        ]
        for name in sorted(removable, key=len, reverse=True):
            sys.modules.pop(name, None)
