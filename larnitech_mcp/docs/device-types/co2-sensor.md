Digest of this file lives in [device_types.md](_device_types.md#co2-sensor) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/CO2-sensor

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | e.g. `"333:10"` |
| `name` | string | device identifier | — | any |
| `type` | — | fixed | — | `"co2-sensor"` |
| `warning-level` | integer | warning message level (0 disables) | 1500 | ppm |
| `emergency-level` | integer | emergency message level (0 disables) | 2000 | ppm |
| `value-min` | integer | min indication-bar value | 0 | — |
| `value-max` | integer | max indication-bar value | 5000 | — |

```xml
<item addr="333:10" name="CO2" type="co2-sensor" warning-level="1200" emergency-level="1500"/>
```

## API

- `state`: integer, ppm (read-only, no write documented)

## Script

Status (2 bytes): bytes 0-1 = CO2 level, integer ppm.

## Notes

Read-only sensor — no write operations documented anywhere.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) (2026-08-18) Confirmed live via direct status-set on a virtual co2-sensor (1:219, stand a1b2c3d4): write {"state": 850} was rejected — acknowledged=false, value stayed at its prior reading (0). Confirms the "read-only, no write path documented" assumption: this type cannot be driven from the API2 client side at all, only from a Larnitech-side script (setStatus).
- (2026-09-02) Confirmed live on 38 co2-sensors, object "school installation": status key is `state`, not `current-co2` as previously documented.

## Known bugs

None recorded yet.
