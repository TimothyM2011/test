"""
core/config.py

Loads config.json next to the project root, applies sane defaults for
anything missing, and exposes the values as attributes.
"""
import json
import os
from dataclasses import dataclass, field

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_ROOT, "config.json")

DEFAULTS = {
    "sidebar_width": 300,
    "expanded_width": 600,
    "anim_ms": 180,
    "edge_trigger_px": 3,
    "leave_grace_ms": 350,
    "reopen_cooldown_ms": 450,
    "poll_ms": 100,
    "theme": "dark",
    "debug_edge": False,
    "state_dir": "state",
    "modules": ["hardware"],
    "apps": [],
}

@dataclass
class Config:
    sidebar_width: int = DEFAULTS["sidebar_width"]
    expanded_width: int = DEFAULTS["expanded_width"]
    anim_ms: int = DEFAULTS["anim_ms"]
    edge_trigger_px: int = DEFAULTS["edge_trigger_px"]
    leave_grace_ms: int = DEFAULTS["leave_grace_ms"]
    reopen_cooldown_ms: int = DEFAULTS["reopen_cooldown_ms"]
    poll_ms: int = DEFAULTS["poll_ms"]
    theme: str = DEFAULTS["theme"]
    debug_edge: bool = DEFAULTS["debug_edge"]
    state_dir: str = DEFAULTS["state_dir"]
    modules: list = field(default_factory=lambda: list(DEFAULTS["modules"]))
    apps: list = field(default_factory=list)

    @property
    def project_root(self) -> str:
        return _ROOT

    @property
    def state_path(self) -> str:
        return os.path.join(_ROOT, self.state_dir)

    @classmethod
    def load(cls) -> "Config":
        data = dict(DEFAULTS)
        if os.path.exists(_CONFIG_PATH):
            try:
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data.update(json.load(f))
            except Exception as e:
                print(f"[config] failed to read {_CONFIG_PATH}: {e}")

        return cls(
            sidebar_width=int(data["sidebar_width"]),
            expanded_width=int(data["expanded_width"]),
            anim_ms=int(data["anim_ms"]),
            edge_trigger_px=int(data["edge_trigger_px"]),
            leave_grace_ms=int(data["leave_grace_ms"]),
            reopen_cooldown_ms=int(data["reopen_cooldown_ms"]),
            poll_ms=int(data["poll_ms"]),
            theme=data["theme"],
            debug_edge=bool(data.get("debug_edge", False)),
            state_dir=str(data.get("state_dir", "state")),
            modules=list(data.get("modules", [])),
            apps=list(data.get("apps", [])),
        )

    def save(self) -> None:
        payload = {
            "sidebar_width": self.sidebar_width,
            "expanded_width": self.expanded_width,
            "anim_ms": self.anim_ms,
            "edge_trigger_px": self.edge_trigger_px,
            "leave_grace_ms": self.leave_grace_ms,
            "reopen_cooldown_ms": self.reopen_cooldown_ms,
            "poll_ms": self.poll_ms,
            "theme": self.theme,
            "debug_edge": self.debug_edge,
            "state_dir": self.state_dir,
            "modules": self.modules,
            "apps": self.apps,
        }
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
