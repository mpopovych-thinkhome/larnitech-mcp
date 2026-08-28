"""Device-type reference docs and user preferences, served on demand.

Fetched per request rather than bundled into every tool response: the index
gives the type overview, a per-type file gives full detail.

Two kinds of durable note can be written back:
  - a Larnitech/device-type finding -> that type's own doc (`add_note`)
  - a general working preference    -> `preferences.md` (`add_preference`)

Where those writes land depends on how the server is installed. From a
checkout they edit the docs in place, which is the point on a maintainer's
machine. From an installed wheel the docs live in `site-packages` — shared,
possibly not writable, and replaced on upgrade — so the first edit copies
that file into a per-user overlay and edits the copy. The overlay then wins
on read, so a user's own findings survive upgrades while everyone still
starts from the shipped set. See `paths`.
"""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from . import paths

DOCS_ROOT = paths.docs_root()
DEVICE_TYPES_DIR = DOCS_ROOT / "device-types"
PREFERENCES_FILE = paths.user_file("preferences.md")

# Reachable through the same tool as the device types: every type file links
# to `BUG-NNN` entries, so the bug registry has to be fetchable too, or those
# links dead-end for anyone without the docs on disk.
EXTRA_DOCS = {
    "bugs": "bugs.md",
    "protocol": "api2_protocol.md",
}

_INDEX_REL = "device-types/_device_types.md"

# Placeholder left in every per-type file's Notes section; new findings go
# directly under it, so the newest is always first.
_QUIRK_ANCHOR = "<!-- Add live-tested quirks here as found. -->"


class DocsError(Exception):
    """Missing or unwritable documentation file."""


# --- resolution ----------------------------------------------------------


def _resolve(relative: str) -> Path:
    """The user's edited copy if there is one, else the served copy."""
    overlay = paths.docs_overlay() / relative
    return overlay if overlay.exists() else DOCS_ROOT / relative


def _writable(relative: str) -> Path:
    """A path that can be edited, copying into the overlay if it must."""
    if paths.docs_are_writable():
        return DOCS_ROOT / relative
    target = paths.docs_overlay() / relative
    if not target.exists():
        source = DOCS_ROOT / relative
        if not source.exists():
            raise DocsError(f"missing {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return target


def _type_rel(device_type: str) -> str:
    return f"device-types/{device_type.strip().lower()}.md"


def available_types() -> list[str]:
    found: set[str] = set()
    for directory in (DEVICE_TYPES_DIR, paths.docs_overlay() / "device-types"):
        if directory.is_dir():
            found |= {p.stem for p in directory.glob("*.md") if not p.stem.startswith("_")}
    return sorted(found)


# --- reading -------------------------------------------------------------


def quirks(device_type: str) -> str:
    """That type's `**Issues**` block from the index, verbatim.

    Attached to every write preview so a write can't be reviewed without the
    type's known quirks in front of the reviewer.
    """
    index = _resolve(_INDEX_REL)
    if not index.exists():
        return ""
    lines = index.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(f"### {device_type.strip().lower()}")
    except ValueError:
        return ""
    out: list[str] = []
    collecting = False
    for line in lines[start + 1:]:
        if line.startswith("### "):
            break
        if line.strip() == "**Issues**":
            collecting = True
            continue
        if collecting:
            if line.startswith("**") or line.strip() == "---":
                break
            if line.strip():
                out.append(line)
    return "\n".join(out).strip()


def read_preferences() -> str:
    if not PREFERENCES_FILE.exists():
        return ""
    return PREFERENCES_FILE.read_text(encoding="utf-8").strip()


def get(device_type: str | None = None) -> dict:
    """Index (no argument), one type's file, or `bugs`/`protocol`.

    Always carries user preferences alongside.
    """
    key = (device_type or "").strip().lower()
    if device_type is None:
        relative = _INDEX_REL
    elif key in EXTRA_DOCS:
        relative = EXTRA_DOCS[key]
    else:
        relative = _type_rel(device_type)
    path = _resolve(relative)

    result: dict = {
        "device_type": device_type or "index",
        "source": str(path),
        "user_preferences": read_preferences(),
    }
    if not path.exists():
        result["found"] = False
        result["available_types"] = available_types()
        result["also_available"] = sorted(EXTRA_DOCS)
        return result
    result["found"] = True
    result["content"] = path.read_text(encoding="utf-8")
    return result


# --- writing -------------------------------------------------------------


def add_note(device_type: str, note: str, index_title: str | None = None) -> dict:
    """Append a finding to a type's Notes section, optionally indexing it.

    `index_title` adds a one-line quirk title under that type's Issues block
    in the index, keeping the index and the detail file in sync.
    """
    note = note.strip()
    if not note:
        raise DocsError("empty note")
    relative = _type_rel(device_type)
    if not (DOCS_ROOT / relative).exists() and not (paths.docs_overlay() / relative).exists():
        raise DocsError(
            f"unknown device type {device_type!r} (have: {', '.join(available_types())})"
        )
    path = _writable(relative)

    bullet = f"- ({date.today().isoformat()}) {note}"
    text = path.read_text(encoding="utf-8")
    if _QUIRK_ANCHOR in text:
        text = text.replace(_QUIRK_ANCHOR, f"{_QUIRK_ANCHOR}\n\n{bullet}", 1)
    elif "\n## Notes\n" in text:
        text = text.replace("\n## Notes\n", f"\n## Notes\n\n{bullet}\n", 1)
    else:
        text = text.rstrip() + f"\n\n## Notes\n\n{bullet}\n"
    path.write_text(text, encoding="utf-8")

    out = {"device_type": device_type.strip().lower(), "written_to": str(path), "note": bullet}
    if index_title:
        out["index"] = _add_index_quirk(device_type.strip().lower(), index_title.strip())
    else:
        out["index"] = {
            "updated": False,
            "hint": "pass index_title to also list this quirk in the index",
        }
    return out


def _add_index_quirk(device_type: str, title: str) -> dict:
    """Insert a quirk title under `### <type>` -> `**Issues**` -> `- Quirks`."""
    try:
        index = _writable(_INDEX_REL)
    except DocsError as err:
        return {"updated": False, "reason": str(err)}
    lines = index.read_text(encoding="utf-8").splitlines()

    try:
        start = lines.index(f"### {device_type}")
    except ValueError:
        return {"updated": False, "reason": f"no '### {device_type}' section in the index"}
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("### "):
            end = i
            break

    quirks_at = issues_at = None
    for i in range(start, end):
        if lines[i].startswith("- Quirks"):
            quirks_at = i
        elif lines[i].strip() == "**Issues**":
            issues_at = i
    bullet = f"  - {title}"

    if quirks_at is not None:
        lines.insert(quirks_at + 1, bullet)
    elif issues_at is not None:
        # A section with no bugs/quirks yet carries a "- none recorded"
        # placeholder right under **Issues** — drop it, it's no longer true.
        for i in range(issues_at + 1, end):
            if lines[i].strip() == "- none recorded":
                del lines[i]
                break
        lines.insert(issues_at + 1, f"- Quirks — details in [{device_type}.md]({device_type}.md)")
        lines.insert(issues_at + 2, bullet)
    else:
        stop = end
        while stop > start and not lines[stop - 1].strip():
            stop -= 1
        if stop > start and lines[stop - 1].strip() == "---":
            stop -= 1
        lines.insert(stop, "")
        lines.insert(stop + 1, "**Issues**")
        lines.insert(stop + 2, f"- Quirks — details in [{device_type}.md]({device_type}.md)")
        lines.insert(stop + 3, bullet)

    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"updated": True, "written_to": str(index), "entry": bullet.strip()}


def add_preference(note: str) -> dict:
    """Append a general working preference (not Larnitech/device-type specific)."""
    note = note.strip()
    if not note:
        raise DocsError("empty preference")
    bullet = f"- ({date.today().isoformat()}) {note}"
    if PREFERENCES_FILE.exists():
        text = PREFERENCES_FILE.read_text(encoding="utf-8").rstrip()
    else:
        text = _PREFERENCES_HEADER.rstrip()
    PREFERENCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCES_FILE.write_text(f"{text}\n{bullet}\n", encoding="utf-8")
    return {"written_to": str(PREFERENCES_FILE), "preference": bullet}


_PREFERENCES_HEADER = """Standing user preferences for working with Larnitech through this MCP.

Applied **on top of** the device-type docs: where a preference and the docs
disagree about how to read, write, or present something, the preference
wins. Facts about the equipment itself belong in the docs
(`device-types/<type>.md`), not here — this file is for how the user wants
the work done.

Served with every `get_docs` call.

## Preferences
"""
