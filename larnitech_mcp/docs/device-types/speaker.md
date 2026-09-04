Digest of this file lives in [device_types.md](_device_types.md#speaker) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Speaker (a stub — one example line, no
attribute table). Status semantics come from
https://wiki.larnitech.com/Mediapoint_control.

| Attribute | Type | Description | Values |
|---|---|---|---|
| `type` | — | fixed | `"speaker"` |
| `addr` | string | device address | e.g. `"5:30"` |
| `name` | string | device identifier | any |
| `hw` | string | space-separated hardware options | seen: `play-lim=0 ss=0` |

Child elements:

```xml
<item addr="5:30" hw="play-lim=0 ss=0" name="Media point" type="speaker">
    <linked addr="4:14" long-click="7"/>
    <linked addr="4:16" click="4" long-click="8"/>
</item>
```

`<linked>` binds a physical button (`addr` of a `switch`) to an action
number on click and/or long-click. **Unusually, this one does come through
API2** as a device-level `linked` array — most config-time attributes do
not (compare `fancoil`, whose valve links are invisible through the API).
`hw` does not come through.

## API

Confirmed live 2026-09-02/03 on `5:30` (demo case), against both a
streaming-radio source and a file on a local DLNA server.

Status:

```json
{
  "state": "playing",
  "url": "http://192.168.X.X:8200/MediaItems/20.mp3",
  "priority": 0,
  "volume": 5.2,
  "position": "1:42:44.907",
  "duration": "2:11.369",
  "muted": true
}
```

`duration` and `muted` are conditional — see below. A key the widget has no
value for is **omitted**, never nulled, which matters when merging partial
updates (see Notes).

- `state` — playback state. **The write vocabulary is not the read
  vocabulary, and it is inconsistent between commands:**

  | Write | Reads back as |
  |---|---|
  | `play` | `playing` |
  | `playing` | `playing` |
  | `pause` | `pause` — *not* `paused` |
  | `stop` | `stopped` |
  | `next` | `playing` |
  | `previous` | `playing` |

  Three different rules in one type: one command gains `-ing`, one gains
  `-ped`, one stays as written. Don't infer, use the table.

  Read-only on top of those: **`eof`** — the track reached its end. Not
  documented by the vendor; found 2026-09-03 by seeking past the duration,
  which does not clamp but ends playback with `position` back at zero. Only
  seen with nothing else queued underneath (see `priority`).

  An unrecognised value is **not** rejected — it puts the widget into
  `state: "error"`, see [BUG-009](../bugs.md#bug-009).

- `next` / `previous` — switch **source**, not track. Confirmed: `next`
  changed `url` from one radio stream to another
  (`hydra.cdnstream.com/1822_128` → `dublab.out.airtime.pro/dublab_a`), and
  `previous` returned to the first. The list of sources is configured
  controller-side and is not visible through the API.

- `url` — the stream or file currently selected, and **writable**: writing
  one switches the source, keeps playing, and resets `position` to zero.
  This is the only indication of *what* is playing: no track title, artist,
  or stream metadata is exposed.

- `volume` — float **percent, 0-100**, but the underlying scale is the
  0-250 of the script API, so a written value snaps to the nearest 1/250
  step (0.4%). Writing `5` reads back as `5.2` (5% of 250 = 12.5 → 13 →
  13/250 = 5.2%). Values that land on a step come back exact: `12` and `50`
  both round-tripped unchanged. A write-then-verify comparing for exact
  equality will report a successful volume write as failed.

- `muted` — boolean, and **present only while muted**: writing `false` is
  accepted but removes the key instead of setting it, so "not muted" is the
  absence of `muted`, not `muted: false`. Muting pushes a `statuses` event;
  **unmuting pushes none at all**, so an unmute made outside HA is invisible
  until the next full read.

- `position` — playback position as a **string** in one of three shapes:
  `SS.mmm`, `M:SS.mmm` or `H:MM:SS.mmm` (all three off one device within a
  minute — leading groups are dropped as they reach zero, so it cannot be
  parsed as plain seconds). Advances in real time while `playing`, holds
  while `pause` and after `stop`, resets when the source changes.

  **Writable — this is seek**, in seconds, and the same value lands whether
  written as `"1:00.000"`, `"20.000"` or a bare number. It only does
  anything where there is something to seek: on a file it jumps, on a live
  stream the write is acked and silently ignored. Past the end of the track
  it does not clamp — playback ends (`eof`, position zero), which is how a
  bare `90000` was found to be ninety thousand *seconds*, not milliseconds.

  While playing, the controller pushes a `position` event **every second**,
  forever. Anything mirroring this status into another system must not turn
  that into a write per second.

- `duration` — track length, same string shapes as `position`. Present
  **only for a source that has one**: a file has it, a live stream does not,
  and it disappears from the status when switching from the former to the
  latter.

- `priority` — integer 0-250, and far more than a label: it is an
  **interruption stack that also gates whether a command runs at all**.
  See the section below.

Not exposed through API2, though the script API has them: balance, soft
start, sync master/slave.

## Priority

Confirmed live 2026-09-03, all of it. Nothing here is on the vendor page.

- A playing source **holds a level**. A command arriving with a *higher*
  priority takes the media point over; one arriving with a *lower* priority
  is **discarded in silence** — no error, no ack, nothing changes. This
  applies to every command, `stop` included: a point held at priority 8
  ignores plain (priority-less, i.e. level 0) writes completely.
- `stop` at a priority >= the active one **releases the active level**
  rather than silencing the device. The source underneath resumes, at the
  position it would have reached — it kept running the whole time. With
  nothing underneath, playback stops (`stopped`, priority back to 0).
- A source that plays to its end pops the same way, and in that case no
  `eof` appears at all: the status goes straight back to the source below.
- Every other command **claims** the level it arrives with. A `pause` sent
  at 250 left the point parked at 250, where a later priority-0 `play`
  could no longer reach it. To act without hijacking, re-assert the level
  already active.
- `priority` is only accepted **alongside another key** — with `url` +
  `state`, or with `state`, `muted`, `volume` on its own. Written entirely
  by itself (`{"priority": 8}`) the controller does not even acknowledge it.

That makes it a public-address system: play an announcement at a level
above the background music and the music returns by itself when the
announcement ends, with no bookkeeping on the client side.

## Script

Source: https://wiki.larnitech.com/Mediapoint_control — status is a byte
array, a different model from the decoded API2 object above.

| Byte | Field | Range |
|---|---|---|
| 0 | state | 0 off, 1 playing, 2 error, 4 pause |
| 1 | volume | 0-250 |
| 2 | mute | flag |
| 3 | balance | — |
| 4 | priority | 0-250, higher wins |
| 5 | track duration | milliseconds |
| 9 | current position | milliseconds |
| 13-15 | sync master addr | if synchronised |
| 16 | sync slave count | — |
| 17 | url | media reference |

Commands:

```c
setStatus(MRID:30, 0);                      // stop
setStatus(MRID:30, 2);                      // pause
setStatus(MRID:30, 3);                      // continue
setStatus(MRID:30, {4, VOLUME});            // volume 0-250
setStatus(MRID:30, {8, "URL"});             // play a URL
setStatus(MRID:30, {9, 0, 1, 0, 0});        // seek, milliseconds
```

Newer string form:

```c
setStatus(MRID:30, {"v=120 m=0 p=1:20 s=1 r=1 ss=10.50 url=http://..."});
```

`v` volume, `m` mute, `s` play/stop/pause, `p` position, `r` priority,
`ss` soft start.

## Notes

The API2 view and the script view of this type disagree on almost every
representation: numeric state vs. string state, 0-250 volume vs. percent,
integer milliseconds vs. a seconds string. Treat them as two separate
interfaces to the same device rather than two views of one model.

<!-- Add live-tested quirks here as found. -->

- (2026-09-02) `<linked>` children reach API2 as a device-level `linked`
  array while the sibling `hw` attribute does not. There is no rule for
  which config-time attributes are exposed — check per attribute rather
  than assuming, and see [BUG-006](../bugs.md#bug-006) for the `system`
  attribute, which is never exposed.

- (2026-09-03) Two keys of this type come and go rather than being nulled —
  `duration` (only a file-backed source has one) and `muted` (present only
  while muted). Since events carry only what changed, an absent key in an
  event is ambiguous, and merging updates key-by-key resurrects values that
  are gone: a stream kept showing the previous file's duration. Treat a
  `url` change as invalidating `duration`, and re-read the full status
  after one.

- (2026-09-03) The media point fetches media **itself**, over the network,
  from wherever the controller sits. Handing it a URL that only resolves on
  the media server's own LAN produces silence with no error anywhere —
  worth checking first when a file "does not play".

## Known bugs

- [BUG-009](../bugs.md#bug-009) — an invalid `state` write drives the
  widget into `error` instead of being rejected
