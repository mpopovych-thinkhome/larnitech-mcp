Digest of this file lives in [device_types.md](_device_types.md#ir-receiver) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Ir-receiver

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"ir-receiver"` |
| `name` | string | device identifier | — | e.g. `"ir-recv"` |
| `addr` | string | device address | — | `"XXX:XX"`, e.g. `"145:21"` |

## API

No status key confirmed live — provisionally maps to the script bytes below.

## Script

Write (1 byte) — capture control:
- `0` — disable capture
- `1` — enable single-message capture

Read (1 byte) — capture state:
- `0` — capture off
- `1` — capture on
- other value — message received

Capture is not persistent — `1` must be written again each time to capture
another message (per vendor docs).

## Notes

Momentary/one-shot capture semantics — do not treat as a persistent
listening mode.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
