<a id="co2-sensor"></a>

Index entry (status keys and issue titles only): [_device_types.md](_device_types.md#co2-sensor) — keep those in sync.

## XML attributes

Source: https://wiki.larnitech.com/CO2-sensor

| Attribute         | Type    | Description                          | Default | Values          |
| ----------------- | ------- | ------------------------------------ | ------- | --------------- |
| `addr`            | string  | device address                       | —       | e.g. `"333:10"` |
| `name`            | string  | device identifier                    | —       | any             |
| `type`            | —       | fixed                                | —       | `"co2-sensor"`  |
| `warning-level`   | integer | warning message level (0 disables)   | 1500    | ppm             |
| `emergency-level` | integer | emergency message level (0 disables) | 2000    | ppm             |
| `value-min`       | integer | min indication-bar value             | 0       | —               |
| `value-max`       | integer | max indication-bar value             | 5000    | —               |

```xml
<item addr="333:10" name="CO2" type="co2-sensor" warning-level="1200" emergency-level="1500"/>
```

## API

- `state`: integer, ppm (read-only, no write documented)

## Script

Status (2 bytes): bytes 0-1 = CO2 level, integer ppm, **little-endian** — byte0 low, byte1 high.

Each element of a `{...}` status array is sent as its low byte only, so a value from a variable is split explicitly:

```c
setStatus(WGT_CO2, {co2%256, co2/256});   // 557 ppm -> {0x2D, 0x02}
```

`{co2*256, co2}` (seen in Brink V1.1) sends `{0, low}` → the widget shows `low*256` (557 ppm → 11520).

## Notes

Read-only sensor — no write operations documented anywhere.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) (2026-08-18) Confirmed live via direct status-set on a virtual co2-sensor (1:219, stand a1b2c3d4): write {"state": 850} was rejected — acknowledged=false, value stayed at its prior reading (0). Confirms the "read-only, no write path documented" assumption: this type cannot be driven from the API2 client side at all, only from a Larnitech-side script (setStatus).
- (2026-09-02) Confirmed live on 38 co2-sensors, object "school installation": status key is `state`, not `current-co2` as previously documented.
- (2026-10-12) Byte order confirmed live (WallPanel ISMA script, 3 virtual co2-sensors): `{v*256, v}` showed 11520 / 54016 / 46080 for 557 / 467 / 180 ppm = `low*256` each → status is little-endian, one byte per `{}` element.

## Known bugs

None recorded yet.
