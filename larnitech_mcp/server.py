"""MCP server exposing Larnitech controllers to an agent.

Reading is open. Writing is opt-in twice over: an object needs `allow_write`
(set from the CLI, never from a tool), and every write goes through
`set_device` -> `confirm_set`, so nothing reaches a controller on a single
tool call.

Per-device-type status keys, value formats, and quirks are served on demand
through `get_docs`, not dumped into every response — call it once with no
argument at the start of a session for the type overview, then per-type as
needed.
"""
from __future__ import annotations

import asyncio
import secrets
import time
from collections import Counter

from mcp.server import MCPServer

from . import config, docs, report, snapshots, validate, watch
from .client import LarnitechError, Session, build_url, request_once

# A write is not settled when the first push arrives: several types make the
# controller re-evaluate the channel and emit further changes of its own
# 0.3-0.8s later (fancoil dropping `state` after a `mode` change, a channel
# coming back on after its automation is cleared). So confirmation waits for
# *silence* — no new event for this long — rather than for the first event.
_SETTLE_QUIET = 1.0
# Absolute cap on that wait, so a chatty device can't stall the tool.
_SETTLE_MAX = 6.0

mcp = MCPServer("larnitech")

# set_device parks a validated write here; confirm_set is the only consumer.
_PENDING: dict[str, dict] = {}
_TOKEN_TTL = 300


def _load(object_name: str) -> tuple[dict, str]:
    obj = config.get_object(object_name)
    return obj, config.get_key(object_name)


def _all_null(value) -> bool:
    """True for a non-empty container whose every leaf is None."""
    if value is None:
        return True
    if isinstance(value, dict):
        return bool(value) and all(_all_null(v) for v in value.values())
    if isinstance(value, list):
        return bool(value) and all(_all_null(v) for v in value)
    return False


def _status_note(device: dict) -> str | None:
    """Flag a status that is not a plain map of semantic keys.

    Several types don't answer with `{"key": value}` at all, and one failure
    mode (a meter missing its poll cycle) looks exactly like real zeros
    unless it's called out.
    """
    status = device.get("status")
    if status is None:
        return "no status reported"
    if not isinstance(status, dict):
        return f"status is a bare {type(status).__name__}, not an object — type-specific encoding"
    if not status:
        return "status is empty"
    if _all_null(status):
        return ("every field is null — the device did not answer this poll cycle. "
                "This is NO DATA: not zero, not an error. Keep the previous reading "
                "rather than reporting these as values")

    notes = []
    if "malfunction" in status:
        notes.append(
            f"device reports a fault (malfunction={status['malfunction']!r}) "
            "in place of its normal status"
        )
    if "hex" in status and not [k for k in status if k not in ("hex", "_raw")]:
        notes.append(
            "status is an opaque `hex` blob with no semantic keys — "
            "decode it per this type's get_docs entry, don't guess"
        )
    if "_raw" in status:
        notes.append(
            "`_raw` is this client's wrapper for the controller's doubled-brace JSON "
            "quirk, not a Larnitech field"
        )
        if _all_null(status.get("_raw")):
            notes.append(
                "inside `_raw` every field is null — no data this poll cycle, "
                "not zeros"
            )
    return "; ".join(notes) if notes else None


def _row(device: dict, include_status: bool) -> dict:
    row = {
        "addr": device.get("addr"),
        "type": device.get("type"),
        "name": device.get("name"),
        "area": device.get("area"),
    }
    if device.get("sub-type"):
        row["sub_type"] = device["sub-type"]
    if include_status:
        row["status"] = device.get("status")
        note = _status_note(device)
        if note:
            row["status_note"] = note
    return row


def _normalize_steps(status, steps) -> list[dict]:
    """Accept a single `status` or an explicit `steps` sequence, return steps."""
    if steps is not None and status is not None:
        raise ValueError("pass either `status` (one write) or `steps` (a sequence), not both")
    if steps is None:
        if status is None:
            raise ValueError("pass `status` for one write, or `steps` for a sequence")
        return [{"status": status, "delay_after": 0.0}]
    if not isinstance(steps, list) or not steps:
        raise ValueError("`steps` must be a non-empty list")
    out = []
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict) or "status" not in step:
            raise ValueError(f"step {i} must be an object with a 'status' key")
        try:
            delay = float(step.get("delay_after") or 0.0)
        except (TypeError, ValueError):
            raise ValueError(f"step {i}: delay_after must be a number of seconds")
        out.append({"status": step["status"], "delay_after": max(0.0, delay)})
    return out


async def _drain_until_quiet(session, addr, into: dict, quiet: float, max_wait: float) -> int:
    """Merge pushed statuses for `addr` until `quiet` seconds pass with none.

    Push events are partial, so they merge into `into` rather than replace it.
    """
    loop = asyncio.get_running_loop()
    hard_deadline = loop.time() + max_wait
    seen = 0
    while True:
        remaining = min(quiet, hard_deadline - loop.time())
        if remaining <= 0:
            return seen
        frame = await session.recv_event(timeout=remaining)
        if frame is None:
            return seen  # quiet window elapsed with nothing new
        if frame.get("event") != "statuses":
            continue
        device = _find_device(frame.get("devices") or [], addr)
        if device and isinstance(device.get("status"), dict):
            into.update(device["status"])
            seen += 1


# --- objects -------------------------------------------------------------


@mcp.tool()
def list_objects() -> dict:
    """List configured Larnitech objects. Never returns API keys."""
    objects = config.load_objects()
    return {
        "config_file": str(config.config_path()),
        "key_storage": config.backend_name(),
        "objects": [
            {
                "name": name,
                "mode": obj.get("mode"),
                "target": obj.get("serial") if obj.get("mode") == "cloud" else obj.get("host"),
                "has_key": config.has_key(name),
                "allow_write": bool(obj.get("allow_write")),
            }
            for name, obj in objects.items()
        ],
    }


@mcp.tool()
def object_add(
    name: str,
    mode: str,
    serial: str | None = None,
    host: str | None = None,
    port: int = config.DEFAULT_LOCAL_PORT,
) -> dict:
    """Register an object. `mode` is "cloud" (needs `serial`) or "local" (needs `host`).

    Does not take the API key — store it separately with `object_set_key`, or
    preferably outside the chat with `python -m larnitech_mcp auth "<name>"`.
    """
    record = config.add_object(name, mode, serial=serial, host=host, port=port)
    return {
        "name": name,
        "url": build_url(record),
        "has_key": config.has_key(name),
        "next_step": f'python -m larnitech_mcp auth "{name}"' if not config.has_key(name) else "ready",
    }


@mcp.tool()
def object_set_key(name: str, key: str) -> dict:
    """Store the API key for an object in the OS credential store.

    The key is write-only from here on: no tool returns it, and it is masked out
    of error messages. Note that a key typed into chat stays in this session's
    transcript — `python -m larnitech_mcp auth "<name>"` avoids that.
    """
    config.get_object(name)  # fail early if the object is unknown
    config.set_key(name, key)
    return {"name": name, "stored_in": config.backend_name(), "has_key": True}


@mcp.tool()
def object_remove(name: str) -> dict:
    """Remove an object from the registry and delete its stored key."""
    config.remove_object(name)
    return {"removed": name}


@mcp.tool()
async def check_connection(object_name: str) -> dict:
    """Connect and authorize against an object, and report what it answers.

    First Larnitech tool call this session? Call `get_docs()` (no argument)
    first for the device-type overview.
    """
    obj, key = _load(object_name)
    try:
        answer = await request_once(obj, key, {"request": "get-devices"})
    except LarnitechError as err:
        return {"object": object_name, "url": build_url(obj), "ok": False,
                "error": config.mask(str(err), object_name)}
    return {
        "object": object_name,
        "url": build_url(obj),
        "ok": True,
        "devices": answer.get("found", len(answer.get("devices", []))),
    }


# --- device-type docs -----------------------------------------------------


@mcp.tool()
def get_docs(device_type: str | None = None) -> dict:
    """Reference docs for interpreting or writing a device's `status`.

    Call with no argument **once, at the start of a session**, before the
    first `list_devices`/`get_device` call — it returns the type overview
    (every known type, its rough status shape, and known issues). Call again
    with a specific `device_type` (as returned in a device's `type` field,
    e.g. "AC", "dimmer-lamp") when you need full detail on that one type:
    exact status keys/enums, XML attributes, script-side byte layout, and
    quirks/bugs.

    Two extra documents share this tool: `get_docs("bugs")` is the numbered
    vendor-bug registry every `BUG-NNN` reference points at, and
    `get_docs("protocol")` is the API2 protocol guide (commands, framing
    quirks, connection rules).

    Every response also carries `user_preferences` — standing instructions
    that override the wiki where they disagree. Honour them.
    """
    return docs.get(device_type)


@mcp.tool()
def add_docs_note(device_type: str, note: str, index_title: str | None = None) -> dict:
    """Record a new Larnitech finding in the device-type wiki, permanently.

    Use for anything true about the equipment itself — a quirk found live, a
    value that differs from what is documented, a confirmed behaviour. Writes
    a dated bullet into that type's Notes section.

    `index_title` (a few words) also lists the quirk in the type overview, so
    a later session sees it exists without opening the file. Pass it whenever
    the finding changes how the type should be read or written.

    A general working preference that is not about Larnitech or a device type
    belongs in `add_preference` instead. Confirm with the user before
    rewriting an existing documented fact; appending a new finding is fine.
    """
    try:
        return docs.add_note(device_type, note, index_title)
    except docs.DocsError as err:
        return {"ok": False, "error": str(err), "available_types": docs.available_types()}


@mcp.tool()
def add_preference(note: str) -> dict:
    """Record a standing user preference about how to work, permanently.

    For instructions that are not facts about the equipment: how to present
    results, what to avoid touching, which units to use, how to phrase
    things. Served back with every `get_docs` call and applied on top of the
    wiki.

    Anything specific to Larnitech or to a device type belongs in
    `add_docs_note` instead.
    """
    try:
        return docs.add_preference(note)
    except docs.DocsError as err:
        return {"ok": False, "error": str(err)}


# --- reading -------------------------------------------------------------


@mcp.tool()
async def list_devices(
    object_name: str,
    area: str | None = None,
    device_type: str | None = None,
    name_contains: str | None = None,
    include_status: bool = True,
) -> dict:
    """Full device snapshot from an object, optionally filtered.

    Filters are case-insensitive; `area` and `device_type` match exactly,
    `name_contains` is a substring match.

    Each device's `status` uses a type-specific key/value format — call
    `get_docs(device_type=type)` before interpreting it.
    """
    obj, key = _load(object_name)
    answer = await request_once(
        obj, key, {"request": "get-devices", "status": "detailed"}
    )
    devices = answer.get("devices", [])
    total = len(devices)

    def keep(d: dict) -> bool:
        if area and (d.get("area") or "").lower() != area.lower():
            return False
        if device_type and (d.get("type") or "").lower() != device_type.lower():
            return False
        if name_contains and name_contains.lower() not in (d.get("name") or "").lower():
            return False
        return True

    devices = [d for d in devices if keep(d)]
    return {
        "object": object_name,
        "total": total,
        "returned": len(devices),
        "types": dict(Counter(d.get("type") for d in devices).most_common()),
        "areas": sorted({d.get("area") for d in devices if d.get("area")}),
        "devices": [_row(d, include_status) for d in devices],
    }


@mcp.tool()
async def get_device(object_name: str, addr: str) -> dict:
    """Current status of one device by `addr` (format `MODULE:ADDR`, e.g. `1:101`).

    `status-get` answers thin — only addr/type/status, no name/area/masks. Those
    come from `list_devices`.

    The `status` keys and their value formats are type-specific — call
    `get_docs(device_type=type)` before interpreting it.
    """
    obj, key = _load(object_name)
    answer = await request_once(
        obj, key, {"request": "status-get", "addr": addr, "status": "detailed"}
    )
    devices = answer.get("devices", [])
    if not devices:
        return {"object": object_name, "addr": addr, "found": False}
    device = devices[0]
    result = {
        "object": object_name,
        "addr": addr,
        "found": True,
        "type": device.get("type"),
        "status": device.get("status"),
    }
    note = _status_note(device)
    if note:
        result["status_note"] = note
    return result


# --- watching ------------------------------------------------------------


@mcp.tool()
async def watch_start(object_name: str, addr: str | None = None) -> dict:
    """Begin watching status changes. Returns immediately with a `watch_id`.

    Nothing blocks: the subscription runs in the background while you keep
    talking to the user. The intended flow is start -> ask the user to act on
    the system (press a switch, change a setpoint) -> `watch_read` to see
    exactly which keys moved -> `watch_stop`.

    `addr` limits the watch to one device; omitted, it watches everything.
    The session is kept alive automatically, so a watch can stay open across
    a long conversation.
    """
    obj, key = _load(object_name)
    try:
        handle = await watch.start(object_name, obj, key, addr)
    except LarnitechError as err:
        return {"ok": False, "error": config.mask(str(err), object_name)}
    summary = handle.summary()
    summary["next"] = f'let the user act, then watch_read("{handle.id}")'
    return summary


@mcp.tool()
def watch_read(watch_id: str) -> dict:
    """Drain everything that changed since the last read. Never blocks.

    Returns one entry per change with `from`/`to` per key, plus `new_keys`
    for keys the device was not reporting when the watch opened — those are
    worth checking against `get_docs` and recording with `add_docs_note` if
    genuinely undocumented.

    Events never identify what caused a change: the protocol's exciter
    fields always arrive empty, so a change made by a person at a wall
    panel, by a controller script, and by this MCP's own write all look
    identical. Don't attribute a change to anyone.

    Button/key inputs (`switch`) report an opaque `hex` that does not clear
    between gestures — compare each reading against the previous one for
    that addr rather than treating every event as a fresh press.

    An empty `changes` list just means nothing has happened yet; call again
    after the user acts.
    """
    try:
        handle = watch.get(watch_id)
    except LarnitechError as err:
        return {"ok": False, "error": str(err)}
    changes = handle.drain()
    result = handle.summary()
    result["changes"] = changes
    result["returned"] = len(changes)
    return result


@mcp.tool()
async def watch_stop(watch_id: str) -> dict:
    """Stop a watch and close its socket. Any undrained changes are returned."""
    try:
        handle = watch.get(watch_id)
    except LarnitechError as err:
        return {"ok": False, "error": str(err)}
    remaining = handle.drain()
    summary = await watch.stop(watch_id)
    summary["changes"] = remaining
    return summary


@mcp.tool()
def watch_list() -> dict:
    """Active watches, with how long each has run and how much it has seen."""
    return {"watches": watch.active()}


# --- writing -------------------------------------------------------------


def _find_device(devices: list[dict], addr: str) -> dict | None:
    return next((d for d in devices if d.get("addr") == addr), None)


@mcp.tool()
async def set_device(
    object_name: str,
    addr: str,
    status: dict | None = None,
    steps: list[dict] | None = None,
) -> dict:
    """Validate a write and return a preview plus a confirmation token.

    **This never touches the controller.** It reads the device's current
    state, checks the payload, and returns what would change. Nothing
    happens until `confirm_set(token)`.

    Pass `status` for a single write, or `steps` for a sequence:

        steps=[{"status": {"mode": "heat"}, "delay_after": 1.0},
               {"status": {"state": "on"}}]

    Sequences exist because several types cannot be driven with one frame:
    the controller re-evaluates the channel after certain keys and overrides
    whatever else arrived too soon behind them (`fancoil` mode+state,
    `vent` state+fan, clearing an `automation` then switching off). The
    per-type rules live in the docs — `quirks` in the response repeats that
    type's known issues so you can see them without a second call.

    Show the user the preview, especially `warnings` and `quirks`, and get
    their agreement before confirming.
    """
    obj, key = _load(object_name)
    if not obj.get("allow_write"):
        return {
            "ok": False,
            "error": f"writes are disabled for {object_name!r}",
            "fix": f'run in a terminal: python -m larnitech_mcp allow-write "{object_name}" on',
            "why": "writes are opt-in per object and can only be enabled outside the chat",
        }

    addr_errors = validate.check_addr(addr)
    if addr_errors:
        return {"ok": False, "errors": addr_errors}

    try:
        plan = _normalize_steps(status, steps)
    except ValueError as err:
        return {"ok": False, "errors": [str(err)]}

    try:
        answer = await request_once(obj, key, {"request": "get-devices", "status": "detailed"})
    except LarnitechError as err:
        return {"ok": False, "error": config.mask(str(err), object_name)}
    device = _find_device(answer.get("devices", []), addr)
    if device is None:
        return {"ok": False, "error": f"no device at {addr} on {object_name!r}"}

    dtype = (device.get("type") or "").lower()
    current = device.get("status") if isinstance(device.get("status"), dict) else {}

    errors: list[str] = []
    warnings: list[str] = []
    preview: list[dict] = []
    running = dict(current)
    single = len(plan) == 1
    for i, step in enumerate(plan, 1):
        step_errors, step_warnings = validate.check(device, step["status"])
        label = "" if single else f"step {i}: "
        errors += [label + e for e in step_errors]
        warnings += [label + w for w in step_warnings]
        preview.append({
            "step": i,
            "status": step["status"],
            "delay_after": step["delay_after"],
            "changes": {
                k: {"from": running.get(k), "to": v}
                for k, v in step["status"].items()
            } if isinstance(step["status"], dict) else step["status"],
        })
        if isinstance(step["status"], dict):
            running.update(step["status"])

    result = {
        "device": _row(device, include_status=False),
        "current_status": current,
        "warnings": warnings,
        "quirks": docs.quirks(dtype) or "none recorded for this type",
    }
    note = _status_note(device)
    if note:
        result["status_note"] = note
    if errors:
        return {"ok": False, "errors": errors, **result}

    token = secrets.token_hex(6)
    _PENDING[token] = {
        "object_name": object_name,
        "addr": addr,
        "plan": plan,
        "before": dict(current),
        "expires": time.time() + _TOKEN_TTL,
    }
    result.update({
        "ok": True,
        "token": token,
        "expires_in": _TOKEN_TTL,
        "preview": preview[0]["changes"] if single else preview,
        "steps": len(plan),
        "next": f'confirm with the user, then confirm_set("{token}")',
    })
    return result


@mcp.tool()
async def confirm_set(token: str) -> dict:
    """Execute a write prepared by `set_device`, then confirm it settled.

    Only call this after the user has agreed to the preview. The token is
    single-use and expires; a stale one means preparing the write again.

    A `status-set` ack only means the command was accepted, not that it took
    effect — some types ack a write they then ignore. So this subscribes
    first, runs the steps with their pauses, and then waits for the device
    to go **quiet** (no new pushed event for ~1s) before reading the
    authoritative final status. Waiting for silence rather than for the
    first event is what catches the controller changing something back on
    its own a fraction of a second later.

    `unrequested_changes` reports keys the controller moved that you did not
    ask for — that is the fingerprint of a type needing a different step
    sequence.
    """
    pending = _PENDING.pop(token, None)
    if pending is None:
        return {"ok": False, "error": "unknown or already-used token — call set_device again"}
    if time.time() > pending["expires"]:
        return {"ok": False, "error": f"token expired after {_TOKEN_TTL}s — call set_device again"}

    object_name, addr, plan = pending["object_name"], pending["addr"], pending["plan"]
    obj, key = _load(object_name)
    if not obj.get("allow_write"):  # re-check: it can be revoked between the two calls
        return {"ok": False, "error": f"writes are disabled for {object_name!r}"}

    observed: dict = {}
    acks: list[bool] = []
    after: dict = {}
    try:
        async with Session(obj, key) as session:
            await session.request(
                {"request": "status-subscribe", "addr": addr, "status": "detailed"}
            )
            for step in plan:
                answer = await session.request(
                    {"request": "status-set", "addr": addr, "status": step["status"]}
                )
                ack = _find_device(answer.get("devices", []), addr) or {}
                acks.append(bool(ack.get("success")))
                if step["delay_after"]:
                    # Spend the pause listening, so the controller's own
                    # reaction to this step is captured rather than missed.
                    await _drain_until_quiet(
                        session, addr, observed,
                        quiet=step["delay_after"], max_wait=step["delay_after"],
                    )

            events = await _drain_until_quiet(
                session, addr, observed, quiet=_SETTLE_QUIET, max_wait=_SETTLE_MAX
            )

            verify = await session.request(
                {"request": "status-get", "addr": addr, "status": "detailed"}
            )
            device = _find_device(verify.get("devices", []), addr)
            if device and isinstance(device.get("status"), dict):
                after = device["status"]
    except LarnitechError as err:
        return {"ok": False, "error": config.mask(str(err), object_name)}

    requested: dict = {}
    for step in plan:
        if isinstance(step["status"], dict):
            requested.update(step["status"])

    before = pending["before"]
    applied = {k: after.get(k) for k in requested} if after else {}
    mismatched = [k for k, v in requested.items() if after and after.get(k) != v]
    unrequested = {
        k: {"from": before.get(k), "to": v}
        for k, v in observed.items()
        if k not in requested and before.get(k) != v
    }

    return {
        "ok": all(acks) and not mismatched,
        "object": object_name,
        "addr": addr,
        "steps_run": len(plan),
        "acknowledged": all(acks),
        "requested": requested,
        "before": {k: before.get(k) for k in requested},
        "after": applied,
        "mismatched": mismatched,
        "events_observed": events,
        "unrequested_changes": unrequested,
        "note": (
            "mismatched keys were acknowledged but did not take the requested value — "
            "check this type's quirks for a required step sequence"
            if mismatched else None
        ),
    }


# --- reporting -----------------------------------------------------------


@mcp.tool()
def report_bug(
    title: str,
    what_happened: str,
    expected: str | None = None,
    device_type: str | None = None,
    status_sample: dict | None = None,
) -> dict:
    """Turn a bug the user hit into a ready-to-file GitHub issue.

    Use this when something in this MCP or in a controller's behaviour looks
    wrong and the user wants the maintainer to know — a status that doesn't
    match the docs, a write that is acknowledged but ignored, a device type
    that behaves differently than documented.

    **This does not post anything.** It composes the report and returns a
    prefilled "new issue" link. Show the user the `body`, then give them the
    `url` to open and submit themselves — they publish it under their own
    account, after reading it. Never describe the report as sent.

    Identifiers are stripped automatically (API keys, serials, hostnames,
    object names) and listed in `redacted`, but quote device output rather
    than paraphrasing it so the maintainer sees the real shape.

    A finding about how the equipment behaves is worth recording locally too
    — `add_docs_note` keeps it for this installation regardless of whether
    the issue is ever filed.
    """
    return report.build(
        title=title,
        what_happened=what_happened,
        expected=expected,
        device_type=device_type,
        status_sample=status_sample,
    )


# --- saved data ----------------------------------------------------------


@mcp.tool()
def save_snapshot(object_name: str, content, comment: str) -> dict:
    """Keep a slice of controller data on disk, for later.

    Use whenever data is worth more than this conversation: a full device
    dump before making changes, the state of one area, a watch trace, a
    reading to compare against next week. The user asking to "save this" or
    "record the current state" means this tool.

    `content` is whatever you want kept — a string, or an object/list which
    is stored as JSON. It is written verbatim, so a snapshot can be read
    back and parsed.

    `comment` is a short slug describing what the slice is
    ("before-fancoil-swap", "all-climate-zones"). The file is named
    `<date>_<time>_<comment>.txt` inside a folder for that object.
    """
    try:
        return snapshots.save(object_name, content, comment)
    except snapshots.SnapshotError as err:
        return {"saved": False, "error": str(err)}


@mcp.tool()
def list_snapshots(object_name: str | None = None) -> dict:
    """Snapshots saved for one object, or a summary across all of them.

    Check this before answering "has this changed since last time" — an
    earlier snapshot is usually the only record of how something looked.
    """
    return snapshots.listing(object_name)


@mcp.tool()
def read_snapshot(object_name: str, file: str) -> dict:
    """Read a saved snapshot back, by the filename `list_snapshots` reports."""
    try:
        return snapshots.read(object_name, file)
    except snapshots.SnapshotError as err:
        return {"error": str(err)}


def main() -> None:
    mcp.run()
