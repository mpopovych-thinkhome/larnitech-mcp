Digest of this file lives in [device_types.md](_device_types.md#fancoil) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Fancoil

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"fancoil"` |
| `addr` | string | device address | — | e.g. `"201:50"` |
| `name` | string | device identifier | — | any |
| `automation` | string | active automation mode | — | preset name |
| `cfgid` | string | configuration ID | — | numeric |
| `temperature-sensors` | list | sensor addresses for automation | — | — |
| `valve-heating` | address | heating valve address | — | device address |
| `valve-cooling` | address | cooling valve address | — | device address |
| `temperature-lag` | number | hysteresis margin | 0.5 | decimal |
| `undefined-behavior` | choice | fallback behavior | `"last"` | `0-250`, `on`, `off`, `last` |
| `P0` | number | minimal power for turning fan on | `"last"` | 0-100 |
| `mode` | choice | operating mode | `"heat"` | `heat`, `cool` |
| `alg` | string | control algorithm | — | `eco`, `fast`, `boost` |
| `limit-fan` | number | max fan power | — | 0-250 |
| `ctrl-change1` | number | min power-change step per `ctrl-ticks` | 5 | 0-250 |
| `ctrl-change2` | number | alternative power-change step | — | 0-250 |
| `ctrl-ticks` | number | timeout for `ctrl-change1` | — | 0-3825 |

## API

Same automation scheme as [valve-heating](valve-heating.md): absent =
manual, `"always-off"` = reserved lockout, named presets carry `target`.
Status: `{"state","automation","target","current","fan","mode"}`.

- `mode` — string, `"heat"`/`"cool"`/... — same lexicon as `AC`/`climate-control`
- `fan` — **always** float 0-100%, **even on explicitly stepped hardware**:
  a device named "Fancoil 3sp" (3-speed) returned `66.4`, not an index or
  string. Physical step count appears to be a hardware/config detail that
  doesn't reach the protocol.
- `valve-heating="ADDR"` / `valve-cooling="ADDR"` XML attributes are **not
  visible via API2 in either direction** — neither the attributes on the
  `fancoil` device itself, nor a reverse reference on the valves they point
  to. Confirmed by directly querying `get-devices` on a `fancoil` with both
  attributes set in XML, and on the two valves it referenced. Same category
  as `light-scheme`'s `ls-type` — config-time only, not runtime.

## Script

7-byte status response: temperature setpoint/current (16-bit each),
automation index, fan level (0-250), 8 error flags.

`setStatus` formats:
- **1 byte:** 0 off, 1 on, 0xFF toggle
- **2 bytes:** status byte + power (0-250)

## Notes

Shares its automation-mode model wholesale with `valve-heating` — read that
file first if working on either type.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) **Switching `mode` between `heat`/`cool` needs a separate, spaced-out `state` write too — even independent of the automation/preset mechanism below.** Confirmed live on `1:213` via `watch_start`/`watch_read` (observing the raw `statuses` push stream, not just read-back): the moment `mode` changes, the controller reacts on its own by dropping `state` to `off` — reproduced twice in a row (`mode` change event, then a `state: on→off` event ~0.3-0.8s later, from the controller itself, not from us). A combined `{"mode": ..., "state": "on"}` write does not survive this — the controller's own reaction to the mode change lands *after* it. Working sequence: write `{"mode": ...}` alone, wait **~1s**, then write `{"state": "on"}` alone; the events trace confirms this second write is exactly what corrects the channel back on.
- (2026-08-18) Same automation-reset-then-off-write pacing quirk as [valve-heating](valve-heating.md#notes) applies here too, confirmed live on `1:213`: clearing `automation` and setting `state: "off"` must be two calls ~1s apart, not one combined write or two rapid ones — otherwise `automation` clears but `state` stays on.
- (2026-08-18, unconfirmed, needs follow-up) Writing `target` on a fancoil **with no active named automation** (`automation` absent) appeared to be silently ignored — `{"state": "on", "target": 24}` on `1:213` in Manual mode was acknowledged by the controller (confirmed via push) but a fresh `status-get` right after showed `state` applied and `target` NOT applied. Not investigated further — unclear whether `target` needs an active automation to mean anything on this type, or whether this is a separate write-ordering issue like the two above. Distinct from the already-known AC/conditioner `target=-128` bug (different type, different symptom) — do not conflate.

## Known bugs

None recorded yet.
