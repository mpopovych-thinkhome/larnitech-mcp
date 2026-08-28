Digest of this file lives in [device_types.md](_device_types.md#vent) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Vent

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | e.g. `"201:50"` |
| `name` | string | device identifier | — | any |
| `type` | — | fixed | — | `"vent"` |
| `automation` | string | active automation mode | — | preset name |
| `cfgid` | number | configuration ID | — | numeric |
| `co2-sensors` | list | CO2 sensors used for automation | — | sensor addresses |
| `undefined-behavior` | choice | fallback position without sensor data | `"last"` | `0-250`, `on`, `off` |
| `P0` | number | minimal power for turning fan on | `"last"` | 0-100 |
| `limit-fan` | number | max fan power | — | 0-250 |
| `ctrl-change1` | number | min power-change step per `ctrl-ticks` | 5 | 0-250 |
| `ctrl-change2` | number | alternative power-change step | — | 0-250 |
| `ctrl-ticks` | number | timeout for `ctrl-change1` | — | 0-3825 |
| `alg` | string | control algorithm | — | `eco`, `fast`, `boost` |

## API

Live-tested status: `{"state": "off"/"on", "fan": 0.0}`.

- `fan` is a **number**, 0-100, analogous to `level` on a dimmer — unlike
  [virtual/ventilation](ventilation.md), where `fan` is a string preset.
  Same key name, two different value types by `type` — check `type` before
  assuming shape.

## Script

Byte 6 — current fan level (0-250), power output.

Write: 1 byte (on/off/toggle: 0, 1, 0xFF) or 2 bytes (byte0 state, byte1
power level 0-250).

## Notes

Do not confuse with [virtual/ventilation](ventilation.md) — same-sounding
name, different type, different `fan` value shape.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) **Resolves the earlier "fan didn't take on immediate verify" note — it is a real quirk, not latency.** Confirmed on `1:102`, including via the proper subscribe-and-wait-for-push confirmation flow (not just an immediate read): **`fan` is ignored whenever it is set in the same `status-set` call as `state`.** `{"state": "on", "fan": 30}` in one call applies `state` only — the push event confirms `state: on` but `fan` stays at its old value. Setting `fan` **alone**, in a separate call, once `state` has already settled, works and is confirmed correctly (`fan: 30.0` applied). Practical rule: write `state` and `fan` as two separate `set_device`/`confirm_set` round trips, state first.
- (2026-08-18) **`fan` holds its last value after `state` goes to `off` — it does not reset to 0.** Confirmed live on `1:102`: after stopping the unit, `status` still read `{"state": "off", "fan": 30.0}` (last-used speed, not 0). A non-zero `fan` alone is therefore **not** a "currently moving air" signal — always check `state` too, not just `fan > 0`.
- (2026-08-18) Same automation-reset-then-off-write pacing quirk as [valve-heating](valve-heating.md#notes) applies here too, confirmed live on `1:102`: clearing `automation` (to drop a named preset back to manual) and setting `state: "off"` must be two calls ~1s apart, not one combined write or two rapid ones — otherwise `automation` clears but `state` stays on. Writing `automation: ""` alone is confirmed working — the key disappears from `status` on the next read, taking `target` (the CO2 setpoint) with it.

## Known bugs

None recorded yet.
