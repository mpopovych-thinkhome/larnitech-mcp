Digest of this file lives in [device_types.md](_device_types.md#virtual) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Virtual

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | required | `"333:132"` |
| `name` | string | device identifier | required | any |
| `type` | — | fixed | required | `"virtual"` |
| `sub-type` | enum | device variant | required | see below |
| `length` | number | status size in bytes | required* | `0` = dynamic (text types), or byte count |
| `dim` | symbol | unit symbol appended to the value in-app | optional | e.g. `%`, `°C` |

Sub-types:
- `sensor` — numeric virtual sensor
- `text` — text sensor (UTF-8), `length` must be `0`
- `long-text` — scrollable text field (UTF-8), `length` must be `0`
- `lamp`, `dimer-lamp` [sic, vendor typo], `rgb-lamp`, `jalousie`, `gate`,
  `gate120`, `jalousie120` — devices that need a script to track status,
  behaving like their standalone counterparts but script-driven
- `prf` — formatted status set
- `sunrise` — sunrise/sunset event device
- `plan` — room-plan/floorplan image reference
- `ventilation` — see dedicated [ventilation](ventilation.md) page (own
  official wiki entry, distinct enough to warrant its own file)

## API

Fully dependent on `sub-type` — this type has no fixed status shape of its
own. Confirmed live 2026-08-20/21 on object `a1b2c3d4` ("test stand") for the sub-types below. See [ventilation.md](ventilation.md) for
`sub-type="ventilation"` (undisturbed by this update).

| sub-type | status shape | reliability |
|---|---|---|
| `sensor` | `{"state": <number>}` | confirmed live |
| `text` | `{"state": <string>}` | confirmed live |
| `long-text` | `{"state": <string>}`, may contain literal `\n` | confirmed live |
| `prf` | `{"hex": <string>}`, no `state` | confirmed live, format undocumented |
| `jalousie`/`jalousie120`/`gate`/`gate120` | `{"hex": <string>}`, no `state` | confirmed live, different wire format from standalone `jalousie`/`gate` |
| `sunrise` | `{"hex": <string>}`, no `state` | confirmed live, format undocumented |
| `plan` | `{"state": "undefined"}` | confirmed live, not an interactive widget |
| `lamp`/`dimer-lamp`/`rgb-lamp` | same shape as standalone counterpart (`state`/`level`/`hue`/`saturation`) | observed live but unreliable — see Notes |

### `sensor`

Plain numeric value, e.g.:
```json
{"state": 85.14}
```

### `text`

Short one-line string, no embedded newlines observed, e.g.:
```json
{"state": "762mmHg"}
{"state": "scattered clouds"}
{"state": "44"}
```

### `long-text`

Same `state`-string shape as `text`, but can be long (one real example
ran ~470 characters) and **does** contain literal `\n` newline characters.
This is the sub-type that actually uses the vendor's documented `%c`+10-for-
newlines script mechanism — `text` does not. Confirmed on a Komfovent
ventilation-unit status-dump script:
```json
{"state": "Alarms:\nComm: ERROR...\n\nStates:\nPower: 0\n..."}
```

### `prf`

Does **not** carry `state` at all. Confirmed live on `1:221`:
```json
{"hex": "0x00000000"}
```
Format of the hex is undocumented — nothing else learned about it.

### `jalousie`, `jalousie120`, `gate`, `gate120` (as `virtual` sub-types)

Do **not** carry `state` — status is hex-based, confirmed on 4 live
scripted examples (`1:225`-`1:228`):
```json
{"hex": "0x00"}
{"hex": "0x01"}
```
**The verb-form open/close model documented for the standalone
[jalousie](jalousie.md)/[gate](gate.md) types does not apply to their
`virtual` counterparts.** These are a distinct, undocumented wire format —
not an oversight, a genuinely different behavior.

### `sunrise`

Also hex-based, format undocumented. Confirmed live on `999:10` (named
"sunset&sunrise"):
```json
{"hex": "0x4E01A004"}
```

### `plan`

Status is:
```json
{"state": "undefined"}
```
Confirmed live on `2048:248` — this is a room-plan/floorplan image
reference (XML has `<dev-polygon>` children pinning other devices onto the
image), not an interactive widget.

### `lamp`, `dimer-lamp`, `rgb-lamp` (as `virtual` sub-types)

These carry the same status shape as their standalone counterparts
(`state`/`level`/`hue`/`saturation`) when working normally. **However, on
this session's only live example, behavior was unreliable:** the
`rgb-lamp` example (`1:224`) returned `level`/`saturation`/`hue` all equal
to `101.6` — outside the documented valid 0-100 range for all three
fields. Observed live, cause unconfirmed (controller bug, script bug, or
stand-specific quirk — not established which).

## Script — `sub-type="sensor"`

```xml
<additem type="virtual" sub-type="sensor" length="N" name="..."/>
```

`length` sets the display format: `length="2"` = 2-digit numeric,
`length="3"` = 3-digit numeric.

```c
setStatus(WGT_SENSOR, {0, value});  // {high_byte, low_byte}
```

For simple values (0-255), high byte is 0.

## Script — `sub-type="long-text"`

```xml
<additem tag="item" id="MODULE_ID" sub-id="%SUBID%"
         type="virtual" sub-type="long-text" length="0" name="..."/>
```

Uses a separate module ID (typically a DE-MG gateway), **not** the script's
own target.

```c
u8 buf[500];
sprintf(buf, "Line 1%cLine 2%cLine 3", 10, 10);  // %c with 10 = newline
setStatus(WGT_TEXT, buf);
```

`%c` with value `10` inserts a newline. Build multi-line text incrementally
with `sprintf(buf+strlen(buf), ...)`.

## Notes

The broadest "catch-all" type in the system — always check `sub-type`
before assuming behavior. The `type:"json"` API2 quirk (doubled `{{` in
`status`, see [api2_protocol.md](../api2_protocol.md#common-quirks-all-commands))
applies to `virtual` widgets using JSON-formatted status — see also the
standalone [json](json.md) device type.

<!-- Add live-tested quirks here as found. -->

- (2026-08-20/21) Full per-sub-type status shape confirmed live on
  `a1b2c3d4` for `sensor`, `text`, `long-text`, `prf`, `jalousie`/`gate`
  (+120 variants), `sunrise`, `plan`, `lamp`/`dimer-lamp`/`rgb-lamp` — see
  the API table and per-sub-type sections above. `ventilation` was already
  documented separately and untouched by this pass.

## Known bugs

None recorded yet.
