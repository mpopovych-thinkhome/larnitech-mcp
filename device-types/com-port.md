Digest of this file lives in [device_types.md](_device_types.md#com-port) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Com-port

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | e.g. `"595:18"` |
| `name` | string | device identifier | — | e.g. `"RS232"` |
| `type` | — | fixed | — | `"com-port"` |

```xml
<item addr="595:18" name="RS232" type="com-port"/>
```

Minimally documented page — no defaults, no further attributes, no
byte-level status info given by the vendor.

## API

No status key documented — this type represents an RS232/serial port
reference, not a device with a readable status.

## Script

Not documented.

## Notes

Thin type — mostly used as a `devices-list filter="com-port"` selector
target in script XML settings (see
the vendor's XML config documentation),
not as a device with meaningful status of its own.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
