Digest of this file lives in [device_types.md](_device_types.md#mic) — keep both in sync.

## XML attributes

No vendor wiki page. Plain item on the intercom's module.

## API

The microphone of the system's [intercom](intercom.md).

The only reading, 2026-09-04, came from an **offline** door station and
returned the offline placeholder:

```json
{"state": "undefined"}
```

Whether this type exposes level, mute or activity when live is **unknown**.
See [protocol](../api2_protocol.md#common-quirks-all-commands).

## Script

Not documented.

## Notes

Part of the door-station family — see [intercom](intercom.md).

<!-- Add live-tested quirks here as found. -->

- (2026-09-08) The 2026-09-04 reading came from a door station that was **offline** — `state: "undefined"` is the offline placeholder, not this type's real status. Re-test against a live door station.

## Known bugs

None recorded yet.
