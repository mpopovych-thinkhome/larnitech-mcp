"""Larnitech API2 WebSocket client.

Two usage shapes over one implementation:
  - `request_once` — one request over a pooled authorized socket, kept
    open for a few minutes so a burst of tool calls shares one connection.
    Used by the read/write tools.
  - `Session` — a kept-open authorized socket. Only `watch` needs this, to
    receive pushed `statuses` events.

Protocol details: `31_Larnitech/wiki/api2_protocol.md`. Per-device-type
quirks: `31_Larnitech/wiki/device-types/_device_types.md`.
"""
from __future__ import annotations

import asyncio
import json
import re
import ssl

import websockets
from websockets.exceptions import WebSocketException

from .config import DEFAULT_LOCAL_PORT, ConfigError

# Controller quirk: "json"-type widgets emit `"status":{{...}` with a doubled
# opening brace (invalid JSON: a key is expected after `{`). Braces stay
# balanced, so insert a placeholder key rather than dropping a brace.
_QUIRK_FROM = '"status":{{'
_QUIRK_TO = '"status":{"_raw":{'

# long-text widgets embed raw control characters (\t, \n, ...) unescaped inside
# JSON strings — invalid JSON, and it breaks the whole frame, taking every
# other device batched into it down with one bad widget.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

_MAX_FRAME = 8 * 1024 * 1024
_ssl_context: ssl.SSLContext | None = None


class LarnitechError(Exception):
    """Connection, protocol or controller-side failure."""


class LarnitechAuthError(LarnitechError):
    """Authorization rejected by the controller."""


def build_url(obj: dict) -> str:
    if obj.get("mode") == "cloud":
        serial = obj.get("serial")
        if not serial:
            raise ConfigError("cloud object has no serial")
        return f"wss://{serial}.in.larnitech.com:8443/api"
    host = obj.get("host")
    if not host:
        raise ConfigError("local object has no host")
    return f"ws://{host}:{obj.get('port') or DEFAULT_LOCAL_PORT}/api"


def clean(raw: str) -> dict:
    """Repair the two known frame-level quirks, then parse."""
    if _QUIRK_FROM in raw:
        raw = raw.replace(_QUIRK_FROM, _QUIRK_TO)
    raw = _CONTROL_CHARS.sub("", raw)
    return json.loads(raw)


class Session:
    """One authorized WebSocket."""

    def __init__(self, obj: dict, key: str):
        self._url = build_url(obj)
        self._key = key
        self._ws = None

    async def open(self) -> None:
        global _ssl_context
        # The cloud never answers WebSocket pings, so client-side keepalive
        # pings would drop the link on a false ping timeout; and it never sends
        # a close frame, so a normal close would hang waiting for one.
        kwargs = {
            "open_timeout": 15,
            "ping_interval": None,
            "close_timeout": 1,
            "max_size": _MAX_FRAME,
        }
        if self._url.startswith("wss"):
            if _ssl_context is None:
                _ssl_context = await asyncio.to_thread(ssl.create_default_context)
            kwargs["ssl"] = _ssl_context
        try:
            self._ws = await websockets.connect(self._url, **kwargs)
            await self._ws.send(json.dumps({"request": "authorize", "key": self._key}))
            resp = clean(await asyncio.wait_for(self._ws.recv(), timeout=15))
        except (OSError, WebSocketException, asyncio.TimeoutError) as err:
            await self.close()
            raise LarnitechError(f"cannot connect to {self._url}: {err}") from err
        if resp.get("result") != "success":
            await self.close()
            raise LarnitechAuthError(f"authorize rejected: {resp}")

    async def send(self, payload: dict) -> None:
        if self._ws is None:
            raise LarnitechError("not connected")
        try:
            await self._ws.send(json.dumps(payload))
        except (OSError, WebSocketException) as err:
            raise LarnitechError(f"send failed: {err}") from err

    async def request(self, payload: dict, timeout: float = 20) -> dict:
        """Send and wait for the matching `response` frame.

        Pushed `statuses` events share the socket and can arrive in between, so
        match on the response name rather than taking the next frame.
        """
        expect = payload["request"]
        await self.send(payload)
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise LarnitechError(f"{expect}: timed out after {timeout}s")
            try:
                raw = await asyncio.wait_for(self._ws.recv(), timeout=remaining)
            except (OSError, WebSocketException, asyncio.TimeoutError) as err:
                raise LarnitechError(f"{expect} failed: {err}") from err
            try:
                msg = clean(raw)
            except json.JSONDecodeError:
                continue  # undecodable frame; the answer may still be coming
            if msg.get("response") == expect:
                return msg

    async def recv_event(self, timeout: float) -> dict | None:
        """Next frame, or None on timeout. Undecodable frames are skipped."""
        try:
            raw = await asyncio.wait_for(self._ws.recv(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        except (OSError, WebSocketException) as err:
            raise LarnitechError(f"connection lost: {err}") from err
        try:
            return clean(raw)
        except json.JSONDecodeError:
            return None

    async def close(self) -> None:
        if self._ws is not None:
            ws, self._ws = self._ws, None
            try:
                await asyncio.wait_for(ws.close(), timeout=2)
            except BaseException:  # noqa: BLE001 - closing must never raise
                pass

    async def __aenter__(self) -> Session:
        await self.open()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()


# --- session pool --------------------------------------------------------

# An agent asks in bursts: a snapshot, then a couple of follow-up reads, then
# a write. Reconnecting for each costs a connect + authorize round trip
# (200-250 ms) and takes a fresh session slot on the controller, so an
# authorized socket is kept after a request and reused by the next one.
# Four minutes, deliberately under the controller's own ~5-minute idle
# timeout: the pool retires a socket while it is still known to be alive
# instead of handing out one the server has already dropped.
IDLE_TIMEOUT = 240.0
_REAP_INTERVAL = 20.0


class _Pooled:
    def __init__(self, session: Session):
        self.session = session
        # A response carries no request id, so two requests in flight on one
        # socket could take each other's answer. One at a time per controller.
        self.lock = asyncio.Lock()
        self.used = asyncio.get_running_loop().time()


_pool: dict[str, _Pooled] = {}
_pool_loop: asyncio.AbstractEventLoop | None = None
_reaper: asyncio.Task | None = None


async def _reap_loop() -> None:
    while _pool:
        await asyncio.sleep(_REAP_INTERVAL)
        now = asyncio.get_running_loop().time()
        for url, entry in list(_pool.items()):
            if entry.lock.locked() or now - entry.used <= IDLE_TIMEOUT:
                continue
            _pool.pop(url, None)
            await entry.session.close()


async def _pooled(obj: dict, key: str, url: str) -> _Pooled:
    global _pool_loop, _reaper
    loop = asyncio.get_running_loop()
    if _pool_loop is not loop:
        # A CLI command runs its own event loop; a socket cannot cross into it.
        _pool.clear()
        _pool_loop = loop
    entry = _pool.get(url)
    if entry is None:
        session = Session(obj, key)
        await session.open()
        entry = _pool[url] = _Pooled(session)
    if _reaper is None or _reaper.done():
        _reaper = loop.create_task(_reap_loop())
    return entry


async def request_once(obj: dict, key: str, payload: dict) -> dict:
    """One request over a kept-open authorized socket.

    The socket stays in the pool for `IDLE_TIMEOUT` after the request and the
    next call reuses it, so a burst of tool calls costs one connect, not one
    per call.
    """
    url = build_url(obj)
    for attempt in (1, 2):
        entry = await _pooled(obj, key, url)
        async with entry.lock:
            try:
                answer = await entry.session.request(payload)
            except LarnitechError:
                # The controller drops an idle session without sending a close
                # frame, so a dead socket only announces itself on use. Retire
                # it and try once more on a fresh one.
                _pool.pop(url, None)
                await entry.session.close()
                if attempt == 2:
                    raise
                continue
            entry.used = asyncio.get_running_loop().time()
            return answer
