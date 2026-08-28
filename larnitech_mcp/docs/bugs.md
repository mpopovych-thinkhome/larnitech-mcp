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
