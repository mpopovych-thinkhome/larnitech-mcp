# Larnitech MCP

<!-- mcp-name: io.github.mpopovych-thinkhome/larnitech-mcp -->

**Version 1.2.1 Beta** · [Changelog](CHANGELOG.md) · MIT licensed

An [MCP](https://modelcontextprotocol.io) server that lets an AI agent read
and control a [Larnitech](https://larnitech.com) smart-home installation over
the API2 protocol — lights, climate, blinds, sensors, meters.

It ships with a documented device-type reference built from live testing
against real controllers, so the agent looks up how a widget actually
behaves instead of guessing from key names. That matters more than it
sounds: on this platform writing `state: "closed"` to a gate is
acknowledged with `success: true` and then silently ignored, and several
climate types drop half of any two-key write. Those traps are documented,
checked before every write, and listed in this README's own safety section.

---

## What it does

**Reading** — open, no configuration beyond the API key.

| Tool | What it does |
|---|---|
| `list_objects` | configured controllers (never returns keys) |
| `check_connection` | connect, authorize, report device count |
| `list_devices` | full snapshot, filterable by area / type / name |
| `get_device` | status of one device by address |

**Understanding what came back** — statuses are type-specific and
occasionally not key/value at all.

| Tool | What it does |
|---|---|
| `get_docs()` | overview of every documented device type |
| `get_docs("AC")` | full detail for one type: status keys, enums, XML attributes, script byte layout, quirks |
| `get_docs("bugs")` | numbered registry of confirmed vendor bugs |
| `get_docs("protocol")` | API2 protocol reference |

Responses flag statuses that need care: an opaque `hex` blob, a
`malfunction` fault code in place of a normal reading, or an all-`null`
payload from a meter that missed its poll cycle — which means *no data*,
not zeros.

**Watching** — non-blocking, for "press the switch and tell me what moved".

| Tool | What it does |
|---|---|
| `watch_start` | begin watching; returns immediately |
| `watch_read` | drain what changed since the last read, per key `from`/`to` |
| `watch_stop` / `watch_list` | stop one / list active |

A watch keeps its own connection alive, so it survives the controller's
5-minute idle timeout and can stay open across a long conversation.

**Writing** — off by default, two-phase, and never a single tool call.

| Tool | What it does |
|---|---|
| `set_device` | validate, preview the change, return a token — **does not write** |
| `confirm_set` | execute, then wait for the device to settle and report what actually landed |

**Learning** — findings survive the session.

| Tool | Writes to |
|---|---|
| `add_docs_note` | that device type's own doc file |
| `add_preference` | `preferences.md`, served with every `get_docs` |

**Saving data** — a snapshot is worth more than scrollback.

| Tool | What it does |
|---|---|
| `save_snapshot` | keep a slice of controller data as a file |
| `list_snapshots` | what has been saved, per controller |
| `read_snapshot` | read one back, to compare against now |

Files land in `data/<controller>/<date>_<time>_<comment>.txt`, one folder
per controller. Each is a JSON envelope — `object`, `saved_at`, `comment`
and the payload under `data` — so provenance travels with the file and
`read_snapshot` hands back parsed structure rather than text to re-parse.
Numbers stay numbers and `null` stays null, which matters here: telling
"no data" apart from zero is the difference between a quiet meter and a
reading of nothing.

Ask for "save the current state" and the agent files it there; ask "has
this changed since last week" and it has something to compare against.

**Reporting** — `report_bug` turns something you hit into a ready-to-file
issue for this repository. It composes the report, strips identifiers
(API keys, serials, hostnames, site names) and returns a prefilled link.
Nothing is posted: you open the link, read exactly what would be
published, and submit it yourself under your own account. No token is
needed by anyone.

---

## Requirements

- Python 3.11+
- A Larnitech controller you administer, reachable via the Larnitech cloud
  or on your LAN

## Install

```bash
pip install larnitech-mcp
```

A virtual environment is worth using, since you'll point Claude Code at
that interpreter's absolute path:

```bash
python -m venv ~/.venvs/larnitech
~/.venvs/larnitech/bin/pip install larnitech-mcp     # Windows: Scripts\pip.exe
```

Your API keys, preferences, saved snapshots, and any device notes the agent
records live in `~/.larnitech-mcp/`, outside the package, so upgrading never
touches them.

To work on the server itself, install from a clone instead:

```bash
git clone https://github.com/mpopovych-thinkhome/larnitech-mcp.git
cd larnitech-mcp
pip install -e .
```

## Where to get your API key

Both values come from **LT_Setup**, Larnitech's own configuration app, on
the installation you administer:

| What | Where in LT_Setup |
|---|---|
| API key | **Security → Show API key** |
| Serial number (cloud connection) | **General** |
| IP address (LAN connection) | **General**, or your router's DHCP table |
| WebSocket port (LAN, default `2041`) | **General → API → Websocket port** |

The key grants full read and write access to the installation. Treat it
like a password.

## Connect a controller

Register it, then store the key:

```bash
python -m larnitech_mcp add "Home" cloud --serial YOUR_SERIAL
python -m larnitech_mcp auth "Home"
```

`auth` prompts with hidden input and writes the key to
`~/.larnitech-mcp/project_keys.json`. The key never passes through the chat
transcript this way — prefer it over the `object_set_key` tool, which works
but leaves the key in the session log.

For a controller on your LAN instead of via the cloud:

```bash
python -m larnitech_mcp add "Home" local --host 192.168.1.50
```

Check it works:

```bash
python -m larnitech_mcp test "Home"      # connect, authorize, count devices
python -m larnitech_mcp devices "Home"   # full snapshot, counts per type
```

## Add to Claude Code

Add the server to the top-level `mcpServers` object in `~/.claude.json`,
using the absolute path to the venv's Python:

```json
{
  "mcpServers": {
    "larnitech": {
      "command": "/home/you/.venvs/larnitech/bin/python",
      "args": ["-m", "larnitech_mcp", "serve"]
    }
  }
}
```

On Windows the command is the `.exe`, with escaped backslashes:

```json
"command": "C:\\Users\\you\\.venvs\\larnitech\\Scripts\\python.exe"
```

It must be the top-level `mcpServers` key in `~/.claude.json` itself — a
`.mcp.json` placed inside the `~/.claude/` folder is never read. To scope
it to one project instead, put the same block in a `.mcp.json` at that
project's root. Restart Claude Code fully afterwards; closing the window
is not enough.

Other MCP clients work the same way — the server runs on stdio via
`python -m larnitech_mcp serve`.

---

## Safety model

**Reading is open. Writing is off until you turn it on, per controller,
from a terminal:**

```bash
python -m larnitech_mcp allow-write "Home" on
```

There is deliberately no tool for this — an agent cannot grant itself
write access, only tell you the command.

**Every write is two calls.** `set_device` validates the payload, reads
current state, and returns a preview plus a single-use token; it never
touches the controller. `confirm_set(token)` performs the write, waits for
the device to go quiet, then reports what actually landed, including
`unrequested_changes` — anything the controller altered on its own.

**Writes can be sequences,** because some types cannot be driven with one
frame:

```json
[{"status": {"mode": "heat"}, "delay_after": 1.0},
 {"status": {"state": "on"}}]
```

Sending `mode` and `state` together loses the `state`: the controller
re-evaluates the channel after a mode change and overrides whatever
arrived behind it. The same applies to `vent` (`state` + `fan`) and to
clearing an `automation` before switching a channel off. `set_device`
rejects the combined forms and tells you the sequence to use instead.

**No key is ever returned by a tool,** and keys are masked out of error
messages.

## Device documentation

`larnitech_mcp/docs/device-types/` holds one file per device type plus an
index, covering the API2 status keys, XML attributes, script-side byte
layout, and every quirk confirmed by live testing. `bugs.md` alongside it is
a numbered registry of confirmed vendor bugs that the type files reference.
Read them through `get_docs` rather than by path — that also picks up
anything you've added locally.

Notes the agent records with `add_docs_note` go to `~/.larnitech-mcp/docs/`,
not into the installed package, so they survive upgrades. Your copy wins on
read; everything you haven't edited still comes from the shipped set.

This is a working knowledge base, not a spec: entries say plainly when
something is confirmed live, observed but unexplained, or still unknown.
Corrections and additions are welcome — that is the most valuable kind of
contribution here.

## Command reference

| Command | Effect |
|---|---|
| `add <name> cloud --serial S` | register a cloud controller |
| `add <name> local --host H [--port P]` | register a LAN controller |
| `auth <name>` | store its API key (hidden prompt) |
| `list` | configured controllers, key presence |
| `test <name>` | connect, authorize, count devices |
| `devices <name> [--full]` | full snapshot, decoded |
| `allow-write <name> on\|off` | enable or disable writes |
| `remove <name>` | drop a controller and its key |
| `serve` | run the MCP server on stdio |

## Status

Beta. Reading, watching, and writing all work and have been exercised
against live hardware, but this has been tested against a limited set of
installations. Device types documented as unconfirmed genuinely are —
see `get_docs` output and the per-type files.

Not affiliated with or endorsed by Larnitech.

## License

[MIT](LICENSE)

## Contact

Mykhailo Popovych
- Telegram: [t.me/M_Popovych_ThinkHome](https://t.me/M_Popovych_ThinkHome)
- Phone (WhatsApp): +370 632 89 991, +380 99 333 99 96
- Email: [m.popovych@thinkhome.io](mailto:m.popovych@thinkhome.io)
