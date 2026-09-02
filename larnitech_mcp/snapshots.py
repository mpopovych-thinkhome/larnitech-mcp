"""Saved slices of controller data, kept on disk per object.

A conversation is a bad place to keep a device snapshot: it scrolls away,
and the next session can't diff against it. So when something is worth
keeping — a full `get-devices` dump before a change, the statuses of one
area, a watch trace — it goes to a file instead:

    data/<object>/2026-08-28_15-42-07_before-fancoil-swap.txt

One folder per object, timestamped filenames, newest sorts last. Contents
are written exactly as given (objects serialised as JSON), with no injected
header, so a saved file can be read back and parsed.

Lives beside the package in a checkout, in `~/.larnitech-mcp/data/` once
installed — same rule as keys and preferences. See `paths`.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from . import paths

STAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"

# Windows forbids <>:"/\|?* in names, and trailing dots or spaces. Collapsing
# runs of separators keeps "test stand" readable as
# "Imerel-Office-stand" rather than littered with placeholders.
_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RUNS = re.compile(r"[-\s_]+")


class SnapshotError(Exception):
    """Bad snapshot name, or nothing to save."""


def slug(text: str) -> str:
    cleaned = _RUNS.sub("-", _ILLEGAL.sub("-", (text or "").strip())).strip("-. ")
    if not cleaned:
        raise SnapshotError("name is empty once stripped of illegal characters")
    return cleaned


def object_dir(object_name: str) -> Path:
    return paths.data_dir() / slug(object_name)


def _serialise(content) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, indent=2, ensure_ascii=False, default=str)


def save(object_name: str, content, comment: str) -> dict:
    """Write a snapshot for one object. Returns where it landed."""
    if content is None or (isinstance(content, str) and not content.strip()):
        raise SnapshotError("nothing to save — content is empty")

    body = _serialise(content)
    stamp = datetime.now().strftime(STAMP_FORMAT)
    name = f"{stamp}_{slug(comment)}.txt"
    target = object_dir(object_name) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return {
        "saved": True,
        "object": object_name,
        "file": name,
        "path": str(target),
        "bytes": len(body.encode("utf-8")),
    }


def _describe(path: Path) -> dict:
    stat = path.stat()
    return {
        "file": path.name,
        "bytes": stat.st_size,
        "saved_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def listing(object_name: str | None = None) -> dict:
    """Snapshots for one object, or a per-object count across all of them."""
    root = paths.data_dir()
    if not root.is_dir():
        return {"root": str(root), "objects": {}, "total": 0}

    if object_name:
        directory = object_dir(object_name)
        files = sorted(directory.glob("*.txt")) if directory.is_dir() else []
        return {
            "root": str(root),
            "object": object_name,
            "snapshots": [_describe(p) for p in files],
            "total": len(files),
        }

    objects = {}
    total = 0
    for directory in sorted(p for p in root.iterdir() if p.is_dir()):
        files = sorted(directory.glob("*.txt"))
        if not files:
            continue
        objects[directory.name] = {
            "count": len(files),
            "newest": files[-1].name,
        }
        total += len(files)
    return {"root": str(root), "objects": objects, "total": total}


def read(object_name: str, file: str) -> dict:
    """Read one saved snapshot back."""
    directory = object_dir(object_name)
    target = (directory / Path(file).name).resolve()
    # Path(file).name already drops any directory part; resolving and
    # re-checking the parent makes traversal impossible either way.
    if not target.is_file() or target.parent != directory.resolve():
        available = [p.name for p in sorted(directory.glob("*.txt"))] if directory.is_dir() else []
        raise SnapshotError(f"no snapshot {file!r} for {object_name!r} (have: {available})")
    return {
        "object": object_name,
        "file": target.name,
        "path": str(target),
        "content": target.read_text(encoding="utf-8"),
    }
