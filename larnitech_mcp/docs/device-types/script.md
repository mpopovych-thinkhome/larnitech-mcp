Digest of this file lives in [device_types.md](_device_types.md#script) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Script

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `path` | string | path to script file, relative to server folder | required* | — |
| `body` | string | script contents inline (instead of `path`) | required* | — |
| `type` | — | fixed | optional | `"script"` |
| `name` | string | script instance identifier | optional | any |
| `addr` | string | memory address reference | optional | e.g. `"125:150"` |
| `NAME` | string | parameters sent to the script (custom, name varies per script) | optional | — |

Either `path` or `body` is required, not both.

## API

- `state`: on/off (per the general device-types table; not separately
  reconfirmed live for this specific type)

## Script

Status values: `0x00` off, `0x01` on, `0xFF` toggle.

## Notes

Represents an Imerel script instance as a device — distinct from the
per-device-type `.md` files in this folder, which document the *targets*
scripts control, not scripts themselves. For script authoring patterns see
separate script-authoring notes.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
