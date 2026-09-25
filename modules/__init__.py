"""
modules/__init__.py

Importing this package registers every built-in module with
core.registry (each module file calls register_module(...) at its
own bottom). Add one import line here per new module file - that is
the only change core/window.py ever needs when a module is added.
"""
from modules.hardware import module as _hardware_module  # noqa: F401
from modules.notes import notes as _notes_module  # noqa: F401
from modules.tasks import tasks as _tasks_module  # noqa: F401
from modules.timers import clock as _clock_module  # noqa: F401
from modules.clipboard import clipboard as _clipboard_module  # noqa: F401
from modules.calculator import calculator as _calculator_module  # noqa: F401
