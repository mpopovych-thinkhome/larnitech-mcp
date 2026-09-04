# Larnitech System Bugs

Numbered registry of confirmed vendor/system bugs found via live testing.
Every other doc in this base links to a `BUG-NNN` entry here instead of
restating the description — keep the description here, keep links elsewhere.

Reference from another file as: `[BUG-001](../bugs.md#bug-001)` (adjust the
relative path to `bugs.md` depending on the referencing file's location).

Each entry: found/confirmed date, affected device types, symptom,
workaround if any, status.

---

## BUG-001 — AC/conditioner: `fans`/`funs` mask never returned via API2

- **Found:** 2026-08-14 · **Confirmed:** 2026-08-14 (twice, `fans="0x47"` and later `fans="0x77"`)
- **Affects:** [ac](device-types/ac.md), [conditioner](device-types/conditioner.md)
- **Symptom:** mask explicitly set in XML (`fans="0x47"` on `1:101`) — key
  `fans` is absent from both `get-devices` and `status-get` responses
  entirely, not just empty.
- **Workaround:** assume the default mask — `0x1F` for AC, `0x0F` for
  conditioner. The real configured mask cannot be read via API2.
- **Status:** open (vendor side)

## BUG-002 — conditioner: `modes` returned as if no mask were set

- **Found:** 2026-08-17
- **Affects:** [conditioner](device-types/conditioner.md)
- **Symptom:** XML has `modes="0x1A"`, `get-devices` returns `"0x1F"` (all
  modes) regardless of the configured value. Unlike BUG-001, the key is
  present — just wrong. `AC` type does not have this bug: same test on
  `1:101` with `modes="0x1A"` returned the correct value.
- **Workaround:** do not read `modes`/`funs` for `conditioner` via API —
  always treat as the full default set.
- **Status:** open (vendor side)

## BUG-003 — AC: fan speeds 4/5/silent unreadable via API2

- **Found:** 2026-08-17
- **Affects:** [ac](device-types/ac.md)
- **Symptom:** live `AC` (`1:101`) running above its 3rd fan speed reports
  `status.fan = null` instead of the actual speed. Confirmed the physical
  unit was running faster than "high" at the time.
- **Workaround:** none — speeds 4/5/silent can be neither read nor written
  via API2 (see also: `status.fan` only accepts `auto`/`low`/`middle`/`high`
  on write, other values rejected with `{"code":9,"description":"set-status
  has invalid parameter"}`).
- **Status:** open (vendor side)

## BUG-004 — AC: official wiki documents 8 status bytes, actual is 9

- **Found:** 2026-08-18
- **Affects:** [ac](device-types/ac.md)
- **Symptom:** `wiki.larnitech.com/AC` states "8-byte status response";
  bytes 0 through 8 (= 9 bytes) are documented on that same page and used
  in production scripts (see `ac.md` → Script).
- **Workaround:** none needed — use 9 bytes, it is what actually works.
- **Status:** open (vendor doc error, not a runtime bug)

## BUG-005 — `statuses` push events never identify the exciter

- **Found:** 2026-08-27
- **Affects:** all widget types (API2 push protocol, not a specific device)
- **Symptom:** a `statuses` push event carries `exciterId`/`exciterSubId`
  (which widget caused the status change), but both always arrive `0` —
  there is no way to tell from the event itself whether a status change
  came from a physical panel, another script/automation, or the HA
  integration's own write, only that *something* changed.
- **Workaround:** none — cannot distinguish the source of a status change
  via API2 push events.
- **Status:** open (vendor side)

## BUG-006 — API2 does not expose `system` widget attribute

- **Found:** 2026-08-27
- **Affects:** `get-devices` (API2 read), all widget types
- **Symptom:** LT_Setup's XML config carries a `system` attribute marking a
  widget as internal/hidden (e.g. group-summary lights, wiring-scaffold
  channels) rather than a real user-facing control. Confirmed by direct
  inspection of a full `get-devices` snapshot (Kaunas school object, 1853
  devices): no device carries a `system` key or any equivalent, regardless
  of whether the widget is marked `system` in LT_Setup. Larnitech's own app
  presumably reads this from the XML config directly, not from the runtime
  API.
- **Workaround:** none via API2. The nearest available proxy from
  `get-devices` alone is an empty/placeholder `name` (`"(пусто)"`) combined
  with `area: "Setup"` — every genuinely unconfigured channel observed so
  far matches both, but this is a placeholder-detection heuristic, not a
  real reading of the `system` flag, and will not catch a widget marked
  `system` that also has a real name/area set.
- **Status:** open (vendor side)

## BUG-007 — `light-scheme` (ls-type 0/3): no status-change event when a slave changes state, only on a direct widget press

- **Found:** 2026-08-28 (live watch, test stand, addr `1:211`, `ls-type=3`)
- **Affects:** [light-scheme](device-types/light-scheme.md), ls-type 0 and 3
- **Symptom:** events about a status change do not arrive if the status
  changes because of a slave device, only when the widget itself is
  pressed directly. Confirmed live: 3 manual toggles of the widget each
  produced a `statuses` push event (`off→on`, `on→off`, `off→on`); a 4th
  change — a slave device's state changed directly, bypassing the scheme
  widget — produced no push event at all, and a follow-up `status-get`
  still returned the stale `state: "on"`.
- **Workaround:** none via API2 — no way to read the true combined state of
  the slaves through this widget. Don't treat `light-scheme` `status.state`
  as live telemetry for ls-type 0/3; it only reflects "was this scheme last
  triggered on or off," not "are the slaves currently in that state."
- **Status:** open (protocol limitation, not fixable client-side)

## BUG-008 — WebSocket: no pong on ping, and session close sends no close frame

- **Found:** undated (documented in [api2_protocol.md](api2_protocol.md#common-quirks-all-commands) quirks list, not previously tracked as a numbered bug)
- **Affects:** WebSocket session (cloud), all commands/types — protocol-level, not device-specific
- **Symptom:** two related keepalive issues:
  1. The cloud never answers a WS ping — a client with `ping_interval` set
     drops the connection on `keepalive ping timeout` (no pong ever
     arrives).
  2. After ~5 minutes idle (no packets sent), the server closes the session
     **without sending a close frame** (`no close frame received or sent`).
- **Workaround:** disable client-side pings (`ping_interval=None`); keep the
  session alive with periodic real requests (e.g. `get-devices`) instead of
  ping/pong — any request resets the idle timer. Keep the client
  `close_timeout` small so the missing close frame doesn't hang the client
  on disconnect.
- **Status:** open (vendor side)

## BUG-009 — `speaker`: an invalid `state` write drives the widget into `error`

- **Found:** 2026-09-02 (live, demo case, addr `5:30`)
- **Affects:** [speaker](device-types/speaker.md)
- **Symptom:** writing an unrecognised value to `status.state` is not
  rejected as a bad parameter. The `status-set` returns without a success
  ack, and the widget then reports `state: "error"` and stays there.
  Confirmed with `state: "start"` (a plausible-looking synonym for the
  accepted `play`): the response carried no `success`, and a follow-up
  `status-get` returned `{"state": "error"}`.
- **Contrast:** `AC`/`conditioner` reject a bad `fan` value cleanly with
  `{"code":9,"description":"set-status has invalid parameter"}` and keep
  working. This type breaks instead.
- **Workaround:** write only the confirmed vocabulary — `play`, `playing`,
  `pause`, `stop`, `next`, `previous`. Recovery from `error` is a plain
  `play`, which restores normal playback.
- **Status:** open (vendor side)

## BUG-010 — climate-control/valve-heating/fancoil: switching the whole-house automation preset does not turn off outputs left on by the previous preset

- **Found:** 2026-09-04 (reported by user, another installation)
- **Affects:** [climate-control](device-types/climate-control.md),
  [valve-heating](device-types/valve-heating.md),
  [fancoil](device-types/fancoil.md)
- **Symptom:** when a script switches the whole-house automation preset
  (e.g. `Winter` → `Summer`), any zone/device that was `on` under the old
  preset stays `on` — the controller does not clear it. The new preset then
  activates its own devices (e.g. cooling fancoils/valves under `Summer`)
  on top of that, without first turning off what the old preset left
  running. Net effect: heating and cooling outputs end up `on`
  simultaneously in the same zone (e.g. floor heating from `Winter` still
  running while a fancoil switches to `cool` under `Summer`).
- **Workaround:** in the script that performs the whole-house
  automation switch, add a function called with a **~20s delay** after
  the switch that explicitly turns off every device that was on under the
  *previous* preset — do not rely on the new preset to supersede it.
- **Status:** open (vendor side)
