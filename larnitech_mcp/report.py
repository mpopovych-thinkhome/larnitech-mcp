"""Turn a user's bug report into a ready-to-file GitHub issue.

Deliberately does **not** post anything. Filing an issue publishes text on
the internet under someone's name, so this composes the report and hands
back a prefilled "new issue" link: the user opens it, reads exactly what
would be published, and submits it themselves. No token is needed, by
anyone, and nothing leaves the machine until a human clicks.

Reports are redacted first — a bug report naturally quotes device output,
and that output carries serial numbers, hostnames and site names that
identify someone's home.
"""
from __future__ import annotations

import json
import platform
import sys
from urllib.parse import quote

from . import config

REPO = "mpopovych-thinkhome/larnitech-mcp"
ISSUE_URL = f"https://github.com/{REPO}/issues/new"

# GitHub rejects very long URLs; keep the prefilled body well inside that.
_MAX_BODY = 6000


def version() -> str:
    try:
        from importlib.metadata import version as _v

        return _v("larnitech-mcp")
    except Exception:  # noqa: BLE001 - never let diagnostics break a report
        return "unknown"


def redactions() -> list[tuple[str, str]]:
    """Identifiers from the local config that must not reach a public issue."""
    out: list[tuple[str, str]] = []
    try:
        objects = config.load_objects()
    except config.ConfigError:
        return out
    for i, (name, obj) in enumerate(objects.items(), 1):
        if name:
            out.append((name, f"<object-{i}>"))
        if obj.get("serial"):
            out.append((obj["serial"], f"<serial-{i}>"))
        if obj.get("host"):
            out.append((obj["host"], f"<host-{i}>"))
    # Longest first, so a serial inside a longer string goes as one piece.
    return sorted(out, key=lambda pair: len(pair[0]), reverse=True)


def redact(text: str) -> tuple[str, list[str]]:
    """Strip API keys and site identifiers. Returns (clean text, what went)."""
    if not text:
        return text, []
    removed = []
    text = config.mask(text)  # API keys first — never negotiable
    if "***" in text:
        removed.append("API key")
    for needle, replacement in redactions():
        if needle and needle in text:
            text = text.replace(needle, replacement)
            removed.append(f"{needle!r} -> {replacement}")
    return text, removed


def build(
    title: str,
    what_happened: str,
    expected: str | None = None,
    device_type: str | None = None,
    status_sample: dict | None = None,
) -> dict:
    """Compose a redacted issue body and the prefilled link to file it."""
    title = (title or "").strip()
    what_happened = (what_happened or "").strip()
    if not title:
        return {"ok": False, "error": "a short title is required"}
    if not what_happened:
        return {"ok": False, "error": "describe what happened — a report without it isn't actionable"}

    parts = ["## What happened", what_happened]
    if expected:
        parts += ["", "## Expected", expected.strip()]
    if device_type:
        parts += ["", "## Device type", f"`{device_type.strip()}`"]
    if status_sample:
        parts += [
            "", "## Status seen", "```json",
            json.dumps(status_sample, indent=2, ensure_ascii=False)[:1500],
            "```",
        ]
    parts += [
        "", "## Environment",
        f"- larnitech-mcp {version()}",
        f"- Python {sys.version.split()[0]} on {platform.system()} {platform.release()}",
        "", "---", "*Filed via the `report_bug` tool. Identifiers were redacted automatically —"
        " please check nothing private remains before submitting.*",
    ]

    body, removed_body = redact("\n".join(parts))
    clean_title, removed_title = redact(title)
    truncated = len(body) > _MAX_BODY
    if truncated:
        body = body[:_MAX_BODY] + "\n\n*(truncated)*"

    url = (
        f"{ISSUE_URL}?title={quote(clean_title)}"
        f"&body={quote(body)}&labels=bug"
    )
    return {
        "ok": True,
        "url": url,
        "title": clean_title,
        "body": body,
        "redacted": sorted(set(removed_body + removed_title)),
        "truncated": truncated,
        "repo": REPO,
    }
