Digest of this file lives in [device_types.md](_device_types.md#percent-sensor) — keep both in sync.

## XML attributes

No vendor wiki page (`wiki.larnitech.com/Percent-sensor` → 404). Observed
in a live controller config:

```xml
<item addr="5:95" cfgid="88" hw="cpu-usage" name="CPU usage"
      system="yes" type="percent-sensor"/>
```

| Attribute | Description |
|---|---|
| `type` | fixed, `"percent-sensor"` |
| `addr` / `name` | as usual |
| `hw` | names the internal metric the controller feeds in — seen: `cpu-usage` |
| `system` | `"yes"` on the observed device — an internal widget, not a user control |

Neither `hw` nor `system` is exposed through API2 — see
[BUG-006](../bugs.md#bug-006). From the API alone this looks like an
ordinary sensor; only the XML says it is controller self-telemetry.

## API

Read-only. Status is a single `state` value:

```json
{"state": 768}
```

**The value is not a percent, despite the type name.** Confirmed live on
`5:95` (demo case, `hw="cpu-usage"`) across three polls six seconds apart:
`768`, `256`, `0`. A percent cannot be 768.

Every observed value is an exact multiple of 256, which points at a raw
two-byte encoding with the integer part in the high byte — the same shape
`temperature-sensor` uses. On that reading the three samples are 3%, 1% and
0%, which matches an idle controller. **Treat the ÷256 scaling as the
leading hypothesis, not established fact:** it rests on three samples from
one device, all of which happened to be whole numbers, so a fractional part
has never actually been observed.

What is certain: do not present `state` to a user as a percentage without
scaling it, or an idle CPU reads as "768%".

## Script

Not documented. Presumably written with `setStatus` like the other scalar
sensor widgets, encoding unconfirmed.

## Notes

One of a family of generic scalar readouts — see also
[float-sensor](float-sensor.md) and [current-sensor](current-sensor.md) —
that differ from each other in how the app formats the number rather than
in what they measure. The `hw` attribute, not the type, says what the value
actually is.

<!-- Add live-tested quirks here as found. -->

## Known bugs

None recorded yet.
