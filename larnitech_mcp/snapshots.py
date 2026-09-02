"""Saved slices of controller data, kept on disk per object.

A conversation is a bad place to keep a device snapshot: it scrolls away,
and the next session can't diff against it. So when something is worth
keeping — a full `get-devices` dump before a change, the statuses of one
area, a watch trace — it goes to a file instead:

    data/<object>/2026-08-28_15-42-07_before-fancoil-swap.txt

One folder per object, timestamped filenames, newest sorts last.

Every snapshot is a JSON envelope, whatever was passed in:

    {"object": ..., "saved_at": ..., "comment": ..., "data": <payload>}

Two reasons it is an envelope rather than the bare payload. Provenance
travels with the file, so a copied or moved snapshot still says what it is
— the folder and filename are no longer the only record. And the format is
fixed, so reading one back needs no sniffing: `read` hands back parsed
structure instead of a string for the caller to guess at and parse.

JSON costs roughly 2-3x the bytes of a CSV table of the same rows. That is
paid deliberately: it round-trips types, so `1025` comes back a number and
`null` stays null rather than becoming the string "null" — and telling
"no data" apart from zero is something this codebase cares about.

Files written before the envelope existed, or by hand, still read back —
`read` returns their raw text and says the format is not an envelope.

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
ENVELOPE_KEYS = {"object", "saved_at", "comment", "data"}

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


def save(object_name: str, content, comment: str) -> dict:
    """Write a snapshot for one object as a JSON envelope."""
    if content is None or (isinstance(content, str) and not content.strip()):
        raise SnapshotError("nothing to save — content is empty")

    now = datetime.now()
    envelope = {
        "object": object_name,
        "saved_at": now.isoformat(timespec="seconds"),
        "comment": comment.strip(),
        "data": content,
    }
    # default=str so an unexpected type (a datetime, a Path) degrades to its
    # string form rather than losing the whole snapshot to a TypeError.
    body = json.dumps(envelope, indent=2, ensure_ascii=False, default=str)

    name = f"{now.strftime(STAMP_FORMAT)}_{slug(comment)}.txt"
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
        objects[directory.name] = {"count": len(files), "newest": files[-1].name}
        total += len(files)
    return {"root": str(root), "objects": objects, "total": total}


def read(object_name: str, file: str) -> dict:
    """Read one saved snapshot back, parsed when it is an envelope."""
    directory = object_dir(object_name)
    # Path(file).name drops any directory part; re-checking the resolved
    # parent makes traversal impossible either way.
    target = (directory / Path(file).name).resolve()
    if not target.is_file() or target.parent != directory.resolve():
        if directory.is_dir():
            available = [p.name for p in sorted(directory.glob("*.txt"))]
            raise SnapshotError(f"no snapshot {file!r} for {object_name!r} (have: {available})")
        # The folder is derived from the object name, so a folder created
        # under a different naming convention won't be found this way. Name
        # the folders that do exist — they can be passed here directly.
        root = paths.data_dir()
        folders = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
        raise SnapshotError(
            f"nothing saved for {object_name!r} (looked in {directory.name!r}). "
            f"Folders that exist: {folders} — pass one of those as `object_name` "
            f"if the snapshot was filed under a different name."
        )

    text = target.read_text(encoding="utf-8")
    result = {"object": object_name, "file": target.name, "path": str(target)}

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        result["format"] = "raw"
        result["note"] = "not a JSON envelope — saved by hand or before the format was fixed"
        result["content"] = text
        return result

    if isinstance(parsed, dict) and ENVELOPE_KEYS <= set(parsed):
        result["format"] = "envelope"
        result["saved_at"] = parsed["saved_at"]
        result["comment"] = parsed["comment"]
        result["saved_for"] = parsed["object"]
        result["data"] = parsed["data"]
        return result

    result["format"] = "json"
    result["note"] = "valid JSON but not an envelope — no provenance recorded in the file"
    result["data"] = parsed
    return result
