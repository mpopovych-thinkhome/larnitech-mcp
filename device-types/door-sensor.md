Digest of this file lives in [device_types.md](_device_types.md#door-sensor) — keep both in sync.

## XML attributes

Not yet pulled from the vendor wiki. Confirmed live 2026-08-20 on object
`a1b2c3d4`: `type="door-sensor"` always carries a `sub-type` attribute that
determines its real semantics — **not** just a plain door/window contact.

Sub-types confirmed to exist (live XML): `contact`, `motion`, `fire`,
`smoke`, `gas`, `co2`, `leak`, `glass`, `lock`, `alarm`. Absent `sub-type` =
plain contact semantics.

Only `contact`'s dispatch was confirmed to actually report "on" (open)
live. The others' XML wiring/dispatch was confirmed to exist, but not their
triggered live value — no way to trigger fire/smoke/gas/etc. sensors on
the test stand.

## API

Status shape (whether it's `state: "open"/"closed"` or something else) is
**unconfirmed** this session.

## Script

Not documented.

## Notes

`sub-type` changes semantics for this type, similar to `lamp` — do not
assume plain contact behavior without checking `sub-type` first.

<!-- Add live-tested quirks here as found. -->

- (2026-08-20) Sub-type enum and XML dispatch confirmed live on
  `a1b2c3d4`; only `contact`'s "open" reporting confirmed at the value
  level. Status key shape unconfirmed.

## Known bugs

None recorded yet.
