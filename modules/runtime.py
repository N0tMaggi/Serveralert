from __future__ import annotations

import socket
import time
from dataclasses import dataclass, field

import requests

from modules import config


def _resolve_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "unknown"


@dataclass
class Runtime:
    config: dict
    session: requests.Session = field(default_factory=requests.Session)
    started_at: float = field(default_factory=time.time)
    hostname: str = field(default_factory=socket.gethostname)
    ip_address: str = field(default_factory=_resolve_ip)


_RUNTIME: Runtime | None = None


def build_runtime(config_data: dict | None = None) -> Runtime:
    config_data = config_data or config.load_config()
    return Runtime(config=config_data)


def get_runtime() -> Runtime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = build_runtime()
    return _RUNTIME


def set_runtime(runtime: Runtime) -> None:
    global _RUNTIME
    _RUNTIME = runtime
