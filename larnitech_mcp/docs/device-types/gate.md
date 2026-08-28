Digest of this file lives in [device_types.md](_device_types.md#gate) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Gate

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `type` | — | fixed | — | `"gate"` |
| `addr` | string | device address | — | e.g. `"384:6"` |
| `name` | string | device identifier | — | e.g. `"Garage"` |

No further attributes documented.

## API

⚠️ The general device-types digest simplifies this type's key field to a
plain `state`, but the vendor page documents a richer position enum (see
Script below) — see Notes.

## Script

Status (1 byte), read — gate position:

| Value | Meaning |
|---|---|
| 0 | closed |
| 1 | opened |
| 2 | closing |
| 3 | opening |
| 4 | middle position |
| 5 | unknown |

Write (1 byte):

| Value | Action |
|---|---|
| 0 | close (stop if position is 2 or 3) |
| 1 | open (stop if position is 2 or 3) |
| 2 | close |
| 3 | open |
| 4 | stop |
| 0xFF | toggle |

## Notes

**Simplification flagged:** treating `gate` as plain on/off loses the
`closing`/`opening`/`middle`/`unknown` states — if building anything that
needs to show gate motion (not just end position), confirm via a live
`status-get` whether these 6 values come through the API as-is or are
collapsed to fewer states at the API2 layer.

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) **Resolves the open question above: API2 does not collapse the position enum.** Confirmed live on `1:218`: `status.state` came through as `closed`, `opened`, and — mid-motion — `opening`/`closing`, matching the vendor script model, not the digest's plain on/off simplification. **Write vocabulary is the verb form (`open`/`close`), not the state form.** Writing `state: "open"` was accepted and produced a transition; writing the read-vocabulary participle `state: "closed"` back was accepted by `status-set` (ack `success: true`) but had **no effect at all** — the gate stayed `opened` through 15s of polling. Only re-sending with the verb form `state: "close"` actually closed it (via `closing` -> `closed`). Transition takes several seconds — do not trust a `status-get` read taken immediately after the write.

## Known bugs

None recorded yet.
