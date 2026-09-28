"""Marks ``src`` as a package so the extension can import it relatively.

Blender extensions must keep bundled modules inside their own package. A
relative import of ``src.blender_camsight`` does that. Adding ``src`` to
``sys.path`` and importing ``blender_camsight`` as a top-level module is
reported as a policy violation.
"""
