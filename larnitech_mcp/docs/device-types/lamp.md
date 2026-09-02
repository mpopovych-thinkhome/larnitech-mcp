Digest of this file lives in [device_types.md](_device_types.md#lamp) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Lamp_element

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | required | `"XXX:XX"` |
| `name` | string | device identifier | required | any |
| `type` | — | fixed | required | `"lamp"` |
| `sub-type` | enum | device variant | optional | `damper`, `air-fan`, `socket`, `lock`, `dehumidifier`, `closing-switch`, `valve-3`, `pump` |
| `auto-period` | integer | automation period | optional | seconds, default 600 |
| `system` | boolean | system device flag | optional | `yes`/`no` |
| `image` | string | UI icon identifier | optional | e.g. `pump` |
| `virtual` | — | script-tracked widget | — | `yes` |

## API

- `state`: on/off
- `auto-state`: boolean, present on plain (no sub-type) lamps

Sub-type behavior confirmed live:
- **`lock`** — polarity is inverted: `state=off` means "locked". Do not
  assume intuitive "on = locked".
- **`closing-switch`** ("impulse closer" per description) — behaves in
  practice as a normal persistent on/off switch, not an impulse/momentary
  output.

## Motion automations (`<automation>`)

Lighting widgets can carry `<automation>` children that switch them by
motion. The same model applies to [dimmer-lamp](dimmer-lamp.md),
[rgb-lamp](rgb-lamp.md) and [light-scheme](light-scheme.md) — documented
here once.

```xml
<item addr="302:1" type="lamp" name="Lamp" auto-period="10">
    <automation type="on-by-moving"  enabled="yes" motion-sensors="3:30"
                motion-level="20" illumination-level="10"
                time-interval="3" time-interval2="1"/>
    <automation type="off-by-moving" motion-level="15" motion-sensors="3:30"
                time-interval="5"/>
    <automation type="off-by-door"   delay="3" motion-level="15"
                time-interval="5"/>
</item>
```

| Rule `type` | Effect |
|---|---|
| `on-by-moving` | switch on when motion is seen |
| `off-by-moving` | switch off once motion stops |
| `off-by-door` | switch off on a door event, after `delay` |

| Attribute | Meaning |
|---|---|
| `motion-sensors` | address of the [motion-sensor](motion-sensor.md) feeding the rule |
| `motion-level` | threshold on that sensor's continuous reading |
| `illumination-level` | only act when darker than this — seen on `on-by-moving` only |
| `time-interval`, `time-interval2` | hold/re-trigger intervals, seconds |
| `delay` | `off-by-door` only |
| `enabled` | `yes`/`no` — a rule can be switched off without deleting it |

A widget commonly carries several: the example above has three. Switch-on
and switch-off thresholds differ deliberately (20 vs 15) — hysteresis, so
the light does not flicker at the boundary.

**None of this is visible through API2.** No rule, threshold or sensor
binding appears in `get-devices`; the only trace is the boolean
`auto-state` in the widget's status, which says automation is active but
nothing about what it does. So when a light changes by itself, the API
cannot explain why — read the XML config for that. Same category as
`ls-type` on `light-scheme` and the `system` attribute
([BUG-006](../bugs.md#bug-006)).

## Script

Status byte (1 byte):
- bit0 — power (0 off, 1 on)
- bit3 — automation (0 disabled, 1 enabled)
- bit7 — alarm (0 none, 1 active)

`setStatus(WGT_LAMP, {state})` — 0 off, 1 on, 0xFF toggle.

```xml
<additem type="lamp" sub-type="pump" virtual="yes" name="..."/>
```

## Notes

Generic on/off indicator widget — used for pumps, valves, relays, locks,
and switches via `sub-type`. `sub-type` changes semantics, not just the UI
icon (see `lock`/`closing-switch` above) — never assume a sub-type behaves
like plain on/off without checking here first.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
