Index of every documented device type: the API2 status keys and the known
issues of each, nothing more. XML attributes, script byte layouts and notes
live only in the linked `<type>.md` — open it before writing XML or a script.
Status keys and issue titles here must match the type file; if they disagree
and it's unclear which side is current, ask the user rather than guessing.

The Larnitech MCP serves this file as the `get_docs()` overview and reads
each type's `**Issues**` block into every write preview — keep the
`### <type>` headings and the `**Issues**` / `- Bugs` / `- Quirks` layout.

A status of `{"state": "undefined"}` on any type usually means the device
is physically offline — see
[api2_protocol.md](../api2_protocol.md#common-quirks-all-commands).

The `<protect>` child element — a lockout some *other* device forces on this
one, seen on `valve-heating`, `AC`, `lamp`, `jalousie` and `dimmer-lamp` items
— is documented once in separate notes on `<protect>` lockouts, not per type.

`Issues` names every bug and quirk of that type by short title only — never
a description — so an agent scanning this file knows an issue exists and
can decide whether to open the type file.

## Index

| Type                                                              | Note                                                       | Issues   |
| ----------------------------------------------------------------- | ---------------------------------------------------------- | -------- |
| [ac](ac.md#ac)                                                    | Universal climate widget, most complex in the system       | 3 bugs   |
| [conditioner](conditioner.md#conditioner)                         | Distinct from `AC`, shares the mask-attribute bugs         | 2 bugs   |
| [climate-control](climate-control.md#climate-control)             | Generic HVAC/climate zone, no vendor page found            | 1 bug    |
| [dimmer-lamp](dimmer-lamp.md#dimmer-lamp)                         | Dimmable light                                             | —        |
| [rgb-lamp](rgb-lamp.md#rgb-lamp)                                  | RGB light, VSH color model                                 | —        |
| [lamp](lamp.md#lamp)                                              | Generic on/off indicator, sub-type changes semantics       | —        |
| [switch](switch.md#switch)                                        | Physical wall-panel button/key input, not a relay — resolved | —      |
| [valve](valve.md#valve)                                           | Water valve                                                | conflict |
| [valve-heating](valve-heating.md#valve-heating)                   | Heating valve with automation presets                      | 1 bug    |
| [fancoil](fancoil.md#fancoil)                                     | Fancoil, shares automation model with valve-heating        | 1 bug    |
| [ventilation](ventilation.md#ventilation)                         | `virtual/ventilation` — Komfovent-class units              | quirk    |
| [vent](vent.md#vent)                                              | Standalone type, not to be confused with `ventilation`     | quirk    |
| [virtual](virtual.md#virtual)                                     | Catch-all — behavior fully depends on `sub-type`           | quirk    |
| [json](json.md#json)                                              | JSON-status device, behavior fully depends on `sub-type`    | quirk    |
| [light-scheme](light-scheme.md#light-scheme)                      | Scene widget, `ls-type` undocumented upstream              | quirk    |
| [temperature-sensor](temperature-sensor.md#temperature-sensor)    | °C sensor                                                  | —        |
| [humidity-sensor](humidity-sensor.md#humidity-sensor)             | % sensor, read-only                                        | —        |
| [co2-sensor](co2-sensor.md#co2-sensor)                            | ppm sensor, read-only                                      | —        |
| [illumination-sensor](illumination-sensor.md#illumination-sensor) | Light-level sensor, read-only                              | —        |
| [motion-sensor](motion-sensor.md#motion-sensor)                   | Continuous motion level, not a boolean                     | —        |
| [door-sensor](door-sensor.md#door-sensor)                         | Generic contact widget, `sub-type` sets real semantics      | quirk    |
| [leak-sensor](leak-sensor.md#leak-sensor)                         | Leak detector, can report a fault via `malfunction`         | quirk    |
| [ir-transmitter](ir-transmitter.md#ir-transmitter)                | IR blaster, vendor page is a stub                          | —        |
| [ir-receiver](ir-receiver.md#ir-receiver)                         | IR receiver, one-shot capture                              | —        |
| [remote-control](remote-control.md#remote-control)                | RF remote learning widget, little confirmed                | quirk    |
| [script](script.md#script)                                        | An Imerel script instance as a device                      | quirk    |
| [com-port](com-port.md#com-port)                                  | RS232/serial port reference, status `hex` = last frame received | quirk |
| [gate](gate.md#gate)                                              | Gate/door, digest oversimplifies to on/off                 | conflict |
| [jalousie](jalousie.md#jalousie)                                  | Motorized blind/shutter, same open/close model as `gate`   | quirk    |
| [speaker](speaker.md#speaker)                                     | Media point — streams, volume, transport commands          | 1 bug    |
| [percent-sensor](percent-sensor.md#percent-sensor)                | Generic scalar readout, value is NOT a percent as-is       | quirk    |
| [float-sensor](float-sensor.md#float-sensor)                      | Generic scalar readout, scale not established              | quirk    |
| [current-sensor](current-sensor.md#current-sensor)                | Electrical current in amperes, encoding unconfirmed        | —        |
| [voltage-sensor](voltage-sensor.md#voltage-sensor)                | Simple voltage readout, unit unconfirmed                   | —        |
| [intercom](intercom.md#intercom)                                  | The system's own door station; exposes its door and camera links | unread |
| [mic](mic.md#mic)                                                 | Microphone of the intercom, status unread                  | unread   |
| [security-card-reader](security-card-reader.md#security-card-reader) | Card reader of the intercom, status unread              | unread   |
| [rtsp](rtsp.md#rtsp)                                              | A camera added to the system, status unread                | unread   |
| [blinds](blinds.md#blinds)                                        | Position/target device, 0=open/100=closed — distinct from `jalousie`/`gate` | quirk |

---

### ac

**API**
- `state`: enum
  - `on`
  - `off`
- `fan`: string enum
  - `auto`
  - `low`
  - `middle`
  - `high`
- device-level masks `modes`/`vane-ver`/`vane-hor`: hex string, live — re-read every poll (`get-devices`)

**Issues**
- Bugs
  - `fans` mask never returned — [BUG-001](../bugs.md#bug-001)
  - fan speeds 4/5/silent unreadable — [BUG-003](../bugs.md#bug-003)
  - vendor wiki says 8 status bytes — [BUG-004](../bugs.md#bug-004)
- Quirks — details in [ac.md](ac.md)
  - resolved: state mismatch was write latency, fixed by waiting for the push confirmation
  - vane-* is both a device mask and a status position
  - full status key set confirmed live
  - `fan` accepts only 4 fixed strings
  - script fan speed is byte 4, not byte 1
  - masks are live, must not be cached

---

### conditioner

**API**
- `modes`: reads as `0x1F` always, ignore the value — see bugs
- `funs`: never returned — see bugs

**Issues**
- Quirks — details in [conditioner.md](conditioner.md)
  - status key set confirmed; BUG-001/BUG-002 reproduced
  - script status byte 1 = setpoint °C − 16 (not plain °C as in `AC`)
- Bugs
  - `funs` mask never returned — [BUG-001](../bugs.md#bug-001)
  - `modes` returned as if unset — [BUG-002](../bugs.md#bug-002)

---

### climate-control

**API**
- `state`: on/off
- `setpoint-heat`/`setpoint-cool`: float °C
- `current-temperature`: float °C
- `current-humidity`: float %
- `pid-temperature`: heat demand 0-100%
- `mode`: string, `heat`/`cool`/`auto` (smaller lexicon than AC/fancoil's `mode`)
- `setpoint-warm-floor`/`current-warm-floor`/`pid-warm-floor`: same three for a zone with `warm-floor-sensors`

**Issues**
- Bugs
  - automation-preset switch leaves previous preset's outputs on — [BUG-010](../bugs.md#bug-010)
- Quirks — details in [climate-control.md](climate-control.md)
  - mode is optional and gated by the active automation's capability, not standalone
  - setpoints seen only in events, not snapshots (unresolved)
  - undocumented time-interval key
  - has automation/automations presets
  - modes is a list here, not a hex mask
  - mode lexicon confirmed heat/cool/auto; write needs no ordering/pacing, unlike valve-heating/fancoil/vent

---

### dimmer-lamp

**API**
- `state`: on/off
- `level`: int, 0-100 percent
- `color-temp`: int, 0-100 percent

**Issues**
- none recorded

---

### rgb-lamp

**API**
- `level`/`saturation`/`hue`: int, all 0-100 percent
  - `hue` needs ×3.6 on read / ÷3.6 on write to become degrees

**Issues**
- none recorded

---

### lamp

**API**
- `state`: on/off
- `auto-state`: bool (plain sub-type only)

**Issues**
- Quirks — details in [lamp.md](lamp.md)
  - `lock` sub-type: `state=off` means locked (inverted polarity)
  - `closing-switch` sub-type: behaves as persistent switch, not impulse

---

### switch

**API**
- No `state` key at all — status is `{"hex": "0xBBCC"}`
  - byte0 (`BB`) — key state: `0xFC` pressed, `0xFD` held/repeat, `0xFF` released
  - byte1 (`CC`) — hold-duration counter, 128ms ticks, resets to 0 on release

**Issues**
- Quirks — details in [switch.md](switch.md)
  - resolved: confirmed live to be a button/key input, `hex`-only status, no `state`
  - integration gotcha: `hex` never clears between real gestures — merge/cache logic must diff against the last read, not re-act on every unrelated update

---

### valve

**API**
- `state`: string enum, `opened`/`closed` — write direction unconfirmed

**Issues**
- Quirks — details in [valve.md](valve.md)
  - read vocab (opened/closed) confirmed NOT to work as write — try on/off or open/close next
  - digest vs. vendor-page mismatch: on/off byte vs. opened/closed string, unresolved

---

### valve-heating

**API**
- `state`/`automation`/`target`: automation absent = manual, name = preset, `"always-off"` = reserved lockout
- `target` resets to `-128` if set without `state`/`mode` together — always include `target`

**Issues**
- Bugs
  - automation-preset switch leaves previous preset's outputs on — [BUG-010](../bugs.md#bug-010)
- Quirks — details in [valve-heating.md](valve-heating.md)
  - automation-reset + state-off must be two writes ~1s apart, not one combined write
  - automation:"" (manual) write confirmed working
  - automation:"always-off" write confirmed — one write, no sequence; controller drops state to off itself and target leaves status
  - manual mode is `as:-4`, confirmed live — the language doc's own `-3` does not work

---

### fancoil

**API**
- Status: `state`/`automation`/`target`/`current`/`fan`/`mode` — automation model identical to `valve-heating`
- `fan`: always float 0-100%, even on stepped hardware
- `valve-heating`/`valve-cooling` XML attrs not visible via API2 in either direction

**Issues**
- Bugs
  - automation-preset switch leaves previous preset's outputs on — [BUG-010](../bugs.md#bug-010)
- Quirks — details in [fancoil.md](fancoil.md)
  - heat/cool mode switch needs mode + state as two writes ~1s apart, not one
  - shares valve-heating's automation-reset + state-off write-ordering quirk
  - automation switching (named preset + `as:-4` manual) confirmed live, identical to valve-heating
  - setpoint via `ts:<N>` confirmed live, works in Manual mode unlike the API2 `target` write
  - target write may be ignored with no active automation (unconfirmed)

---

### ventilation

**API**
- Status: `{"state", "target", "fan"}` — `fan` is a **string preset** (e.g. `"auto"`)

**Issues**
- Quirks — details in [ventilation.md](ventilation.md)
  - target/current only appear in status once temperature-sensors is set in XML

---

### vent

**API**
- Status: `{"state", "fan"}` — `fan` is a **number**, 0-100

**Issues**
- Quirks — details in [vent.md](vent.md)
  - fan is ignored when bundled with state in one call — write them as two separate calls
  - fan holds its last value after state goes off — does not reset to 0
  - shares valve-heating's automation-reset + state-off write-ordering quirk

---

### virtual

**API**
- fully dependent on `sub-type` — no fixed shape of its own
- `sensor`/`text`/`long-text`: carry `state` (number/string/string, `long-text` may contain literal `\n`)
- `prf`, `jalousie`/`jalousie120`/`gate`/`gate120`, `sunrise`: carry `hex` only, no `state` — undocumented formats; the jalousie/gate `virtual` sub-types are a **different wire format** from the standalone `jalousie`/`gate` types, not the same verb-form model
- `plan`: `{"state": "undefined"}` — floorplan image reference, not interactive
- `lamp`/`dimer-lamp`/`rgb-lamp`: same shape as standalone counterparts, but observed live emitting out-of-range values (0-100 fields all `101.6`) on this session's only example — reliability unconfirmed

**Issues**
- Quirks — details in [virtual.md](virtual.md)
  - `jalousie`/`gate` (+120) sub-types: hex-only, distinct undocumented wire format vs. their standalone counterparts
  - `prf`/`sunrise`: hex-only, format undocumented
  - `lamp`/`dimer-lamp`/`rgb-lamp` sub-types: observed emitting out-of-range values on the only live example — cause unconfirmed

---

### json

**API**
- fully dependent on `sub-type` — status is a JSON object, subject to the doubled-brace protocol quirk (see [api2_protocol.md](../api2_protocol.md#common-quirks-all-commands))
- `btunreg`: raw/empty diagnostic aggregate, no stable schema, e.g. `{"CAN810": {"0": {}, "1": {}}}`
- `MBUS`: self-describing meter data — numeric-string keys → values, plus `descr` (per-key metadata: `typ`/`dim`/`func`/`stor`) and `hr` (model/serial string)

**Issues**
- Quirks — details in [json.md](json.md)
  - `MBUS`: fully-`null` payload means "no data this cycle", must not be treated as error or zero
  - `MBUS` `descr` can itself contain `{"ERROR": "PARSER ERROR"}` — partial-decode signal, don't drop it
  - `btunreg`: no stable schema, not meant to be consumed generically

---

### light-scheme

**API**
- `state`: on/off, identical shape across all `ls-type` values
- `ls-type` itself does not come through the API at all — XML-only

**Issues**
- Quirks — details in [light-scheme.md](light-scheme.md)
  - no status-change event when a slave changes state, only on a direct widget press, ls-type 0/3 (BUG-007)

---

### temperature-sensor

**API**
- `state`: float °C

**Issues**
- Quirks — details in [temperature-sensor.md](temperature-sensor.md)
  - negative values: whole part rounded down in the script encoding

---

### humidity-sensor

**API**
- `current-humidity`: float %, read-only

**Issues**
- none recorded

---

### co2-sensor

**API**
- `state`: int ppm, read-only

**Issues**
- none recorded

---

### illumination-sensor

**API**
- `state`: numeric light level, read-only

**Issues**
- none recorded

---

### motion-sensor

**API**
- `state`: documented as key field — see conflict below

**Issues**
- Quirks — details in [motion-sensor.md](motion-sensor.md)
  - resolved: `state` is a continuous level, not a boolean — confirmed live

---

### door-sensor

**API**
- status key shape unconfirmed this session

**Issues**
- Quirks — details in [door-sensor.md](door-sensor.md)
  - `sub-type` changes semantics, similar to `lamp` — status shape unconfirmed

---

### leak-sensor

**API**
- normal (non-fault) status shape unconfirmed this session
- can report a fault via `{"malfunction": <code>}` **instead of** normal state — confirmed live on a real device

**Issues**
- Quirks — details in [leak-sensor.md](leak-sensor.md)
  - `malfunction` key confirmed live; normal status shape still unconfirmed

---

### ir-transmitter

**API**
- no status key documented

**Issues**
- none recorded

---

### ir-receiver

**API**
- no status key confirmed live

**Issues**
- none recorded

---

### remote-control

**API**
- `state`: confirmed `"undefined"` on two devices with zero configured `<remote-signal>` children — populated-state and write-side (send-a-code) behavior unconfirmed

**Issues**
- Quirks — details in [remote-control.md](remote-control.md)
  - only unconfigured examples tested; populated/write behavior unconfirmed

---

### script

**API**
- reads and writes exactly like a `lamp` — not a one-shot trigger
- `state`: on/off, writable
- `auto-state`: bool, auto mode — same flag as `lamp`, undocumented for this type; omitted rather than nulled

**Issues**
- Quirks — details in [script.md](script.md)
  - mutually exclusive script groups (house modes, seasons) are per-object configuration, not a property of the type

---

### com-port

**API**
- `hex` — last frame the controller received on the port (device answers, write echoes), hex string with CRC

**Issues**
- `hex` shows only received frames; identical consecutive frames make one event
- `hex` as an object (`{"hex": …}`, all MCP `set_device` can send) is ignored: `set_device` reports `acknowledged: false`, nothing goes to the bus; a raw frame goes out with API2 `status-set` and a string status (`"0x01060001002399D3"`, CRC by hand)

---

### gate

**API**
- digest simplifies to plain `state` — vendor page has a richer enum, see conflict below

**Issues**
- Quirks — details in [gate.md](gate.md)
  - write needs verb form open/close, not opened/closed — echoing read vocab is a silent no-op
  - digest oversimplifies to on/off, vendor page documents 6 states, unconfirmed whether API2 collapses them

---

### jalousie

**API**
- `state`: four-state read — `opened`, `closed`, `opening`, `closing`
- Write vocabulary is the verb form (`open`/`close`), distinct from the read/state form

**Issues**
- Quirks — details in [jalousie.md](jalousie.md)
  - write needs verb form open/close, not opened/closed — see gate.md

---

### blinds

**API**
- `position`/`target`: numeric, 0-100 scale — **0 = fully open, 100 = fully closed** (inverted from the natural guess)
- transient overshoot past 0/100 (e.g. `-2`/`102`) observed during motion — motor coast, not a bug

**Issues**
- Quirks — details in [blinds.md](blinds.md)
  - 0=open/100=closed convention is inverted from typical expectation — confirmed live

---

### speaker

**API**
- `state`: write vocabulary differs from read, and differs per command
  - `play` -> reads `playing`
  - `pause` -> reads `pause` (not `paused`)
  - `stop` -> reads `stopped`
  - `next` / `previous` -> switch source, read `playing`
  - read-only `eof`: reached the end of the track
- `url`: current stream/file, writable — the only indication of what is playing, no track metadata
- `volume`: float percent 0-100, snaps to 1/250 steps (0.4%)
- `muted`: bool, present ONLY while muted — unmuting removes the key and pushes no event
- `position`: string, `SS.mmm` / `M:SS.mmm` / `H:MM:SS.mmm`; writable (seek, in seconds, file sources only); pushed every second while playing
- `duration`: string, same shapes — only for a source that has one (file yes, live stream no)
- `priority`: int 0-250, an interruption stack that also gates whether a command runs at all
- device-level `linked`: button bindings, one of the few config-time attributes that IS exposed

**Issues**
- Bugs
  - invalid `state` write puts the widget in `error` — [BUG-009](../bugs.md#bug-009)
- Quirks — details in [speaker.md](speaker.md)
  - write vocabulary is per-command, three different rules
  - volume snaps to 0.4% steps, so an exact-match verify reports a good write as failed
  - `next`/`previous` change the source, not the track
  - priority stack: a lower-priority command is discarded in silence, a higher one claims the level, `stop` releases it and the source underneath resumes
  - `priority` is rejected when written on its own — only alongside another key
  - `muted`/`duration` are omitted rather than nulled, so merging partial updates resurrects stale values
  - the media point fetches media itself — a URL must resolve from where the controller sits

---

### percent-sensor

**API**
- `state`: number — **not a percent as-is**, observed 768, 256, 0 on an idle CPU
- Read-only

**Issues**
- Quirks — details in [percent-sensor.md](percent-sensor.md)
  - value exceeds 100 and needs scaling; ÷256 fits the samples but is unconfirmed

---

### float-sensor

**API**
- `state`: number, observed 17/23/20/35 and moving — live telemetry
- Read-only

**Issues**
- Quirks — details in [float-sensor.md](float-sensor.md)
  - scale not established, and different from `percent-sensor` (values are not multiples of 256)

---

### current-sensor

**API**
- `state`: electrical current in **amperes**; only ever observed as `0`, so encoding unconfirmed
- Read-only

**Issues**
- none recorded

---

### voltage-sensor

**API**
- `state`: number — voltage; read 16-18 across four devices, unit and scaling unconfirmed
- Read-only

**Issues**
- none recorded

---

### intercom

**API**
- `state`: only ever read as `"undefined"` — from an OFFLINE door station, so the live status is unknown
- device-level `door`: address of the lock it opens
- device-level `cameras`: address of its `rtsp` camera
- device-level `linked`: bound button addresses

**Issues**
- status never read from live hardware (only offline)

---

### mic

**API**
- `state`: only ever read as `"undefined"` — from an OFFLINE door station, so the live status is unknown
- Read-only

**Issues**
- status never read from live hardware (only offline)

---

### security-card-reader

**API**
- `state`: only ever read as `"undefined"` — from an OFFLINE door station, so the live status is unknown
- Read-only

**Issues**
- status never read from live hardware (only offline)

---

### rtsp

**API**
- `state`: only ever read as `"undefined"` — from an OFFLINE camera, so the live status is unknown; the device record carries no stream URL or credentials
- Read-only

**Issues**
- status never read from live hardware (only offline)
