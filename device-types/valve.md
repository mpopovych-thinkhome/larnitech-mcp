Digest of this file lives in [device_types.md](_device_types.md#valve) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Valve

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"valve"` |
| `addr` | string | device address | — | e.g. `"314:7"` |
| `name` | string | device identifier | — | any |
| `leak-sensors` | list | connected leak sensors | — | `;`-separated addresses, e.g. `"314:3;304:10"` |

Optional `<linked addr="314:1"/>` child — control button address.

## API

- `state`: string enum — **`opened`/`closed` vocabulary**, not `on`/`off`.
  Confirmed live 2026-08-14 on the main water valve (`status.state =
  "opened"`). Write not yet verified — currently assumed `on`/`off` by
  analogy with other types, **unconfirmed**.

⚠️ **Unresolved conflict with the vendor page's byte semantics below** — see
Notes.

## Script

Status (1 byte), per the official page:
- **Read:** `0` = valve off (water supply active), `1` = valve on (water
  supply stopped)
- **Write:** `0` off, `1` on, `0xFF` toggle

## Notes

**Mismatch, not yet resolved:** the official page's byte semantics (`0` =
off = water flowing, `1` = on = water stopped) describe an on/off
relay-style valve. Live API testing instead returned a `state` string of
`"opened"`/`"closed"` for this same `type="valve"`. It is unclear whether:
(a) `opened`/`closed` are the API2-decoded names for the same `0`/`1` byte
values (in which case the on/off ↔ opened/closed mapping direction still
needs confirming — does `1` mean opened or closed?), or (b) this is a
different sub-variant. Do not assume a mapping — verify against a live
device before writing to a `valve`.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) Writing `state: "closed"` (the same vocabulary `status-get` reads back) to `1:215` was **not acknowledged** — `status-set` object-form response had no `success: true` for this addr, and the device stayed `opened`. This replaces the earlier "unverified, assumed on/off by analogy" note: on/off is still untested, but the read vocabulary (`opened`/`closed`) is now confirmed **not** to work as write vocabulary, at least not on this device. Try `on`/`off`, or the `open`/`close` verb form that fixed `gate`/`jalousie`, before assuming `valve` is read-only via API2.

## Known bugs

None recorded yet.
