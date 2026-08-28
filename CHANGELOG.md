Every change bumps the version here and gets an entry — agreed before it
lands, not after.

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
