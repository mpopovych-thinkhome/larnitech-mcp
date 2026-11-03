<a id="climate-control"></a>

Index entry (status keys and issue titles only): [_device_types.md](_device_types.md#climate-control) — keep those in sync.

## XML attributes

No vendor page. Taken from production configs exported off a controller (2026-10-14) — the
shape the controller itself writes:

```xml
<item addr="117:250" type="climate-control" name="..." automation="Winter" hw="def='last'"
      warm-floor-sensors="119:5">            <!-- or temperature-sensors="117:34;117:35" -->
    <automation name="Winter" setpoint-heat="25" setpoint-cool="27" setpoint-warm-floor="26"
                setpoint-dry="80" setpoint-humidify="50" setpoint-co2="1000">
        <alg preset="default"/>
        <device addr="117:3"><warm-floor range="0-100"/></device>   <!-- or <heat range="0-100"/> -->
    </automation>
    <automation name="Summer" ...>
        <alg preset="default"/>
        <device addr="103:5"><warm-floor range="0-100"/></device>
    </automation>
</item>
```

- Each automation lists its own output devices — one zone can drive different circuits per preset (water floor in Winter, electric mat in Summer).
- A driven `valve-heating` carries `climate-control="<climate addr>"` and no `automation` attribute of its own (the climate drives it); a circuit used only in another preset stays in manual mode. Leaving it in `always-off` blocks the climate from switching it on.
- `state` is not part of the XML: a climate-control added by importing a config comes up **off** and has to be switched on.

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
- `setpoint-warm-floor` / `current-warm-floor` / `pid-warm-floor` — the same three for a zone with `warm-floor-sensors`.

## Script

No byte-level layout. Driven from a script through the server: automation by name via `SRV-ID:102`, setpoints via a `status-set` request on `SRV-ID:108` — see separate notes on script requests to the server.

## Notes

Appears in `get-devices` as a distinct API2 `type` from `AC`/`fancoil`, used
for generic HVAC/climate zones. Exact relationship to `valve-heating` and
`fancoil` (which have their own richer XML/automation model) is unclear —
possibly `climate-control` is a script-defined virtual climate widget rather
than a vendor-fixed hardware type. Confirm with a live device before adding
more here.

<!-- Add live-tested quirks here as found. -->

- (2026-10-14) **Warm-floor zones report their own keys:** `setpoint-warm-floor`, `current-warm-floor` (floor probe from `warm-floor-sensors`) and `pid-warm-floor` (0-100 demand), instead of the `-temperature` set. Seen live on five zones; a zone switched on reacted within a second (`pid-warm-floor` 0 → 13, its water circuit turned on).
- (2026-10-14) **Snapshots do carry setpoints in a heating preset.** With `Winter` active (`setpoint-heat` in the preset), `list_devices` returned `setpoint` and `setpoint-heat` — so the 2026-08-18 "snapshots never carry setpoints" reading depends on the preset, as suspected below.
- (2026-10-14) **`setpoint-heat` via a script `status-set` (`SRV-ID:108`) and automation by name via `SRV-ID:102` confirmed live** — preset `Winter` ↔ `Summer` switched back and forth, `setpoint-heat` followed the master each time. `state` and `setpoint-warm-floor` through the same request are written by a production script but not yet verified.

- (2026-08-18) The optional `mode` key constrains what the *currently active automation* is allowed to do, it does not select a mode on its own. If the active automation supports both heating and cooling, setting `mode` (e.g. `heat`) restricts it to just that one. If the active automation does not support the requested mode at all (e.g. `mode: heat` while the automation can only cool), the zone does nothing and carries no setpoint — behaviour is capability-gated by the automation, not by `mode` itself. `mode` is absent unless explicitly constrained.

- (2026-08-18) **Setpoint keys behave differently in snapshots vs events.** On `1:250`, `setpoint` (bare — itself undocumented) and `setpoint-heat` moved together in `statuses` events, and `pid-temperature` appeared there too (`0 -> 29`), yet a `get-devices status=detailed` snapshot taken minutes later contained none of them — only `{state, current-temperature, automation, mode, time-interval}`. Unresolved: whether snapshots never carry setpoints for this type, or whether it depends on the active automation preset (the preset switched to `Summer` during the same observation). Re-check with a non-summer preset before relying on either reading.

- (2026-08-18) `status.time-interval` (int, observed `0`) is returned but is not documented anywhere — meaning unknown, needs investigation.

- (2026-08-18) Uses the named-preset scheme previously documented only for `valve-heating`/`fancoil`: `status.automation` (`"Summer"`) plus a device-level `automations` list (`['Winter', 'Midseason', 'Summer']`). Switching presets was observed live as an `automation` change event.

- (2026-08-18) `modes` arrives as a **list of strings** (`['cool']`) at device level, not as a hex bitmask string like `ac`/`conditioner` use for the same key name. Check the type before parsing it. Observed live on `1:250`.

- (2026-08-18) **Write is a plain, single `status-set` — no ordering/pacing quirk, unlike `valve-heating`/`fancoil`/`vent`.** Confirmed live on `1:250`: `{"mode": "cool"}` alone, and `{"state": "on", "mode": "heat"}` combined, both apply cleanly and immediately — verified via a fresh `status-get` (not just the push ack) after each. Writing `mode: "auto"` produces **both** `setpoint-heat` and `setpoint-cool` simultaneously when the active automation supports both (confirmed by switching the active automation to one with `modes: ["heat","cool"]`) — this is the mechanism behind the "unconstrained" behavior described above, not a separate key-deletion trick.

## Known bugs

- Automation-preset switch leaves the previous preset's outputs on — [BUG-010](../bugs.md#bug-010)
