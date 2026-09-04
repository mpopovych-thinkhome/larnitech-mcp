Digest of this file lives in [device_types.md](_device_types.md#climate-control) — keep both in sync.

## XML attributes

No dedicated page found under `wiki.larnitech.com` for a `climate-control`
type (the official `/Xml` index does not list it separately — it may be
covered generically or under a different name). Not documented here until
found — do not invent attributes.

## API

- `state` — on/off
- `setpoint-heat` — float, °C
- `setpoint-cool` — float, °C
- `current-temperature` — float, °C
- `current-humidity` — float, %
- `pid-temperature` — heat demand, 0-100%. `100` = zone calling for maximum
  heat and not reaching setpoint.
- `mode` — string, exactly `"heat"` / `"cool"` / `"auto"` (confirmed live
  2026-08-18 by writing all three directly and re-reading via a fresh
  `status-get`) — a **smaller** lexicon than `AC`/`fancoil`'s `mode` (no
  `dry`/`fan`). `"auto"` is the specific unconstrained sentinel, not just
  "key absent" — see the gating note below.

## Script

Not documented — no confirmed byte-level layout for this type yet.

## Notes

Appears in `get-devices` as a distinct API2 `type` from `AC`/`fancoil`, used
for generic HVAC/climate zones. Exact relationship to `valve-heating` and
`fancoil` (which have their own richer XML/automation model) is unclear —
possibly `climate-control` is a script-defined virtual climate widget rather
than a vendor-fixed hardware type. Confirm with a live device before adding
more here.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) The optional `mode` key constrains what the *currently active automation* is allowed to do, it does not select a mode on its own. If the active automation supports both heating and cooling, setting `mode` (e.g. `heat`) restricts it to just that one. If the active automation does not support the requested mode at all (e.g. `mode: heat` while the automation can only cool), the zone does nothing and carries no setpoint — behaviour is capability-gated by the automation, not by `mode` itself. `mode` is absent unless explicitly constrained.

- (2026-08-18) **Setpoint keys behave differently in snapshots vs events.** On `1:250`, `setpoint` (bare — itself undocumented) and `setpoint-heat` moved together in `statuses` events, and `pid-temperature` appeared there too (`0 -> 29`), yet a `get-devices status=detailed` snapshot taken minutes later contained none of them — only `{state, current-temperature, automation, mode, time-interval}`. Unresolved: whether snapshots never carry setpoints for this type, or whether it depends on the active automation preset (the preset switched to `Summer` during the same observation). Re-check with a non-summer preset before relying on either reading.

- (2026-08-18) `status.time-interval` (int, observed `0`) is returned but is not documented anywhere — meaning unknown, needs investigation.

- (2026-08-18) Uses the named-preset scheme previously documented only for `valve-heating`/`fancoil`: `status.automation` (`"Summer"`) plus a device-level `automations` list (`['Winter', 'Midseason', 'Summer']`). Switching presets was observed live as an `automation` change event.

- (2026-08-18) `modes` arrives as a **list of strings** (`['cool']`) at device level, not as a hex bitmask string like `ac`/`conditioner` use for the same key name. Check the type before parsing it. Observed live on `1:250`.

- (2026-08-18) **Write is a plain, single `status-set` — no ordering/pacing quirk, unlike `valve-heating`/`fancoil`/`vent`.** Confirmed live on `1:250`: `{"mode": "cool"}` alone, and `{"state": "on", "mode": "heat"}` combined, both apply cleanly and immediately — verified via a fresh `status-get` (not just the push ack) after each. Writing `mode: "auto"` produces **both** `setpoint-heat` and `setpoint-cool` simultaneously when the active automation supports both (confirmed by switching the active automation to one with `modes: ["heat","cool"]`) — this is the mechanism behind the "unconstrained" behavior described above, not a separate key-deletion trick.

## Known bugs

- Automation-preset switch leaves the previous preset's outputs on — [BUG-010](../bugs.md#bug-010)
