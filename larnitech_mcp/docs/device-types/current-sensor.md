Digest of this file lives in [device_types.md](_device_types.md#current-sensor) — keep both in sync.

## XML attributes

No vendor wiki page (`wiki.larnitech.com/Current-sensor` → 404). Observed
in a live controller config:

```xml
<item addr="302:90" cfgid="192" name="Current" system="yes"
      type="current-sensor"/>
```

| Attribute | Description |
|---|---|
| `type` | fixed, `"current-sensor"` |
| `addr` / `name` | as usual |
| `system` | `"yes"` on the observed device — an internal widget, not a user control |

No `hw` attribute here, unlike its siblings — the type alone says what the
quantity is. `system` is not exposed through API2, see
[BUG-006](../bugs.md#bug-006).

## API

Read-only. Status is a single `state` value:

```json
{"state": 0}
```

**Electrical current, in amperes.** The quantity is confirmed; the
encoding is not — the only observed device read `0` on every poll, so
neither a scaling factor nor a fractional form has ever been seen. Before
relying on a non-zero reading, check it against a known load: the sibling
types are known to carry raw values that need scaling
([percent-sensor](percent-sensor.md) returns multiples of 256 for what is
meant to be a percent), so a raw-value encoding here would be in keeping
with the family.

## Script

Not documented.

## Notes

One of a family of generic scalar readouts — see also
[percent-sensor](percent-sensor.md) and [float-sensor](float-sensor.md).
Unlike those two, this one names its quantity in the type rather than in
an `hw` attribute.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
