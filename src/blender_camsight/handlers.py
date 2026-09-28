"""Depsgraph and draw-handler lifecycle.

The depsgraph callback only marks the preview dirty and tags 3D Views.
It does not render. The draw callback blits a cached image unless that flag
is set, so orbiting the main viewport does not re-render the scene.
"""

from __future__ import annotations

from typing import List

import bpy

from .drawing import draw_callback, free_offscreen, runtime
from .registration import add_unique, remove_all
from .viewport import tag_view3d_redraws

_depsgraph_handlers: List[object] = []


def _on_depsgraph_update(scene, depsgraph) -> None:
    del depsgraph
    settings = getattr(scene, "camera_preview", None)
    if settings is None or not settings.preview_enabled:
        return
    runtime().mark_dirty()
    try:
        tag_view3d_redraws(bpy.context.window_manager)
    except Exception:
        return


def register_handlers() -> None:
    if add_unique(_depsgraph_handlers, _on_depsgraph_update):
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)
    state = runtime()
    if state.draw_handler is None:
        state.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback, (), "WINDOW", "POST_PIXEL"
        )


def unregister_handlers() -> None:
    remove_all(_depsgraph_handlers, _on_depsgraph_update)
    handlers = bpy.app.handlers.depsgraph_update_post
    while _on_depsgraph_update in handlers:
        handlers.remove(_on_depsgraph_update)
    state = runtime()
    if state.draw_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(state.draw_handler, "WINDOW")
        except Exception:
            pass
        state.draw_handler = None
    free_offscreen()


def handler_installed() -> bool:
    return _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post


def draw_handler_installed() -> bool:
    return runtime().draw_handler is not None
