Extended index of every documented device type — what exists and roughly
how, never the full detail. Every detail lives in the linked `<type>.md`
file; this file must stay consistent with them (same keys, same enum
values, same byte numbers). If they disagree and it's unclear which side is
current, ask the user rather than guessing — see the sync rule in
[the README](https://github.com/mpopovych-thinkhome/larnitech-mcp#readme).

`Issues` names every bug and quirk of that type by short title only — never
a description — so an agent scanning this file knows an issue exists and
can decide whether to open the type file.

## Index

| Type                                                              | Note                                                       | Issues   |
| ----------------------------------------------------------------- | ---------------------------------------------------------- | -------- |
| [ac](ac.md#ac)                                                    | Universal climate widget, most complex in the system       | 3 bugs   |
| [conditioner](conditioner.md#conditioner)                         | Distinct from `AC`, shares the mask-attribute bugs         | 2 bugs   |
| [climate-control](climate-control.md#climate-control)             | Generic HVAC/climate zone, no vendor page found            | quirk    |
| [dimmer-lamp](dimmer-lamp.md#dimmer-lamp)                         | Dimmable light                                             | —        |
| [rgb-lamp](rgb-lamp.md#rgb-lamp)                                  | RGB light, VSH color model                                 | —        |
| [lamp](lamp.md#lamp)                                              | Generic on/off indicator, sub-type changes semantics       | —        |
| [switch](switch.md#switch)                                        | Physical wall-panel button/key input, not a relay — resolved | —      |
| [valve](valve.md#valve)                                           | Water valve                                                | conflict |
| [valve-heating](valve-heating.md#valve-heating)                   | Heating valve with automation presets                      | quirk    |
| [fancoil](fancoil.md#fancoil)                                     | Fancoil, shares automation model with valve-heating        | quirk    |
| [ventilation](ventilation.md#ventilation)                         | `virtual/ventilation` — Komfovent-class units              | quirk    |
| [vent](vent.md#vent)                                              | Standalone type, not to be confused with `ventilation`     | quirk    |
| [virtual](virtual.md#virtual)                                     | Catch-all — behavior fully depends on `sub-type`           | quirk    |
| [json](json.md#json)                                              | JSON-status device, behavior fully depends on `sub-type`    | quirk    |
| [light-scheme](light-scheme.md#light-scheme)                      | Scene widget, `ls-type` undocumented upstream              | —        |
| [temperature-sensor](temperature-sensor.md#temperature-sensor)    | °C sensor                                                  | —        |
| [humidity-sensor](humidity-sensor.md#humidity-sensor)             | % sensor, read-only                                        | —        |
| [co2-sensor](co2-sensor.md#co2-sensor)                            | ppm sensor, read-only                                      | —        |
| [illumination-sensor](illumination-sensor.md#illumination-sensor) | Light-level sensor, read-only                              | —        |
| [motion-sensor](motion-sensor.md#motion-sensor)                   | Vendor page looks like a generic sensor template           | conflict |
| [door-sensor](door-sensor.md#door-sensor)                         | Generic contact widget, `sub-type` sets real semantics      | quirk    |
| [leak-sensor](leak-sensor.md#leak-sensor)                         | Leak detector, can report a fault via `malfunction`         | quirk    |
| [ir-transmitter](ir-transmitter.md#ir-transmitter)                | IR blaster, vendor page is a stub                          | —        |
| [ir-receiver](ir-receiver.md#ir-receiver)                         | IR receiver, one-shot capture                              | —        |
| [remote-control](remote-control.md#remote-control)                | RF remote learning widget, little confirmed                | quirk    |
| [script](script.md#script)                                        | An Imerel script instance as a device                      | —        |
| [com-port](com-port.md#com-port)                                  | RS232/serial port reference, no status                     | —        |
| [gate](gate.md#gate)                                              | Gate/door, digest oversimplifies to on/off                 | conflict |
| [jalousie](jalousie.md#jalousie)                                  | Motorized blind/shutter, same open/close model as `gate`   | quirk    |
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

**XML**
- `modes`: bitmask 5b, default `0x1F`
  - 0b — fan
  - 1b — cool
  - 2b — dry
  - 3b — heat
  - 4b — auto
- `fans`: bitmask 5b, default `0x1F` — auto, 1-5, silent
- `vane-ver`: bitmask 7b, default `0x7E`
- `vane-hor`: bitmask 8b, default `0x00`
- `t-min`/`t-delta`/`t-step`: int, default 16/16/1

**Script**
- Read: 9 bytes
  - 0 — status
    - 0b — on/off
    - 4-7b — mode as a number: 0 fan, 1 cool, 2 dry, 3 heat, 4 auto
  - 1 — fan speed
  - 2 — setpoint °C, int
  - 5 — current temp fraction `(t%10)*250/10`
  - 6 — current temp int `t/10`
  - 8 — alarm 0/1
- Write: `setStatus(WGT_AC, {...}, 9)`, same layout

**Note**
Universal climate widget, used by most HVAC scripts. API and script encodings are independent — no 1:1 mapping.

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
  - masks are live, must not be cached

---

### conditioner

**API**
- `modes`: reads as `0x1F` always, ignore the value — see bugs
- `funs`: never returned — see bugs

**XML**
- `modes`: bitmask 5b, default `0x1F` (same bit layout as `ac`)
- `funs`: bitmask, default `0x0F` — **named `funs` not `fans`**
- `vane-ver`/`vane-hor`: bitmask, default `0x7F` each
- `IRT`/`CONDID`/`IRID`: IR/identifier addresses

**Script**
- Read: 6 bytes — power, temperature, vane positions, airflow capacity (byte split unconfirmed live)
- Mode byte bits 4-7: same numbering as `ac`

**Note**
Distinct API2 type from `ac`, shares XML shape and masking bugs.

**Issues**
- Quirks — details in [conditioner.md](conditioner.md)
  - status key set confirmed; BUG-001/BUG-002 reproduced
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

**XML**
- no dedicated vendor page found — not documented

**Script**
- not documented

**Note**
Generic HVAC/climate zone type; relationship to `valve-heating`/`fancoil` unclear.

**Issues**
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

**XML**
- `color-temp`/`color-white`: linked dimmer addr, `"ID:SUBID"`
- `auto-period`: int seconds, `system`: yes/no

**Script**
- Read: 2 bytes — byte0 status bits (0 on/off, 3 automation, 7 alarm), byte1 brightness 0-250
- Write: 1 byte (on/off/toggle) or 3 bytes (state, brightness, transition seconds)

**Note**
API `level` (0-100%) and script brightness byte (0-250) are different scales for the same value.

**Issues**
- none recorded

---

### rgb-lamp

**API**
- `level`/`saturation`/`hue`: int, all 0-100 percent
  - `hue` needs ×3.6 on read / ÷3.6 on write to become degrees

**XML**
- same shape as `dimmer-lamp`: `color-temp`, `color-white`, `auto-period`, `system`

**Script**
- Read: 4 bytes — byte0 status bits, byte1 V(brightness), byte2 S(saturation), byte3 H(hue), all 0-250
- Write: 1/4/5 bytes (5th = transition time ×0.1s)

**Note**
Three independent 0-100% API scales map to three 0-250 script byte scales; `hue` additionally needs the degree conversion.

**Issues**
- none recorded

---

### lamp

**API**
- `state`: on/off
- `auto-state`: bool (plain sub-type only)

**XML**
- `sub-type`: enum — `damper`, `air-fan`, `socket`, `lock`, `dehumidifier`, `closing-switch`, `valve-3`, `pump`

**Script**
- Read/write: 1 byte — bit0 power, bit3 automation, bit7 alarm

**Note**
`sub-type` changes semantics, not just the icon.

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

**XML**
- `type`/`addr`/`name` only, no further attributes documented

**Script**
- Read: 2 bytes — byte0 key state (`0xFF` released/`0xFD` held/`0xFC` pressed), byte1 hold duration ×128ms
- LED status: separate config, values 0-31, standard/inverted color modes

**Note**
Confirmed live 2026-08-20: `switch` is a physical wall-panel button/key input, not a relay output — vendor page was right, the earlier digest's on/off relay framing was wrong. Conflict resolved.

**Issues**
- Quirks — details in [switch.md](switch.md)
  - resolved: confirmed live to be a button/key input, `hex`-only status, no `state`
  - integration gotcha: `hex` never clears between real gestures — merge/cache logic must diff against the last read, not re-act on every unrelated update

---

### valve

**API**
- `state`: string enum, `opened`/`closed` — write direction unconfirmed

**XML**
- `leak-sensors`: list, `;`-separated addresses
- optional `<linked addr="..."/>` control button

**Script**
- Read/write: 1 byte per vendor page — `0` off (water flowing), `1` on (water stopped)

**Note**
Vendor byte semantics (0/1 on/off) vs. live API string (`opened`/`closed`) — mapping direction not confirmed.

**Issues**
- Quirks — details in [valve.md](valve.md)
  - read vocab (opened/closed) confirmed NOT to work as write — try on/off or open/close next
  - digest vs. vendor-page mismatch: on/off byte vs. opened/closed string, unresolved

---

### valve-heating

**API**
- `state`/`automation`/`target`: automation absent = manual, name = preset, `"always-off"` = reserved lockout
- `target` resets to `-128` if set without `state`/`mode` together — always include `target`

**XML**
- `sub-type`: `warm-floor` (no observed behavior difference)
- `undefined-behavior`: `on`/`off`/`last`, default `last`
- `t-min`/`t-max`: default 0/32
- `<automation>` children: `name`, `temperature-level`, optional schedule

**Script**
- Event (1 byte): bit0 on/off, bits4-7 automation mode number
- Status request (6 bytes): status, setpoint (2b), avg temp (2b), mode indicator (`254`=always-off, `255`=manual)
- Write: 1 byte

**Note**
Always has 2 reserved modes (manual, always-off) beyond any named presets.

**Issues**
- Quirks — details in [valve-heating.md](valve-heating.md)
  - automation-reset + state-off must be two writes ~1s apart, not one combined write
  - automation:"" (manual) write confirmed working

---

### fancoil

**API**
- Status: `state`/`automation`/`target`/`current`/`fan`/`mode` — automation model identical to `valve-heating`
- `fan`: always float 0-100%, even on stepped hardware
- `valve-heating`/`valve-cooling` XML attrs not visible via API2 in either direction

**XML**
- `mode`: `heat`/`cool`, default `heat`
- `alg`: `eco`/`fast`/`boost`
- `valve-heating`/`valve-cooling`: addr references

**Script**
- Read: 7 bytes — setpoint/current (16-bit each), automation index, fan level 0-250, 8 error flags
- Write: 1 byte or 2 bytes (status + power 0-250)

**Note**
Shares its automation-mode model wholesale with `valve-heating`.

**Issues**
- Quirks — details in [fancoil.md](fancoil.md)
  - heat/cool mode switch needs mode + state as two writes ~1s apart, not one
  - shares valve-heating's automation-reset + state-off write-ordering quirk
  - target write may be ignored with no active automation (unconfirmed)

---

### ventilation

**API**
- Status: `{"state", "target", "fan"}` — `fan` is a **string preset** (e.g. `"auto"`)

**XML**
- `type="virtual" sub-type="ventilation"`, `funs` bitmask default `0xFF`, `length` default 6
- `temperature-sensors`: gates whether `target`/`current` appear in status at all

**Script**
- Read: 6 bytes — byte0 power bit0, byte1 temp (value+16 offset, bits0-3), byte4 airflow capacity bits0-3

**Note**
Not the same as `vent` below — same-sounding name, `fan` is a string here vs. a number there.

**Issues**
- Quirks — details in [ventilation.md](ventilation.md)
  - target/current only appear in status once temperature-sensors is set in XML

---

### vent

**API**
- Status: `{"state", "fan"}` — `fan` is a **number**, 0-100

**XML**
- `co2-sensors`, `undefined-behavior`, `P0`, `limit-fan`, `ctrl-change1/2`, `ctrl-ticks`, `alg`

**Script**
- Byte 6: current fan level 0-250
- Write: 1 byte (on/off/toggle) or 2 bytes (state + power)

**Note**
Not the same as `ventilation` above — `fan` is a number here vs. a string preset there.

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

**XML**
- `sub-type`: `sensor`, `text`, `long-text`, `lamp`, `dimer-lamp`, `rgb-lamp`, `jalousie`, `gate`, `gate120`, `jalousie120`, `prf`, `sunrise`, `plan`, `ventilation`
- `length`: 0 for text types, byte count otherwise
- `dim`: unit symbol suffix

**Script**
- `sensor`: `setStatus(WGT_SENSOR, {0, value})`
- `long-text`: separate module ID, `sprintf` with `%c`+10 for newlines

**Note**
Broadest catch-all type — always check `sub-type` before assuming behavior. `ventilation` sub-type has its own file. Full per-sub-type API confirmed live 2026-08-20/21 — see [virtual.md](virtual.md).

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

**XML**
- not yet pulled from the vendor wiki

**Script**
- not documented

**Note**
`MBUS` numeric key is the only stable field identifier — `typ` names repeat across keys on the same device. An unanswered meter returns every field (including `descr`/`hr`) as `null` for that poll cycle — not an error, not zero.

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

**XML**
- `<contains>` children: `addr`, `state`, `state-rev` (for `ls-type=3`)
- `<automation>` children: `door-sensors`, `enabled`, `illumination-level`, `time-interval`, `type`

**Script**
- not documented at byte level — behavior is controller-internal

**Note**
`ls-type` meanings (0=impulse, 1=impulse+feedback, 2=activation-only, 3=impulse+separate on/off status, 4=master-slave passthrough) come entirely from live testing — vendor page doesn't document them.

**Issues**
- none recorded

---

### temperature-sensor

**API**
- `state`: float °C

**XML**
- `scale`: `auto` or `MIN:MAX`
- `log-levels`: default `60,80,90`
- `value-min`/`value-max`: default 16/32

**Script**
- Read: 2 bytes — byte0 fraction `(v%10)*256/10`, byte1 integer `v/10`
- Decode back: `value = byte1*10 + byte0*10/255` (not `/26` — under-reads)

**Note**
Fractional encoding (×256/10) differs from `ac` (×250/10) — don't mix them up.

**Issues**
- none recorded

---

### humidity-sensor

**API**
- `current-humidity`: float %, read-only

**XML**
- `scale`, `value-min`/`value-max`: default 0/100

**Script**
- Read: 2 bytes — byte0 fraction, byte1 integer

**Note**
Read-only, same 2-byte shape as other continuous sensors.

**Issues**
- none recorded

---

### co2-sensor

**API**
- `state`: int ppm, read-only

**XML**
- `warning-level`/`emergency-level`: default 1500/2000
- `value-min`/`value-max`: default 0/5000

**Script**
- Read: 2 bytes, integer ppm

**Note**
Read-only, no write path documented. API status key confirmed live as `state`, not `current-co2`.

**Issues**
- none recorded

---

### illumination-sensor

**API**
- `state`: numeric light level, read-only

**XML**
- `scale`, `value-min`/`value-max`: default 0/100

**Script**
- Read: 2 bytes — byte0 fraction, byte1 integer

**Note**
Read-only, continuous range only.

**Issues**
- none recorded

---

### motion-sensor

**API**
- `state`: documented as key field — see conflict below

**XML**
- `scale`: `"0:100"` or `auto`
- `value-min`/`value-max`: default 0/100

**Script**
- Read: 2 bytes — byte0 fraction, byte1 integer (continuous-range encoding, no boolean)

**Note**
Vendor page uses the generic continuous-sensor template; no discrete "motion detected" value is documented.

**Issues**
- Quirks — details in [motion-sensor.md](motion-sensor.md)
  - digest assumes boolean `state`, vendor page describes continuous encoding, unresolved

---

### door-sensor

**API**
- status key shape unconfirmed this session

**XML**
- always has a `sub-type` attribute that sets real semantics — not a plain contact by default assumption
- sub-types confirmed to exist: `contact`, `motion`, `fire`, `smoke`, `gas`, `co2`, `leak`, `glass`, `lock`, `alarm`
- absent `sub-type` = plain contact semantics

**Script**
- not documented

**Note**
Only `contact` was confirmed live to report "on" (open) at the value level; the rest were confirmed only in XML dispatch, not their triggered value.

**Issues**
- Quirks — details in [door-sensor.md](door-sensor.md)
  - `sub-type` changes semantics, similar to `lamp` — status shape unconfirmed

---

### leak-sensor

**API**
- normal (non-fault) status shape unconfirmed this session
- can report a fault via `{"malfunction": <code>}` **instead of** normal state — confirmed live on a real device

**XML**
- not yet pulled from the vendor wiki

**Script**
- not documented

**Note**
`malfunction` is a companion "sensor itself is broken" signal, separate from "leak detected".

**Issues**
- Quirks — details in [leak-sensor.md](leak-sensor.md)
  - `malfunction` key confirmed live; normal status shape still unconfirmed

---

### ir-transmitter

**API**
- no status key documented

**XML**
- `type`/`addr`/`name` only — vendor page is a stub (last updated 2022)

**Script**
- "byte 0..N contains transmit packet" — no further breakdown given

**Note**
Minimal vendor documentation; nothing more until tested live.

**Issues**
- none recorded

---

### ir-receiver

**API**
- no status key confirmed live

**XML**
- `type`/`addr`/`name` only

**Script**
- Write (1 byte): 0 disable capture, 1 enable single-message capture
- Read (1 byte): 0 off, 1 on, other = message received
- Not persistent — must re-write `1` for each capture

**Note**
One-shot capture, not a listening mode.

**Issues**
- none recorded

---

### remote-control

**API**
- `state`: confirmed `"undefined"` on two devices with zero configured `<remote-signal>` children — populated-state and write-side (send-a-code) behavior unconfirmed

**XML**
- presumed `<remote-signal identifier=... transmitter-addr=... value=HEX.../>` children per vendor page, not re-verified this session

**Script**
- not documented

**Note**
Very little confirmed — only that `state` exists and reads `"undefined"` with nothing configured. Needs a real configured example to learn more.

**Issues**
- Quirks — details in [remote-control.md](remote-control.md)
  - only unconfigured examples tested; populated/write behavior unconfirmed

---

### script

**API**
- `state`: on/off (per general table, not separately reconfirmed for this type)

**XML**
- `path` or `body` (one required), `name`, `addr`, custom `NAME` params

**Script**
- Status: `0x00` off, `0x01` on, `0xFF` toggle

**Note**
Represents an Imerel script instance as a device — see separate script-authoring notes for script-authoring patterns, different subject.

**Issues**
- none recorded

---

### com-port

**API**
- no status key — not a device with readable status

**XML**
- `type`/`addr`/`name` only

**Script**
- not documented

**Note**
Mostly used as a `devices-list filter="com-port"` selector target in script settings, not a live device.

**Issues**
- none recorded

---

### gate

**API**
- digest simplifies to plain `state` — vendor page has a richer enum, see conflict below

**XML**
- `type`/`addr`/`name` only

**Script**
- Read (1 byte): 0 closed, 1 opened, 2 closing, 3 opening, 4 middle, 5 unknown
- Write (1 byte): 0 close, 1 open, 2 close, 3 open, 4 stop, `0xFF` toggle

**Note**
6-state read model — richer than plain on/off.

**Issues**
- Quirks — details in [gate.md](gate.md)
  - write needs verb form open/close, not opened/closed — echoing read vocab is a silent no-op
  - digest oversimplifies to on/off, vendor page documents 6 states, unconfirmed whether API2 collapses them

---

### jalousie

**API**
- `state`: four-state read — `opened`, `closed`, `opening`, `closing`
- Write vocabulary is the verb form (`open`/`close`), distinct from the read/state form

**XML**
- not yet pulled from the vendor wiki

**Script**
- not yet documented

**Note**
Same open/close motorized behaviour as `gate`, confirmed on a separate live device.

**Issues**
- Quirks — details in [jalousie.md](jalousie.md)
  - write needs verb form open/close, not opened/closed — see gate.md

---

### blinds

**API**
- `position`/`target`: numeric, 0-100 scale — **0 = fully open, 100 = fully closed** (inverted from the natural guess)
- transient overshoot past 0/100 (e.g. `-2`/`102`) observed during motion — motor coast, not a bug

**XML**
- not yet pulled from the vendor wiki

**Script**
- not documented

**Note**
Distinct control model from `jalousie`/`gate` — those are state-only, verb-form open/close writes with no position; `blinds` is a genuine position/target device.

**Issues**
- Quirks — details in [blinds.md](blinds.md)
  - 0=open/100=closed convention is inverted from typical expectation — confirmed live
