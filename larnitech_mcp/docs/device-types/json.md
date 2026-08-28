Digest of this file lives in [device_types.md](_device_types.md#json) — keep both in sync.

## XML attributes

Not yet pulled from the vendor wiki — add when needed.

## API

`type="json"` devices send a `status` value that is itself a JSON object,
subject to the doubled-brace protocol quirk documented in
[api2_protocol.md](../api2_protocol.md#common-quirks-all-commands)
(`"status":{{...` — must be fixed to `"status":{"_raw":{...` before
`json.loads`, or the whole frame fails to parse). The `_raw` wrapper key
below is that fix's artifact, not part of Larnitech's own wire format.

Behavior is fully dependent on `sub-type` — no fixed shape beyond "a JSON
object". Two sub-types confirmed live 2026-08-21:

### `sub-type="btunreg"`

Confirmed on object `a1b2c3d4`, addr `900:1` — a raw/empty diagnostic
aggregate:
```json
{"CAN810": {"0": {}, "1": {}}}
```
No stable schema observed. **Treat as a controller-internal diagnostic
blob, not meant to be consumed generically.**

### `sub-type="MBUS"`

Confirmed on object `b2c3d4e5` ("live installation"), addrs `900:1`,
`900:2`, `900:3` — two Axioma heat/cooling-load meters and one Apator
water meter. Self-describing structure, genuinely useful:

```json
{
  "_raw": {
    "0": 945032504.0, "1": 16842752.0, "2": 67108864.0,
    "descr": {
      "0": {"typ": "Time Point, time & date"},
      "1": {"func": "During error", "typ": "Time Point, time & date"},
      "5": {"dim": "Wh", "typ": "Energy"},
      "7": {"dim": "m3", "typ": "Volume"},
      "8": {"dim": "W", "typ": "Power"},
      "10": {"dim": "C", "typ": "Flow Temperature"},
      "12": {"dim": "K", "typ": "Temperature Difference"}
    },
    "hr": "3080310:AXI:11:Heat / Cooling load meter:37:16:0"
  }
}
```

**Shape (Larnitech's own, minus the `_raw` brace-fix wrapper):** top-level
status is one JSON object whose keys are stringified small integers
(`"0"`, `"1"`, `"2"`...) mapping to the meter's data values, plus:
- `"descr"` — object, same numeric-string keys, giving each field's metadata
- `"hr"` — string, a compact colon-separated model/serial identifier

**`descr` entry fields (per numeric key):**
- `typ` — human name, e.g. `"Energy"`, `"Volume"`, `"Flow Temperature"`,
  `"Fabrication No"`, `"Error flags (binary)"`, `"Time Point, time & date"`.
  Also seen: `"MA"`, `"MB"`, `"MC"`, `"M0"` — short codes, unexplained, do
  not guess their meaning.
- `dim` — optional, unit string: seen `Wh`, `m3`, `W`, `C`, `K`, `m3/h`,
  `seconds`, `days`.
- `func` — optional qualifier string, only ever seen as `"During error"`.
- `stor` — optional integer, seen as `1`; meaning unconfirmed (possibly
  "stored/previous reading slot" vs. current).

**`typ` is not a unique field identifier.** One meter had "Time Point, time
& date" at both key `"0"` and key `"1"` (the second with
`func: "During error"`), and "Energy" appeared at two different keys. **The
numeric key is the only stable identifier for a field.**

`dim: "K"` (Kelvin) is used specifically for a *temperature-difference*
field (flow-minus-return delta), not an absolute temperature — the two
absolute-temperature fields on the same meter use `dim: "C"`.

Some fields legitimately have no `dim` at all — serial numbers, raw
timestamps/epoch-like large integers, bitmask-looking "Error flags
(binary)" values, and the unexplained `MA`/`MB`/`MC`/`M0` codes. Not every
field is a real physical measurement.

Two-value "On Time" and "Operating Time" fields are cumulative
device-uptime counters (seconds or days depending on the meter) — how to
*display* them is an HA-integration-side choice, not prescribed here.

One live example (`descr` for the Apator meter) had an extra top-level
`descr` key:
```json
"descr": {"ERROR": "PARSER ERROR"}
```
meaning the controller itself failed to fully decode part of that MBUS
packet. Surface this, don't silently drop it.

## Script

Not documented.

## Notes

**Reliability quirk, confirmed live 2026-08-21 — flag prominently:** an
MBUS meter that doesn't answer a given poll cycle returns **every** field
as `null`, including `descr` and `hr` themselves being `null` (not merely
absent or empty), rather than omitting the response or keeping stale
values. Which of several meters goes quiet on a given poll appears to
rotate/vary. **Anything consuming this data must treat a fully-null
payload as "no data this cycle," not as an error or as "value is actually
zero."**

<!-- Add live-tested quirks here as found. -->

- (2026-08-21) `btunreg` and `MBUS` sub-type shapes confirmed live on two
  different objects — see API above.

## Known bugs

None recorded yet.
