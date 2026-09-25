"""
core/registry.py

Central module registry. The Sidebar builds modules purely by looking
ids up here - it never hardcodes a module class.

To add a new module later:
  1. Write modules/<your_module>/<file>.py with a class that
     subclasses core.module.Module, and call
     register_module("your_id", YourModuleClass) at the bottom of
     that file.
  2. Add one import line for that file to modules/__init__.py (this
     is what makes the register_module(...) call actually run).
  3. Add "your_id" to the "modules" list in config.json.

That's it - core/window.py needs no changes for a new module.
"""

_REGISTRY = {}


def register_module(module_id, module_cls):
    """Register a Module subclass under an id used in config.json."""
    _REGISTRY[module_id] = module_cls
    return module_cls


def get_module_class(module_id):
    return _REGISTRY.get(module_id)


def known_module_ids():
    return list(_REGISTRY.keys())
