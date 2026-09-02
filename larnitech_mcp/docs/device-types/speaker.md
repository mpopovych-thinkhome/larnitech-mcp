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

Confirmed live 2026-09-02 on `5:30` (demo case), a streaming-radio setup.

Status:

```json
{
  "state": "stopped",
  "url": "http://hydra.cdnstream.com/1822_128",
  "priority": 0,
  "volume": 5.2,
  "position": "07.836"
}
```

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

  An unrecognised value is **not** rejected — it puts the widget into
  `state: "error"`, see [BUG-009](../bugs.md#bug-009).

- `next` / `previous` — switch **source**, not track. Confirmed: `next`
  changed `url` from one radio stream to another
  (`hydra.cdnstream.com/1822_128` → `dublab.out.airtime.pro/dublab_a`), and
  `previous` returned to the first. The list of sources is configured
  controller-side and is not visible through the API.

- `url` — the stream or file currently selected. This is the only
  indication of *what* is playing: no track title, artist, or stream
  metadata is exposed.

- `volume` — float **percent, 0-100**, but the underlying scale is the
  0-250 of the script API, so a written value snaps to the nearest 1/250
  step (0.4%). Writing `5` reads back as `5.2` (5% of 250 = 12.5 → 13 →
  13/250 = 5.2%). Values that land on a step come back exact: `12` and `50`
  both round-tripped unchanged. A write-then-verify comparing for exact
  equality will report a successful volume write as failed.

- `position` — playback position as a **string**, seconds with
  milliseconds (`"39.784"` = 39.784 s), not the raw milliseconds integer
  the script API uses. Advances in real time while `playing`, holds while
  `pause` and after `stop`, resets when the source changes.

- `priority` — integer, `0` observed. Script side documents 0-250, higher
  wins when several sources compete.

Not exposed through API2, though the script API has them: mute, balance,
track duration, sync master/slave.

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

## Known bugs

- [BUG-009](../bugs.md#bug-009) — an invalid `state` write drives the
  widget into `error` instead of being rejected
