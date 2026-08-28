Digest of this file lives in [device_types.md](_device_types.md#ir-transmitter) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Ir-transmitter (vendor page is a stub,
last updated 2022-01-25)

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"ir-transmitter"` |
| `addr` | string | device address | — | e.g. `"147:16"` |
| `name` | string | device identifier | — | e.g. `"IR 147"` |

No defaults or further attributes documented — vendor page is minimal.

## API

No status key documented.

## Script

Status setting: "byte number 0..N contains transmit packet" — no further
byte-level breakdown given by the vendor.

## Notes

Vendor documentation is a stub. Nothing more to add until tested live or
until the vendor page is expanded.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
