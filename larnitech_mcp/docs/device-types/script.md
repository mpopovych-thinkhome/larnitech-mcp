Digest of this file lives in [device_types.md](_device_types.md#script) — keep both in sync.

## XML attributes

Source: https://wiki.larnitech.com/Script

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `path` | string | path to script file, relative to server folder | required* | — |
| `body` | string | script contents inline (instead of `path`) | required* | — |
| `type` | — | fixed | optional | `"script"` |
| `name` | string | script instance identifier | optional | any |
| `addr` | string | memory address reference | optional | e.g. `"125:150"` |
| `NAME` | string | parameters sent to the script (custom, name varies per script) | optional | — |

Either `path` or `body` is required, not both.

Seen live but absent from the vendor page (demo case, 2026-09-10):

| Attribute | Description |
|---|---|
| `id` | the module half of `addr` repeated on its own (`id="302"` on `addr="302:247"`) |
| `image` | icon reference, e.g. `home` — same idea as `light-scheme`'s |
| `script-folder` | **base64** of an XPath into the config, e.g. `L3NtYXJ0LWhvdXNlL3NjcmlwdC1mb2xkZXJzL3NjcmlwdC1mb2xkZXJbMl0` → `/smart-house/script-folders/script-folder[2]` |

```xml
<item addr="302:247" id="302" image="home" name="Home"
      path="blocklyScripts/qpeaurSghZ.txt"
      script-folder="L3NtYXJ0LWhvdXNlL3NjcmlwdC1mb2xkZXJzL3NjcmlwdC1mb2xkZXJbMl0"
      type="script"/>
```

A `path` under `blocklyScripts/` is a script authored in the Blockly editor
rather than written by hand — the file name is generated, so it says nothing
about what the script does. None of these attributes reach API2; there the
device carries only `addr`/`type`/`name`/`area`/`status`.

## API

Confirmed live 2026-09-10 on the demo case, across 12 script widgets.

A script is not a one-shot trigger over API2 — **it reads and writes exactly
like a `lamp`**, and the same two keys carry it:

- `state`: on/off, writable. Writing `on` starts it, `off` stops it, and the
  new state comes back as an ordinary event.
- `auto-state`: bool — the same auto-mode flag `lamp` has, undocumented by
  the vendor for this type. Present only while the state is automatic: it
  vanished from both widgets involved in a manual switch and stayed on the
  untouched third one. Like `muted`/`duration` on
  [speaker](speaker.md#api), it is **omitted rather than nulled**, so a
  key-by-key merge of partial events resurrects a stale value.

## Script

Status values: `0x00` off, `0x01` on, `0xFF` toggle.

## Notes

Represents an Imerel script instance as a device — distinct from the
per-device-type `.md` files in this folder, which document the *targets*
scripts control, not scripts themselves. For script authoring patterns see
separate script-authoring notes.

<!-- Add live-tested quirks here as found. -->

- (2026-09-10) Scripts wired as **mutually exclusive groups** — house modes
  (Away / Home / Night / Vacation), seasons (Summer / Midseason / Winter) —
  are a per-object configuration, **not a property of the type**. On the demo
  case, turning `Midseason` on turned `Summer` off; the controller does that
  itself and the sibling's new state arrives as an ordinary event, so there
  is nothing to model — but do not assume the behaviour on another object.

## Known bugs

None recorded yet.
