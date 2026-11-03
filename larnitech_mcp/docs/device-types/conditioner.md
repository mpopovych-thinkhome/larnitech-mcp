<a id="conditioner"></a>

Index entry (status keys and issue titles only): [_device_types.md](_device_types.md#conditioner) — keep those in sync.

## XML attributes

Source: https://wiki.larnitech.com/Conditioner

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"conditioner"` |
| `addr` | string | device address | — | — |
| `name` | string | device identifier | — | — |
| `path` | string | path to script (required) | — | — |
| `script-id` | string | script identifier for interface | — | — |
| `IRT` | string | infrared temperature sensor address | — | — |
| `t-min` | number | minimum temperature setpoint | 16 | integer |
| `t-delta` | number | temperature adjustment range | 16 | integer |
| `modes` | bitmask, 5 bits | operation mode availability | `0x1F` | bit0 fan, bit1 cool, bit2 dry, bit3 heat, bit4 auto |
| `funs` | bitmask | airflow mode options — **named `funs`, not `fans`** (vendor typo, real attribute name) | `0x0F` | auto, 1, 2, 3, 4, 5, silent |
| `vane-ver` | bitmask | vertical fins positioning | `0x7F` | (positions, per vendor page) |
| `vane-hor` | bitmask | horizontal fins positioning | `0x7F` | (positions, per vendor page) |
| `temperature-sensors` | list | temperature sensor references | — | — |
| `CONDID` | string | conditioner control identifier | — | — |
| `IRID` | string | IR device address | — | — |

`conditioner` with a `fans=` attribute (instead of `funs=`) silently ignores
it and falls back to the default mask.

## API

- `modes` — **reads back as `0x1F` (all modes) regardless of the XML
  value** — [BUG-002](../bugs.md#bug-002). Unlike `AC`, this bug affects
  `conditioner` specifically; treat `modes` as always the full default set.
- `funs` — **never returned** via API regardless of XML config —
  [BUG-001](../bugs.md#bug-001) — always assume default `0x0F`.
- `fan` / `state` — same string-enum behavior as [ac](ac.md) is assumed but
  not yet separately confirmed live on a `conditioner`-typed device.

## Script

Status written from a script — 5 bytes, used by production scripts
(`scripts/ready-scripts/state-restore/RestoreStatus_Cond_16pcs`, NEST support script):

- byte 0 — `(mode<<4) + state`: bit0 on/off, bits 4-7 mode
- byte 1 — setpoint as **°C − 16** (16…31 °C → 0…15; **differs from `AC`**, where byte 2 holds plain °C). Confirmed live 2026-10-19: writing `20` showed `target: 36`. The NEST support script writes `0` for the lowest setpoint
- byte 2 — 0
- byte 3 — vanes
- byte 4 — fan speed

```c
// cool, on, 22 C, keep vanes, fan speed 2
u8 st[9];
getStatus(@id:@sid, &st, 9);
setStatus(@id:@sid, {(1<<4) + 1, 22 - 16, 0, st[3], 2}, 5);
```

`getStatus` of a conditioner on another module works only if the script also has a `V-ID` handler for it — see the script-language notes.

Operation modes byte (bits 4-7), same numbering as `AC`:
- 0 fan, 1 cool, 2 dry, 3 heat, 4 auto

The vendor wiki speaks of a 6-byte status (power, temperature, vanes,
airflow); the 6th byte is not used by the scripts above.

## Notes

Distinct API2 `type` from `AC`, but shares most of the XML attribute shape
and the same class of masking bugs. The vendor's own wiki misspells the fan
mask attribute as `fans` on the `AC` page and `funs` on this page — `funs`
is the one that actually works for `conditioner`.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) Confirmed live on `1:214`: status is `{state, target, current, fan, mode, vane-hor, vane-ver}` with `fan` a string (`"high"`) and `vane-*` ints (current position), matching `ac`. Device-level `modes` read back `'0x1F'` (BUG-002 reproduced) and no `funs` key was returned at all (BUG-001 reproduced).

## Known bugs

- [BUG-001](../bugs.md#bug-001) — `funs` mask never returned via API2
- [BUG-002](../bugs.md#bug-002) — `modes` returned as if no mask were set
