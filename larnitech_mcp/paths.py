"""Where the server's files live, in a checkout and once pip-installed.

Two very different situations:

  * **A source checkout** (this repo, or `pip install -e .`) — docs sit
    beside the package and everything is writable. The maintainer's copy
    reaches its docs through a junction into a private knowledge base, so
    the checkout's own paths must keep winning there.

  * **An installed wheel** — the package lives in `site-packages`, which is
    shared, may need admin rights, and is replaced wholesale on upgrade.
    Docs ship *inside* the package and are read-only; anything the user
    owns (API keys, preferences, notes they add) belongs in their home
    directory instead, where an upgrade cannot delete it.

`LARNITECH_MCP_HOME` overrides the user directory, which is what the tests
and anyone running several configurations use.
"""
from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
CHECKOUT_DIR = PACKAGE_DIR.parent
APP_DIR_NAME = ".larnitech-mcp"


def is_checkout() -> bool:
    """True when running from a source tree rather than an installed wheel."""
    return (CHECKOUT_DIR / "pyproject.toml").exists()


def user_dir() -> Path:
    override = os.environ.get("LARNITECH_MCP_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / APP_DIR_NAME


def bundled_docs() -> Path:
    """Docs shipped inside the package. Read-only by convention."""
    return PACKAGE_DIR / "docs"


def docs_root() -> Path:
    """The docs to serve: the checkout's own if present, else the bundled set."""
    if is_checkout() and (CHECKOUT_DIR / "device-types").is_dir():
        return CHECKOUT_DIR
    return bundled_docs()


def docs_are_writable() -> bool:
    """Whether doc edits can go straight to the served copy."""
    return docs_root() != bundled_docs()


def docs_overlay() -> Path:
    """Where doc edits go when the served docs are the bundled, read-only set."""
    return user_dir() / "docs"


def user_file(name: str) -> Path:
    """A file the user owns — keys, preferences.

    In a checkout this stays beside the package, so an existing setup keeps
    working untouched. Installed, it moves to the user directory.
    """
    if is_checkout():
        return CHECKOUT_DIR / name
    return user_dir() / name
