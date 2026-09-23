<a id="rtsp"></a>

Digest of this file lives in [device_types.md](_device_types.md#rtsp) — keep both in sync.

## XML attributes

No vendor wiki page. Observed as a plain item; an intercom references its
camera through a `cameras` attribute (see [intercom](intercom.md)).

## API

A camera added to the system.

The one camera read, 2026-09-04, was the **offline** door station's own
camera and returned the offline placeholder:

```json
{"state": "undefined"}
```

So this type's live status is **unknown**. See
[protocol](../api2_protocol.md#common-quirks-all-commands).

Independent of status: the device record carries no stream URL, credentials
or snapshot endpoint — the widget is a reference to a camera configured
elsewhere, not a source of video metadata.

## Script

Not documented.

## Notes

<!-- Add live-tested quirks here as found. -->

- (2026-09-08) The 2026-09-04 reading came from a door station that was **offline** — `state: "undefined"` is the offline placeholder, not this type's real status. Re-test against a live door station.

## Known bugs

None recorded yet.
