Digest of this file lives in [device_types.md](_device_types.md#remote-control) — keep both in sync.

## XML attributes

Not yet pulled/verified from the vendor wiki this session. Vendor page is
presumed to describe `<remote-signal identifier=... transmitter-addr=...
value=HEX.../>` children and an app-side learning flow (point a real remote
at an IR receiver, press button, capture code) — not re-verified here, but
nothing found contradicts it.

## API

Confirmed live 2026-08-20/21 on object `a1b2c3d4`: two examples
(`2048:250`, `2048:249`), both with **zero configured `<remote-signal>`
children**. Status for both was simply:
```json
{"state": "undefined"}
```

What `state` becomes once actual `<remote-signal>` buttons are configured
is **unconfirmed** — needs a real configured example. Write-side
(send-a-code) behavior is also **unconfirmed**.

## Script

Not documented.

## Notes

Very little confirmed this session — only that `state` exists and reads
`"undefined"` with nothing configured.

<!-- Add live-tested quirks here as found. -->

- (2026-08-20/21) `state: "undefined"` confirmed on two unconfigured
  devices (`2048:250`, `2048:249`). No configured example available to
  learn the populated-state or write-side shape.

## Known bugs

None recorded yet.
