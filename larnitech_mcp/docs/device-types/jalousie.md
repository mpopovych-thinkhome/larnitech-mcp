Digest of this file lives in [device_types.md](_device_types.md#jalousie) — keep both in sync.

## XML attributes

Not yet pulled from the vendor wiki — add when needed.

## API

- `state`: read as a **four-state** value — `opened`, `closed`, `opening`,
  `closing` (the two in-transition states were observed live, not
  documented anywhere before now)
- **Write vocabulary differs from read vocabulary.** Writing the verb form
  (`open`, `close`) is accepted and triggers a transition (`state` becomes
  `opening`/`closing`, then settles on `opened`/`closed`). Writing the
  participle form (`opened`, `closed` — i.e. an echo of what `status-get`
  reports) is **silently accepted with no effect**: the request gets a
  `success` ack from `status-set` object form, but the device never
  transitions and `state` stays unchanged. Confirmed live on `1:217`,
  2026-08-18.
- Transition takes measurable time — `status-get` read immediately after
  the write returns the pre-transition or mid-transition value; poll again
  rather than trusting a single immediate read.

## Script

Not yet documented.

## Notes

<!-- Add live-tested quirks here as found. -->

- (2026-08-18) Same write/read vocabulary split as `gate` — see there for the mechanism. Confirmed live on `1:217` with an identical failure and identical fix (re-send with `state: "close"` instead of `state: "closed"`).

## Known bugs

None recorded yet.
