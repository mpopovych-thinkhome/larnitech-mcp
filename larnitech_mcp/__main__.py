r"""CLI: store keys without going through the chat, and check a connection.

    python -m larnitech_mcp serve                  run the MCP server (stdio)
    python -m larnitech_mcp auth "Test stand"    store an API key (hidden input)
    python -m larnitech_mcp add "Test stand" cloud --serial a1b2c3d4
    python -m larnitech_mcp list
    python -m larnitech_mcp test "Test stand"
    python -m larnitech_mcp allow-write "Test stand" on
    python -m larnitech_mcp data-dir "Test stand" "D:\Projects\Office\Backups"
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from collections import Counter
from getpass import getpass

from . import config
from .client import LarnitechError, build_url, request_once


def _cmd_auth(args) -> int:
    config.get_object(args.name)
    key = getpass(f"API key for {args.name!r} (input hidden): ")
    config.set_key(args.name, key)
    print(f"stored in {config.backend_name()}")
    return 0


def _cmd_add(args) -> int:
    record = config.add_object(
        args.name, args.mode, serial=args.serial, host=args.host, port=args.port
    )
    print(f"{args.name} -> {build_url(record)}")
    if not config.has_key(args.name):
        print(f'no key yet: python -m larnitech_mcp auth "{args.name}"')
    return 0


def _cmd_list(args) -> int:
    objects = config.load_objects()
    print(f"config:  {config.config_path()}")
    print(f"storage: {config.backend_name()}")
    if not objects:
        print("no objects configured")
        return 0
    for name, obj in objects.items():
        key = "key ok" if config.has_key(name) else "NO KEY"
        write = "write allowed" if obj.get("allow_write") else "read-only"
        print(f"  {name}: {build_url(obj)}  [{key}, {write}]")
        if obj.get("data_dir"):
            print(f"      snapshots -> {obj['data_dir']}")
    return 0


def _cmd_test(args) -> int:
    obj = config.get_object(args.name)
    key = config.get_key(args.name)
    try:
        answer = asyncio.run(request_once(obj, key, {"request": "get-devices"}))
    except LarnitechError as err:
        print(f"FAILED {build_url(obj)}: {config.mask(str(err), args.name)}")
        return 1
    print(f"OK {build_url(obj)} — {answer.get('found', 0)} devices")
    return 0


def _cmd_devices(args) -> int:
    """Full get-devices snapshot — proves connect+auth+decode end-to-end."""
    obj = config.get_object(args.name)
    key = config.get_key(args.name)
    try:
        answer = asyncio.run(
            request_once(obj, key, {"request": "get-devices", "status": "detailed"})
        )
    except LarnitechError as err:
        print(f"FAILED {build_url(obj)}: {config.mask(str(err), args.name)}")
        return 1

    devices = answer.get("devices", [])
    print(f"{build_url(obj)} — {answer.get('found', len(devices))} devices")
    by_type = Counter(d.get("type") for d in devices)
    for dtype, count in by_type.most_common():
        print(f"  {dtype:22} {count}")

    if args.full:
        print()
        for d in devices:
            addr = d.get("addr", "")
            dtype = d.get("type", "")
            name = d.get("name", "")
            area = d.get("area", "")
            status = d.get("status", "")
            print(f"{addr:12} {dtype:20} {name:28} {area:16} {status}")
    return 0


def _cmd_data_dir(args) -> int:
    """Point an object's snapshots at its own project folder, or clear it."""
    record = config.set_data_dir(args.name, None if args.clear else args.path)
    where = record.get("data_dir") or "(default: the MCP data folder)"
    print(f"{args.name}: snapshots -> {where}")
    return 0


def _cmd_allow_write(args) -> int:
    """Writes are opt-in per object, and only from here — never from a chat tool."""
    allowed = args.state == "on"
    config.set_allow_write(args.name, allowed)
    print(f"{args.name}: {'write allowed' if allowed else 'read-only'}")
    return 0


def _cmd_remove(args) -> int:
    config.remove_object(args.name)
    print(f"removed {args.name!r} (object + stored key)")
    return 0


def _cmd_serve(args) -> int:
    from .server import main

    main()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="larnitech_mcp", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("serve", help="run the MCP server on stdio").set_defaults(fn=_cmd_serve)

    p = sub.add_parser("auth", help="store an API key (hidden input)")
    p.add_argument("name")
    p.set_defaults(fn=_cmd_auth)

    p = sub.add_parser("add", help="register an object")
    p.add_argument("name")
    p.add_argument("mode", choices=config.MODES)
    p.add_argument("--serial")
    p.add_argument("--host")
    p.add_argument("--port", type=int, default=config.DEFAULT_LOCAL_PORT)
    p.set_defaults(fn=_cmd_add)

    sub.add_parser("list", help="list configured objects").set_defaults(fn=_cmd_list)

    p = sub.add_parser("test", help="connect and count devices")
    p.add_argument("name")
    p.set_defaults(fn=_cmd_test)

    p = sub.add_parser("devices", help="full get-devices snapshot (type counts, optionally every device)")
    p.add_argument("name")
    p.add_argument("--full", action="store_true", help="print every device, not just the type breakdown")
    p.set_defaults(fn=_cmd_devices)

    p = sub.add_parser("data-dir", help="store an object's snapshots in a folder of its own")
    p.add_argument("name")
    p.add_argument("path", nargs="?", help="folder to keep this object's snapshots in")
    p.add_argument("--clear", action="store_true", help="revert to the default data folder")
    p.set_defaults(fn=_cmd_data_dir)

    p = sub.add_parser("allow-write", help="allow or forbid writes for an object")
    p.add_argument("name")
    p.add_argument("state", choices=("on", "off"))
    p.set_defaults(fn=_cmd_allow_write)

    p = sub.add_parser("remove", help="drop an object and delete its stored key")
    p.add_argument("name")
    p.set_defaults(fn=_cmd_remove)

    args = parser.parse_args()
    try:
        return args.fn(args)
    except config.ConfigError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
