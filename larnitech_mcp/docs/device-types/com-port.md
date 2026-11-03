<a id="com-port"></a>

Index entry (status keys and issue titles only): [_device_types.md](_device_types.md#com-port) — keep those in sync.

## XML attributes

Source: https://wiki.larnitech.com/Com-port

| Attribute | Type | Description | Default | Values |
|---|---|---|---|---|
| `addr` | string | device address | — | e.g. `"595:18"` |
| `name` | string | device identifier | — | e.g. `"RS232"` |
| `type` | — | fixed | — | `"com-port"` |

```xml
<item addr="595:18" name="RS232" type="com-port"/>
```

Minimally documented page — no defaults, no further attributes, no
byte-level status info given by the vendor.

## API

No status key documented by the vendor. Seen live (2026-11-03, object 190,
RS-485 `210:1` with a Modbus RTU script): the status carries `hex`, the last
frame the controller received on the port, as a hex string with the CRC —
e.g. `0x0106000A0032281D`. Every received frame arrives as a `hex` change event
(a `watch_start` on the port shows the whole exchange in order).

## Script

Not documented.

## Notes

Thin type — mostly used as a `devices-list filter="com-port"` selector
target in script XML settings (see
the vendor's XML config documentation),
not as a device with meaningful status of its own.

<!-- Add live-tested quirks here as found. -->

- (2026-11-03) **MCP `modbus_request` (1.4.0) drives the port end to end, write
  included.** On object 190, port `210:1`, slave 1: register 1 read 35 four
  times in a row; FC06 36 was echoed and read back as 36; FC06 35
  (`01 06 00 01 00 23 99 D3`) was echoed and read back as 35. Register 1 is the
  climate widget's target (see above), so the unit's setpoint was 36 for a few
  seconds. One exchange takes 2.4-4 s: the answer queues behind the script's
  own polling. The script master here polls in one burst every 10 s — FC03
  count 4 (first register 35), two FC03 count 1 (45 and 1), five FC04 reads.
  The session's very first read of register 1 returned 36 and the next one
  4 s later 35: the Home Assistant integration was running the same 36 → 35
  test on this register at that moment.
  **The answer collision is real, not theoretical:** a later read of register
  1 (FC03 count 1) returned 45 — exactly the script's own FC03 count-1 answer
  in its polling burst — while the reads around it gave 34. A count-1 read
  of slave 1 here can take another register's value without any error; one
  of 12 reads did. Reading with a count the script does not use (here
  anything but 1 and 4) gives an answer of a size nobody else asks for.

- (2026-11-03) `hex` shows only what the controller *receives*: the device's
  answers, and for a write (FC06) the device's echo — identical to the
  request, so an echo with the written value confirms the write. The script's
  own read requests are not shown. Two identical frames in a row make one
  change event, not two. The CRC is not checked — decode the bytes by hand:
  `01 06 00 0A 00 32` = ID 1, FC06, register 10, value 50;
  `01 03 08 …` = a read answer of 4 registers (byte count 8).
  Used to verify writes of HeatPump_Daikin V0.4–V0.5 without script logs.
- (2026-11-03) **A raw frame can be sent to the port through API2, but only
  in the legacy string form** — `{"request": "status-set", "addr": "210:1",
  "status": "0x01060001002399D3"}` (the frame with the Modbus CRC, low byte
  first, computed by hand). Reply `{"response": "status-set", "devices":
  ["210:1"]}` (no `success`); the device's answer follows on the port after
  ~0.2 s, outside the script's own polling burst. Checked on object 190: a read
  of holding register 6 (`01 03 00 06 00 01 64 0B`) was answered
  `01 03 02 00 14 …` (20); a write of register 1 = 35 (`01 06 00 01 00 23 99 D3`)
  was echoed, the script's next cycle read 35 and the climate widget target
  became 35.0. The echo of the write came with two extra zero bytes
  (`…99D3 0000`), the read answer without — not explained.
- (2026-11-03) The object form `{"status": {"hex": "0x…"}}` is ignored: this is
  all MCP `set_device` can send (its `status` is a dict), so through MCP the
  port was read-only until 1.4.0's `modbus_request` — `set_device` returned `acknowledged: false, mismatched:
  ["hex"]` and nothing reaches the bus. A raw frame needs the API socket itself
  (`authorize`, then `status-set` with a string); the frames of other masters
  share the bus with the script — send only what the script would send.

## Known bugs

None recorded yet.
