Digest of this file lives in [device_types.md](_device_types.md#light-scheme) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Light-scheme

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | `"100:100"` |
| `name` | string | device identifier | — | any |
| `type` | — | fixed | — | `"light-scheme"` |
| `system` | boolean | system device flag | — | `yes`/`no` |
| `image` | string | icon reference | — | e.g. `lamp` |

`<contains>` child element (one per slave device):

| Attribute | Type | Description |
|---|---|---|
| `addr` | number, 1..2048 | executive device ID |
| `state` | number | status sent to the executor on activation |
| `state-rev` | number | status sent on deactivation (only meaningful for `ls-type=3`) |

`<automation>` child element:

| Attribute | Description |
|---|---|
| `door-sensors` | sensor address reference |
| `enabled` | automation active flag |
| `illumination-level` | light intensity threshold |
| `time-interval` | duration, seconds |
| `type` | automation mode, e.g. `"on-by-door"` |

**`ls-type` is not documented on the official page at all** ("no specific
meanings for ls-type parameters" — vendor page limitation, not something to
fix here since it isn't ours to edit). The meanings below come entirely
from live testing, not the vendor.

## API

`status.state` (on/off) is identical in shape across every `ls-type` value
— the behavioral difference is entirely controller-side, not visible in the
status shape itself. `ls-type` itself **does not come through the API at
all** (neither `get-devices` nor events) — only present in the XML config.

`ls-type` meanings (live-tested, not vendor-documented):
- `0` — impulse scene: defaults off, activation applies the configured
  status to slaves, no feedback
- `1` — impulse with feedback: on only while slaves match the configured
  status, otherwise off
- `2` — activation only: has feedback, but the controller ignores
  deactivation/`turn_off`
- `3` — like `0`, but status is configured separately for both activation
  and deactivation (`state`/`state-rev` on `<contains>`)
- `4` (master-slave) — not a scene at all: behaves like a normal widget of
  its own type (lamp/dimmer/RGB), just mirrors its status to slaves

## Script

Not documented at byte level — `light-scheme` state propagation is
controller-internal, not a script-readable status format in the usual
sense.

## Notes

This is a case where our own live testing documents more than the vendor
wiki does — `ls-type` behavior is entirely undocumented upstream.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
