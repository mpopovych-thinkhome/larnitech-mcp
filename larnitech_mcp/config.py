"""Object registry and API-key storage.

Everything — connection fields and the API key — lives in one JSON file
inside this project: `mcp/project_keys.json`. Top-level keys are the exact
object name used in every tool call — no slug, no separate ID.

This file holds live credentials — never commit it (see `mcp/.gitignore`).
"""
from __future__ import annotations

import json

from . import paths

# Beside the package in a checkout; in the user's own directory once
# installed, where a pip upgrade cannot wipe it. See `paths`.
CONFIG_PATH = paths.user_file("project_keys.json")

DEFAULT_LOCAL_PORT = 2041
MODES = ("cloud", "local")
_PLACEHOLDER_KEYS = {"", "replace_me", "your-api-key-here", "changeme"}


class ConfigError(Exception):
    """Bad or missing object configuration."""


def config_path() -> Path:
    return CONFIG_PATH


def backend_name() -> str:
    return f"file ({CONFIG_PATH})"


def _read() -> dict[str, dict]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise ConfigError(f"cannot read {CONFIG_PATH}: {err}") from err


def _write(objects: dict[str, dict]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(objects, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _public(rec: dict) -> dict:
    """Connection fields only — never the key."""
    return {
        "mode": rec.get("mode"),
        "serial": rec.get("serial"),
        "host": rec.get("host"),
        "port": rec.get("port") or DEFAULT_LOCAL_PORT,
        "allow_write": bool(rec.get("allow_write")),
    }


# --- object registry -----------------------------------------------------


def load_objects() -> dict[str, dict]:
    return {name: _public(rec) for name, rec in _read().items()}


def get_object(name: str) -> dict:
    objects = _read()
    if name not in objects:
        known = ", ".join(objects) or "none"
        raise ConfigError(f"unknown object {name!r} (configured: {known})")
    return _public(objects[name])


def add_object(
    name: str,
    mode: str,
    serial: str | None = None,
    host: str | None = None,
    port: int = DEFAULT_LOCAL_PORT,
) -> dict:
    """Create or update an object's connection fields. Never touches `key` on update."""
    if mode not in MODES:
        raise ConfigError(f"mode must be one of {MODES}, got {mode!r}")
    if mode == "cloud" and not serial:
        raise ConfigError("cloud mode needs `serial`")
    if mode == "local" and not host:
        raise ConfigError("local mode needs `host`")

    objects = _read()
    rec = objects.get(name, {"key": "REPLACE_ME", "allow_write": False})
    rec["mode"] = mode
    rec["serial"] = serial if mode == "cloud" else None
    rec["host"] = host if mode == "local" else None
    rec["port"] = port if mode == "local" else None
    objects[name] = rec
    _write(objects)
    return _public(rec)


def remove_object(name: str) -> None:
    objects = _read()
    objects.pop(name, None)
    _write(objects)


# --- key storage ---------------------------------------------------------


def set_key(name: str, key: str) -> None:
    if not key or not key.strip():
        raise ConfigError("empty key")
    objects = _read()
    if name not in objects:
        raise ConfigError(f"unknown object {name!r}")
    objects[name]["key"] = key.strip()
    _write(objects)


def get_key(name: str) -> str:
    rec = _read().get(name)
    key = rec.get("key") if rec else None
    if not key or key.strip().lower() in _PLACEHOLDER_KEYS:
        raise ConfigError(
            f"no API key for {name!r} yet. Edit {CONFIG_PATH} and set its "
            f'"key" field, or run: python -m larnitech_mcp auth "{name}"'
        )
    return key.strip()


def has_key(name: str) -> bool:
    try:
        get_key(name)
    except ConfigError:
        return False
    return True


def mask(text: str, name: str | None = None) -> str:
    """Strip any stored key out of text before it reaches a caller."""
    names = [name] if name else list(_read())
    for obj_name in names:
        try:
            key = get_key(obj_name)
        except ConfigError:
            continue
        if key and key in text:
            text = text.replace(key, "***")
    return text


# --- write permission ----------------------------------------------------


def set_allow_write(name: str, allowed: bool) -> dict:
    """Toggle writes for an object. CLI-only on purpose — see `mcp/README.md`."""
    objects = _read()
    if name not in objects:
        raise ConfigError(f"unknown object {name!r}")
    objects[name]["allow_write"] = bool(allowed)
    _write(objects)
    return _public(objects[name])
