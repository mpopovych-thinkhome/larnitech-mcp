Every change bumps the version here and gets an entry — agreed before it
lands, not after.

## 1.2.1 Beta — 2026-09-02

Documentation only — no code changes. Four device types added and two open
questions closed, all from live testing against a controller that carries
types the earlier objects did not.

**`speaker`** — media point. Transport commands all confirmed working, but
the write vocabulary is not the read vocabulary *and differs per command*:
`play` reads back `playing`, `stop` reads `stopped`, `pause` reads `pause`.
Three rules in one type; the table is in the docs because inferring it is
hopeless. `next`/`previous` switch **source**, not track — confirmed by the
`url` changing between radio streams. `volume` is a 0-100 percent over an
underlying 0-250 scale, so a written value snaps to the nearest 0.4% step:
writing `5` reads back `5.2`, which makes an exact-match write verify
report a good write as failed. `position` is a seconds-with-milliseconds
string, not the raw milliseconds the script API uses.

**`percent-sensor`, `float-sensor`, `current-sensor`** — generic scalar
readouts, used on the observed controller for self-telemetry. The type name
describes display formatting; an XML-only `hw` attribute says what the
value actually is. `percent-sensor` returned 768 and 256 on an idle CPU, so
**the value is not a percent as it arrives** — every sample was a multiple
of 256, which fits a raw two-byte encoding, recorded as the leading
hypothesis rather than as fact. `current-sensor` is amperes; its encoding
is unconfirmed because the one observed device reads zero.

**Motion automations documented.** `lamp`, `dimmer-lamp`, `rgb-lamp` and
`light-scheme` can carry `<automation>` rules — `on-by-moving`,
`off-by-moving`, `off-by-door` — with separate on and off thresholds for
hysteresis. None of it is visible through API2: the only trace is the
boolean `auto-state`, so the API cannot explain why a light changed by
itself. Written once in `lamp.md`, referenced from the other three.

**`motion-sensor` conflict resolved.** The docs carried an unresolved
disagreement over whether `state` is a boolean. It is not — live readings
of `39.65` and `0.0` settle it as a continuous level compared against a
threshold, which is exactly how the controller's own automations use it.

**[BUG-009](https://github.com/mpopovych-thinkhome/larnitech-mcp/blob/main/larnitech_mcp/docs/bugs.md)** — an invalid `state`
write to a `speaker` is not rejected; it drives the widget into `error` and
leaves it there. `AC` rejects a bad value cleanly, so this is specific to
the type. Recovery is a plain `play`.

## 1.2.0 Beta — 2026-09-02

**Snapshots are a JSON envelope now.** 1.1.0 wrote whatever it was handed,
which meant the format depended on whoever saved it — one folder already
held a CSV table written by a different session. Reading one back therefore
meant sniffing the format and guessing at column types.

Every snapshot is now:

```json
{"object": ..., "saved_at": ..., "comment": ..., "data": <payload>}
```

Provenance travels with the file rather than living only in the folder and
filename, and `read_snapshot` returns the payload already parsed under
`data` — no parsing step, no guessing. Types survive the round trip: a
reading saved as `22.38` comes back a float, and `null` stays null instead
of becoming the string "null". That distinction is load-bearing here, since
an all-`null` payload means "the device did not answer", not zero.

JSON costs roughly 2-3x the bytes of an equivalent CSV table. Paid
deliberately, for the type fidelity and the fixed shape.

Files written before this, or by hand, still read back: `format` reports
`raw` or `json` instead of `envelope`, and says they carry no provenance.

**Better miss on an unknown folder.** A snapshot filed under a folder name
that isn't derived from the object name used to fail with an unhelpful
empty list. The error now names the folders that do exist and says they can
be passed directly.

## 1.1.0 Beta — 2026-09-02

**Saved snapshots.** Three tools — `save_snapshot`, `list_snapshots`,
`read_snapshot` — keep slices of controller data on disk instead of losing
them to scrollback. A conversation is a bad place to hold a device dump:
it scrolls away, and the next session has nothing to diff against.

Files land in `data/<object>/<date>_<time>_<comment>.txt`, one folder per
controller, newest sorting last. Content is written verbatim — objects as
JSON, strings as-is, no injected header — so a snapshot can be read back
and parsed. Object names are slugged for the filesystem, since a real name
like `test stand` contains characters Windows forbids.

Storage follows the same rule as keys and preferences: beside the package
in a checkout, `~/.larnitech-mcp/data/` once installed.

**`data/` never ships.** Snapshots hold real device data from real sites,
so `publish.py` deletes the folder from the built tree and `.gitignore`
keeps it out of the repository.

## 1.0.2 Beta — 2026-08-28

First version actually published to PyPI. 1.0.0 and 1.0.1 were tagged
before the publishing workflow existed, so neither reached the index.

**Registry metadata.** Added `server.json` for the official MCP registry,
validated against its schema, and the `mcp-name` marker the registry looks
for in the published package description to verify PyPI ownership. Both had
to be in place *before* the first upload, since the check runs against
what PyPI actually serves.

**Automated publishing.** A GitHub Actions workflow publishes on a version
tag using PyPI Trusted Publishing — no API token is created or stored. It
asserts the docs are inside the built wheel before uploading, because
shipping one without them silently breaks `get_docs` (which is exactly what
1.0.0 did).

**Stale-docs guard.** The docs served from a maintainer checkout are hard
links into a knowledge base. An atomic editor save broke one, and a newly
written bug entry (BUG-006) silently never reached the built package. The
release build now compares the two and refuses to run on a stale copy
instead of trusting the link. BUG-006 is restored.

## 1.0.1 Beta — 2026-08-28

Packaging fix — 1.0.0 could only be installed from a clone.

**The wheel shipped no documentation.** Docs sat beside the package at the
repo root, so `pip install` produced a server whose `get_docs` — the whole
point of it — returned nothing. They now live inside the package
(`larnitech_mcp/docs/`) and are declared as package data. Verified by
installing the built wheel into a clean environment: 33 doc files present,
all four `get_docs` forms answer.

**User data no longer lands in `site-packages`.** API keys and preferences
resolved to a path beside the package, which once installed is shared,
often needs admin rights, and is wiped on upgrade. They now go to
`~/.larnitech-mcp/` (override with `LARNITECH_MCP_HOME`). A source checkout
keeps using the files beside it, so existing setups are unchanged.

**`add_docs_note` on an installed copy** would have tried to write into
`site-packages`. It now copies the file into a per-user overlay on first
edit and writes there; the overlay wins on read, so notes survive upgrades.
Only edited files are copied, not the whole set.

New `paths` module holds this resolution in one place.

## 1.0.0 Beta — 2026-08-28

First public release. MIT licensed.

**Write sequences.** `set_device` accepts `steps` — a list of
`{status, delay_after}` — because several types cannot be driven with one
frame: the controller re-evaluates the channel after certain keys and
overrides whatever arrived behind them. Combined forms known to fail are
now rejected with the working sequence in the error:
- `fancoil`: `mode` + `state`
- `vent`: `state` + `fan`
- `valve-heating` / `fancoil` / `vent`: `automation` + `state`

**Confirmation waits for silence.** `confirm_set` no longer trusts the
first pushed event. It subscribes, runs the steps with their pauses, then
waits for the device to stop emitting (no new event for ~1s) before
reading the authoritative status. This catches the controller changing
something back on its own 0.3–0.8s later, which the previous
first-event-wins logic reported as success. New `unrequested_changes`
field reports keys the controller moved that were never asked for.

**Statuses that aren't key/value.** Reads now flag:
- an all-`null` payload as *no data this poll cycle* — not zeros, not an
  error (MBUS meters do this when they miss a cycle)
- an opaque `hex` blob with no semantic keys (`switch`, several `virtual`
  sub-types)
- a `malfunction` fault code standing in for a normal status
- `_raw` as this client's own wrapper for the controller's doubled-brace
  JSON quirk, not a Larnitech field

**Docs reachable through the tool.** `get_docs("bugs")` and
`get_docs("protocol")` now serve the vendor-bug registry and the protocol
reference. Previously every `BUG-NNN` reference in the type docs dead-ended
for anyone without filesystem access to them.

**Validation reworked.** `validate.py` no longer tries to mirror the
device docs — a second copy of the rules in code had already drifted and
was shipping one rule that recommended the opposite of what live testing
established. It now carries only what is confirmed, mechanically
checkable, and fails *silently* on the wire; everything else comes from
the docs, and `set_device` attaches the type's own quirk list to every
preview so a write can't be reviewed without it. Added: verb-form
enforcement for `gate`/`jalousie`, the corrected `valve` vocabulary,
`blinds` inverted 0=open/100=closed scale, hex-only type rejection,
fault-state warning, and the sequence rules above.

**Bug reporting.** New `report_bug` tool composes a redacted GitHub issue
and returns a prefilled link for the user to review and submit themselves.
It posts nothing and needs no token — filing publishes text under someone's
name, so a human sees it first. API keys, serials, hostnames and object
names are stripped automatically and listed back. Issue templates added for
manual reports.

**Publishing.** `tools/publish.py` builds a clean tree from the private
working copy, replacing controller identifiers and refusing to finish if
any survive.

## 0.8.0 Beta — 2026-08-18

First feature-complete pass. Read, watch, and write implemented and
verified live.

**Connection & keys** — `project_keys.json` registry (git-ignored); CLI
`add`, `auth`, `list`, `test`, `devices`, `remove`, `allow-write`, `serve`;
tools `list_objects`, `object_add`, `object_set_key`, `object_remove`,
`check_connection`.

**Reading** — `list_devices` (filterable), `get_device`.

**Documentation on demand** — `get_docs()` for the type overview or one
type's full detail, served from the device-type knowledge base, plus
standing user preferences on every call. `add_docs_note` and
`add_preference` let findings survive the session.

**Watching** — `watch_start` / `watch_read` / `watch_stop` / `watch_list`,
non-blocking status diffing over a kept-open subscription, with a 2-minute
keepalive so a watch survives the controller's ~5-minute idle timeout
(verified to 6.5 minutes).

**Writing** — `allow_write` per controller, CLI-only; two-phase
`set_device` → `confirm_set` with write-then-verify; `validate.py`
pre-flight checks.
