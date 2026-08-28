# Larnitech API2 — Protocol & Connection Guide

Connection mechanics, WebSocket/HTTP commands, and protocol-level quirks.
Device-type status keys, XML attributes, and per-type quirks live in
[device-types/](device-types/_device_types.md), not here. Known vendor bugs
are numbered in [bugs.md](bugs.md) — this file links to them, never restates.

## What You Need

| Item                       | Where to get it                            |
| -------------------------- | ------------------------------------------ |
| Server serial number       | LT_Setup → General                         |
| API key                    | LT_Setup → Security → Show API key         |
| IP address (local only)    | LT_Setup → General, or router DHCP table   |
| WebSocket client or Python | Any WS client, or `pip install websockets` |

Credentials per object are stored in `mcp/project_keys.json` — see
[README.md](https://github.com/mpopovych-thinkhome/larnitech-mcp#readme).

---

## Connecting

### Cloud

```
wss://<SERIAL>.in.larnitech.com:8443/api
```

TLS, port `8443`. No port forwarding needed — routed through the Larnitech
cloud. Example stand: `wss://a1b2c3d4.in.larnitech.com:8443/api`.

### Local (LAN)

```
ws://<IPADDR>:2041/api
```

No TLS, default port `2041`. Faster, no cloud dependency, but requires
network access to the controller.

### HTTP (alternative, no session)

```
http://<IPADDR>/API2/    or    http://de-mg.local/API2/
```

For one-off reads/writes. No session — `"API-KEY"` is sent in **every**
request body. `status-subscribe` is not available over HTTP (needs
WebSocket).

### Settings

| Parameter        | Where |
|-------------------|---|
| WebSocket port    | LT_Setup → General → API → Websocket port (default `2041`) |
| Serial            | LT_Setup → General |
| API key           | LT_Setup → Security → Show API key |

---

## WebSocket (primary method)

One socket = one session. After a successful `authorize`, all further
requests go over the same connection without re-authorizing.

### Commands

#### `authorize`

Sent right after opening the socket, once per session.

**Request:**
```json
{"request": "authorize", "key": "YOUR_API_KEY"}
```
**Response:**
```json
{"response": "authorize", "result": "success"}
```

**Nuances:**
- Wrong key → `result` is not `"success"` (connection stays open, but
  commands don't go through).
- No need to re-authorize within the same session.

---

#### `get-devices` — all devices

**Request:**
```json
{"request": "get-devices", "status": "detailed"}
```
**Response (abridged):**
```json
{
  "response": "get-devices",
  "devices": [
    {"addr": "1:1", "type": "lamp", "name": "Spotai", "area": "Hall",
     "status": {"state": "off", "auto-state": true}}
  ],
  "found": 59
}
```

Device fields: `addr`, `type`, `name`, `area`, `status`, plus `automations`
and `modes` for climate devices.

**Nuances:**
- **Without `status:"detailed"` there is no `status` key at all** — only
  device descriptions come back.
- `detailed` applies **only to this request** (not sticky on the session).
- May contain the `"status":{{` quirk (`type:"json"` widgets) and control
  characters — see "Common quirks" below.
- Stand: ~160-210 ms, 11.4 KB, 59 devices.

---

#### `status-get` — status of one device

**Request:**
```json
{"request": "status-get", "addr": "33:200", "status": "detailed"}
```
**Response (abridged):**
```json
{
  "response": "status-get",
  "devices": [
    {"addr": "33:200", "type": "climate-control",
     "status": {"state": "on", "setpoint-heat": 22.0, "current-temperature": 21.2}}
  ],
  "found": 1
}
```

**Nuances:**
- Same `detailed` rule as `get-devices`.
- `found: 0` if `addr` doesn't exist.
- **Response is "thin" — only `addr`/`type`/`status`.** (2026-08-17,
  confirmed live on `1:101`) Unlike `get-devices`, there is no
  `name`/`area`/`automations`/`modes`/`vane-hor`/`t-min`/... — no
  device-level config attributes, status only. If you use `status-get` for
  a point update after a write (write-then-verify) — **merge only the
  `status` key** into the existing device dict, never replace the whole
  dict: a replace wipes masks/name/area and everything else `status-get`
  doesn't return.

---

#### `status-set` — set state

**On/off (object):**
```json
{"request": "status-set", "addr": "999:250", "status": {"state": "off"}}
```
**Dimmer — brightness:**
```json
{"request": "status-set", "addr": "585:17", "status": {"level": 50}}
```
**Dimmer — color temperature:**
```json
{"request": "status-set", "addr": "585:17", "status": {"color-temp": 100}}
```
**Climate — setpoint:**
```json
{"request": "status-set", "addr": "33:200", "status": {"state": "on", "setpoint-heat": 21.0}}
```
**Hex (legacy):**
```json
{"request": "status-set", "addr": "999:250", "status": "0x01"}
```
**Response (object form):**
```json
{"response": "status-set", "devices": [{"addr": "999:250", "success": true}]}
```

**Nuances:**
- **Both object and hex apply the change**, but the response differs:
  object gives `[{"addr":...,"success":true}]`; hex gives `["999:250"]`
  (bare addr, no `success`). **Use object form** — it has a checkable ack.
- The change is sent as one command for one `addr`, not a list.
- Which keys apply depends on type (`state` / `level` / `setpoint-heat` /
  etc.) — see [device-types/](device-types/_device_types.md).

---

#### `status-subscribe` — event subscription (WebSocket only)

**Request (global, all devices):**
```json
{"request": "status-subscribe", "status": "detailed"}
```
**Request (one device):**
```json
{"request": "status-subscribe", "addr": "999:250", "status": "detailed"}
```
**Response (abridged):**
```json
{"response": "status-subscribe", "devices": [{"addr": "1:1", "status": {"state": "off"}}],
 "found": 58, "subscribed": 58}
```
**Incoming event:**
```json
{"event": "statuses", "devices": [{"addr": "1:1", "status": {"state": "on"}}]}
```

**Nuances:**
- **The `detailed` flag determines the event format:** with it — decoded
  objects (`{"state":"on"}`); without it — hex strings (`"0x018A"`, own
  encoding per type).
- **Events are partial** — they carry only the keys that changed (a lamp
  event is `{"state":"on"}` without `auto-state`). Apply **merge** by addr,
  not replace.
- No `addr` — subscribes to all devices; with `addr` — only one.
- Events arrive on the same socket as `{"event":"statuses",...}`.

---

### Common quirks (all commands)

- **One session.** After `authorize` no re-authorization is needed; all
  requests go over one socket.
- **`detailed` is per-request.** Not sticky to the session: mark every
  request/subscription with `status:"detailed"` yourself. Without it, no
  status comes through (`get-devices`/`status-get` — no `status` key;
  events — hex).
- **Cloud does not answer WS ping.** A client `ping_interval` drops the
  connection on `keepalive ping timeout` — no pong arrives. Disable pings
  (`ping_interval=None`); keep the connection alive with periodic
  `get-devices` instead.
- **5-minute idle timeout.** Idle with no packets: server closes the
  session **without a close frame** (`no close frame received or sent`).
  Any request resets the timer; polling more often than every 5 min keeps
  the session alive. Keep the client `close_timeout` small.
- **`type:"json"` quirk.** Such widgets send `"status":{{...}` (doubled
  `{`) in the `detailed` response — breaks parsing of **the whole** frame.
  Fix by replacing `"status":{{` with `"status":{"_raw":{` before
  `json.loads`. Without `detailed` there's no status, so the quirk doesn't
  appear.
- **Control characters.** Text statuses (long-text widgets) contain tab,
  newline, etc. Strip the range `\x00`-`\x08`, `\x0b`, `\x0c`, `\x0e`-`\x1f`
  before `json.loads`.
- **`addr` format** — `MODULE_ID:ADDR`. One physical module hosts several
  devices under different `ADDR`. IDs can be large (`2048:247`) — split on
  `:`, don't assume any particular range.
- **Which key holds the value depends on type** — there is no single
  convention. See the per-type `API` section in
  [device-types/device_types.md](device-types/_device_types.md).

### Performance (stand, cloud)

| Operation | Time | Traffic |
|---|---|---|
| `get-devices status:detailed` | 160-210 ms | 11.4 KB / 59 devices |
| connect + authorize | ~200-250 ms | once per connection |

---

## HTTP

Endpoint (no session):

```
http://<IPADDR>/API2/    or    http://de-mg.local/API2/
```

POST with a JSON body. Instead of `authorize` — an `"API-KEY"` field in
**every** request. `status-subscribe` is unavailable (push is WebSocket
only). The `detailed` rule is the same as over WS.

**get-devices:**
```json
{"request": "get-devices", "API-KEY": "YOUR_API_KEY", "status": "detailed"}
```
**status-get:**
```json
{"request": "status-get", "API-KEY": "YOUR_API_KEY", "addr": "33:200", "status": "detailed"}
```
**status-set:**
```json
{"request": "status-set", "API-KEY": "YOUR_API_KEY", "addr": "1:1", "status": {"state": "on"}}
```

**Nuances:**
- Every request is independent — `API-KEY` is always required, no session.
- No push events (`status-subscribe` — WebSocket only).
- Responses have the same JSON shape as over WS (`response`, `devices`,
  `found`).
- Documented for local access; cloud HTTP has not been tested.

---

## cURL

`Content-Type: application/json`, `-d` implies POST.

**get-devices:**
```bash
curl -H 'Content-Type: application/json' \
  -d '{"request":"get-devices","API-KEY":"YOUR_API_KEY","status":"detailed"}' \
  'http://de-mg.local/API2/'
```

**status-get (one device):**
```bash
curl -H 'Content-Type: application/json' \
  -d '{"request":"status-get","API-KEY":"YOUR_API_KEY","addr":"33:200","status":"detailed"}' \
  'http://de-mg.local/API2/'
```

**status-set (turn on):**
```bash
curl -H 'Content-Type: application/json' \
  -d '{"request":"status-set","API-KEY":"YOUR_API_KEY","addr":"1:1","status":{"state":"on"}}' \
  'http://de-mg.local/API2/'
```

**status-set (climate setpoint):**
```bash
curl -H 'Content-Type: application/json' \
  -d '{"request":"status-set","API-KEY":"YOUR_API_KEY","addr":"33:200","status":{"state":"on","setpoint-heat":21.0}}' \
  'http://de-mg.local/API2/'
```

---

## Python examples

`pip install websockets`. All examples share the `_clean` helper (fixes the
`{{` quirk and strips control characters) and `connect_authorize`.

### Connect + authorize

```python
import asyncio, json, re, ssl, websockets

SERIAL = "a1b2c3d4"
API_KEY = "YOUR_API_KEY"
URL = f"wss://{SERIAL}.in.larnitech.com:8443/api"

def _clean(raw: str) -> dict:
    raw = raw.replace('"status":{{', '"status":{"_raw":{')          # type=json quirk
    raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)          # control chars
    return json.loads(raw)

async def connect_authorize():
    ctx = ssl.create_default_context()
    # ping_interval=None: cloud does not answer pings; close_timeout=1: no close frame.
    ws = await websockets.connect(URL, ssl=ctx, ping_interval=None, close_timeout=1)
    await ws.send(json.dumps({"request": "authorize", "key": API_KEY}))
    resp = _clean(await asyncio.wait_for(ws.recv(), timeout=10))
    if resp.get("result") != "success":
        raise RuntimeError(f"authorize rejected: {resp}")
    return ws
```

### Status request (get-devices / status-get)

```python
async def read_all():
    ws = await connect_authorize()
    async with ws:
        await ws.send(json.dumps({"request": "get-devices", "status": "detailed"}))
        data = _clean(await asyncio.wait_for(ws.recv(), timeout=15))
        for d in data["devices"]:
            print(d["addr"], d["type"], d.get("name"), d.get("status"))

async def read_one(addr):
    ws = await connect_authorize()
    async with ws:
        await ws.send(json.dumps({"request": "status-get", "addr": addr, "status": "detailed"}))
        data = _clean(await asyncio.wait_for(ws.recv(), timeout=15))
        return data["devices"][0]["status"] if data.get("found") else None

asyncio.run(read_all())
```

### Set status (status-set)

```python
async def set_state(addr, status):
    ws = await connect_authorize()
    async with ws:
        await ws.send(json.dumps({"request": "status-set", "addr": addr, "status": status}))
        # Object form replies with a success flag; loop until the status-set reply.
        for _ in range(10):
            msg = _clean(await asyncio.wait_for(ws.recv(), timeout=15))
            if msg.get("response") == "status-set":
                return msg["devices"]        # [{"addr": ..., "success": true}]

asyncio.run(set_state("1:1", {"state": "on"}))     # on/off
asyncio.run(set_state("585:17", {"level": 50}))    # dimmer brightness
```

### Subscribe (status-subscribe)

```python
async def subscribe_and_listen():
    ws = await connect_authorize()
    async with ws:
        await ws.send(json.dumps({"request": "status-subscribe", "status": "detailed"}))
        _clean(await asyncio.wait_for(ws.recv(), timeout=15))       # subscribe reply

        async for raw in ws:                                        # push events
            msg = _clean(raw)
            if msg.get("event") == "statuses":
                for d in msg["devices"]:
                    # Events are partial - merge per addr into your own cache.
                    print("changed:", d["addr"], d["status"])

asyncio.run(subscribe_and_listen())
```

> **Keepalive.** A long-lived subscription idles and closes after ~5 min.
> In production, run `get-devices` every ~2 min in parallel (resets the
> idle timer and guards against missed events).
