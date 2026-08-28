"""Device-type reference docs and user preferences, served on demand.

Docs live in `mcp/device-types/` (a junction to the wiki on this machine, a
plain folder once published). They are fetched per request rather than
bundled into every tool response: the index gives the type overview, a
per-type file gives full detail.

Two kinds of durable note can be written back:
  - a Larnitech/device-type finding -> the type's own wiki file (`add_note`)
  - a general working preference    -> `mcp/preferences.md` (`add_preference`)
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent.parent
DEVICE_TYPES_DIR = MCP_DIR / "device-types"
INDEX_FILE = DEVICE_TYPES_DIR / "_device_types.md"
PREFERENCES_FILE = MCP_DIR / "preferences.md"

# Reachable through the same tool as the device types: every type file links
# to `BUG-NNN` entries, so the bug registry has to be fetchable too, or those
# links dead-end for anyone without filesystem access to the wiki.
EXTRA_DOCS = {
    "bugs": MCP_DIR / "bugs.md",
    "protocol": MCP_DIR / "api2_protocol.md",
}

# Placeholder left in every per-type file's Notes section; new findings go
# directly under it, so the newest is always first.
_QUIRK_ANCHOR = "<!-- Add live-tested quirks here as found. -->"


class DocsError(Exception):
    """Missing or unwritable documentation file."""


def _type_path(device_type: str) -> Path:
    return DEVICE_TYPES_DIR / f"{device_type.strip().lower()}.md"


def available_types() -> list[str]:
    if not DEVICE_TYPES_DIR.exists():
        return []
    return sorted(p.stem for p in DEVICE_TYPES_DIR.glob("*.md") if not p.stem.startswith("_"))


def quirks(device_type: str) -> str:
    """That type's `**Issues**` block from the index, verbatim.

    Attached to every write preview so a write can't be reviewed without the
    type's known quirks in front of the reviewer.
    """
    if not INDEX_FILE.exists():
        return ""
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()
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
        path = INDEX_FILE
    elif key in EXTRA_DOCS:
        path = EXTRA_DOCS[key]
    else:
        path = _type_path(device_type)

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


def add_note(device_type: str, note: str, index_title: str | None = None) -> dict:
    """Append a finding to a type's Notes section, optionally indexing it.

    `index_title` adds a one-line quirk title under that type's Issues block
    in `_device_types.md`, keeping the index and the detail file in sync.
    """
    note = note.strip()
    if not note:
        raise DocsError("empty note")
    path = _type_path(device_type)
    if not path.exists():
        raise DocsError(f"unknown device type {device_type!r} (have: {', '.join(available_types())})")

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
            "hint": "pass index_title to also list this quirk in _device_types.md",
        }
    return out


def _add_index_quirk(device_type: str, title: str) -> dict:
    """Insert a quirk title under `### <type>` -> `**Issues**` -> `- Quirks`."""
    if not INDEX_FILE.exists():
        return {"updated": False, "reason": f"missing {INDEX_FILE}"}
    lines = INDEX_FILE.read_text(encoding="utf-8").splitlines()

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

    INDEX_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"updated": True, "written_to": str(INDEX_FILE), "entry": bullet.strip()}


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
    PREFERENCES_FILE.write_text(f"{text}\n{bullet}\n", encoding="utf-8")
    return {"written_to": str(PREFERENCES_FILE), "preference": bullet}


_PREFERENCES_HEADER = """Standing user preferences for working with Larnitech through this MCP.

Applied **on top of** the device-type wiki: where a preference and the wiki
disagree about how to read, write, or present something, the preference
wins. Facts about the equipment itself belong in the wiki
(`device-types/<type>.md`), not here — this file is for how the user wants
the work done.

Served with every `get_docs` call.

## Preferences
"""
