"""Order-sensitive register and unregister helpers.

Blender class objects are passed in by the add-on entry point. These helpers
stay free of ``bpy`` so tests can run them with stand-ins.
"""

from __future__ import annotations

from typing import Any, Callable, List, Sequence


def register_classes(classes: Sequence[Any], register_fn: Callable[[Any], None]) -> List[Any]:
    registered: List[Any] = []
    try:
        for cls in classes:
            register_fn(cls)
            registered.append(cls)
    except Exception:
        unregister_classes(registered, _best_effort_unregister(register_fn))
        raise
    return registered


def _best_effort_unregister(register_fn: Callable[[Any], None]) -> Callable[[Any], None]:
    """Used only when registration fails halfway and no unregister callback was given."""
    sibling = getattr(register_fn, "unregister", None)
    if callable(sibling):
        return sibling

    def _noop(_cls: Any) -> None:
        return None

    return _noop


def unregister_classes(classes: Sequence[Any], unregister_fn: Callable[[Any], None]) -> List[BaseException]:
    errors: List[BaseException] = []
    for cls in reversed(list(classes)):
        try:
            unregister_fn(cls)
        except BaseException as exc:  # noqa: BLE001 - one failure must not skip the rest
            errors.append(exc)
    return errors


def add_unique(collection: List[Any], item: Any) -> bool:
    """Append ``item`` once. Returns True when it was newly added."""
    if item in collection:
        return False
    collection.append(item)
    return True


def remove_all(collection: List[Any], item: Any) -> int:
    """Remove every occurrence of ``item``. Returns how many were removed."""
    removed = 0
    while item in collection:
        collection.remove(item)
        removed += 1
    return removed
