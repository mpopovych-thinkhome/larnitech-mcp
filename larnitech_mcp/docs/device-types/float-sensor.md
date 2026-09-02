Digest of this file lives in [device_types.md](_device_types.md#float-sensor) — keep both in sync.

## XML attributes

No vendor wiki page (`wiki.larnitech.com/Float-sensor` → 404). Observed in
a live controller config:

```xml
<item addr="5:96" cfgid="88" hw="cpu-load" name="CPU load"
      system="yes" type="float-sensor"/>
```

| Attribute | Description |
|---|---|
| `type` | fixed, `"float-sensor"` |
| `addr` / `name` | as usual |
| `hw` | names the internal metric the controller feeds in — seen: `cpu-load` |
| `system` | `"yes"` on the observed device — an internal widget, not a user control |

Neither `hw` nor `system` is exposed through API2 — see
[BUG-006](../bugs.md#bug-006).

## API

Read-only. Status is a single `state` value:

```json
{"state": 23}
```

Confirmed live on `5:96` (demo case, `hw="cpu-load"`) across four polls:
`17`, `23`, `20`, `35`. The value moves, so it is live telemetry rather
than a static configured number.

**Despite the type name, every observed value was an integer.** The type
appears to describe how the app *renders* the number — with a fractional
part — rather than what arrives on the wire, so a scaling factor is
implied. Unlike [percent-sensor](percent-sensor.md), the values here are
not multiples of 256, so whatever the factor is, it is a different one.
Divided by 100 the samples read 0.17-0.35, which would be an ordinary
load average for a lightly loaded controller — **plausible, unverified,
and not to be relied on.**

What is certain: `state` is a raw number whose scale is not established.
Do not present it as a final value without knowing what the `hw` metric is.

## Script

Not documented.

## Notes

One of a family of generic scalar readouts — see also
[percent-sensor](percent-sensor.md) and [current-sensor](current-sensor.md).
They differ in display formatting rather than in subject matter; the `hw`
attribute is what says which quantity a given instance carries, and it is
XML-only.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
