Digest of this file lives in [device_types.md](_device_types.md#intercom) — keep both in sync.

## XML attributes

No vendor wiki page. Device-level attributes seen live tie the door station
to its parts:

| Attribute | Meaning | Example |
|---|---|---|
| `door` | address of the lock it opens | `903:8` |
| `cameras` | address of its [rtsp](rtsp.md) camera | `903:240` |
| `linked` | bound button/device addresses | `[{"addr": "903:1"}]` |

Unusually for this platform, these config-time links **do** come through
API2 — most do not (compare `fancoil`). Everything sits on one module
number, so the whole door station is recognisable by its address prefix.

## API

The system's own door station.

The only live reading so far, 2026-09-04, was taken while the door station
was **offline** and returned the offline placeholder:

```json
{"state": "undefined"}
```

So what this type reports when it is up — call state, ringing, door-open —
is **unknown**, not "nothing". See
[protocol](../api2_protocol.md#common-quirks-all-commands).

The `door`/`cameras`/`linked` attributes above still came through with the
hardware down: that wiring is served by the controller, not by the door
station.

## Script

Not documented.

## Notes

Comes as a family on one module: the intercom itself plus its
[mic](mic.md), [security-card-reader](security-card-reader.md) and
[rtsp](rtsp.md) camera.

<!-- Add live-tested quirks here as found. -->

- (2026-09-08) The 2026-09-04 reading came from a door station that was **offline** — `state: "undefined"` is the offline placeholder, not this type's real status. Re-test against a live door station.

## Known bugs

None recorded yet.
