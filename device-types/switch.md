Digest of this file lives in [device_types.md](_device_types.md#switch) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Switch

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"switch"` |
| `addr` | string | device address | — | e.g. `"125:1"` |
| `name` | string | device identifier | — | e.g. `"№1"` |

No further attributes documented.

## API

**Confirmed live 2026-08-20.** `switch` is a physical wall-panel button/key
**input**, not a relay output — the vendor page was right, the earlier
digest calling it a plain on/off relay was wrong.

Status carries **no `state` key at all** — only a `hex` field:

```json
{"hex": "0xBBCC"}
```

- byte 0 (`BB`, high byte) — key state:
  - `0xFC` — pressed (initial press)
  - `0xFD` — held / repeat
  - `0xFF` — released
- byte 1 (`CC`, low byte) — hold-duration counter, in 128 ms ticks; counts
  up while held, resets to `0` on release
- On release (`0xFF`), the counter value distinguishes a short tap
  (counter still `0`) from a long hold ending (counter `>0`)

## Script

Status (2 bytes) — same shape as the API `hex` field above:
- byte 0 — key state: `0xFF` released, `0xFD` held, `0xFC` pressed
- byte 1 — hold duration, increments of 128 ms

LED status (separate config): standard mode — values 0-31 select
red/green/yellow/off with optional blink (0.25/0.5/1/2 s intervals);
inverted mode — same range, colors swapped (green replaces red, etc.).

## Notes

**Resolved (2026-08-20):** the earlier "relay vs. button input" conflict is
closed — `switch` is confirmed live to be a button/key input, matching the
vendor page. It never carries `state`, only `hex`.

**Integration-side gotcha (partial-update / merge logic):** the `hex` value
never clears between real button gestures — there is no "idle" hex that
means "nothing happening." A `merge_status`-style cache that re-reads this
key on every unrelated device update (not just real button events) will
treat the last stale gesture as a fresh one and refire it endlessly. Only
act on `hex` when it actually changed since the last read for this device.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) Live test on `1:220` (a device explicitly named "switch,
  virtual" on the stand) supports the input-not-output theory: `status`
  had no `state` key, and writing `state: "on"` was **not acknowledged** —
  no ack, no state change.
- (2026-08-20) Confirmed the full `hex` field shape and byte meaning live
  (see API above) — closes the conflict recorded on 2026-08-18.

## Known bugs

None recorded yet.
