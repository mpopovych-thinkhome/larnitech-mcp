"""Non-blocking status watching over a kept-open subscription.

Start a watch, let the user act on the physical system, read what changed —
`watch_read` never blocks waiting for a timer to expire, it drains whatever
has arrived so far.

Two background tasks per watch share one authorized socket:
  - a reader, which owns `recv` and buffers `statuses` events
  - a keepalive, which sends a bare `get-devices` every 2 minutes, because
    the controller drops an idle session after ~5 minutes without ever
    sending a close frame

Only the reader calls `recv`; the keepalive only sends. Splitting them this
way avoids cancelling a pending `recv` on every poll interval.
"""
from __future__ import annotations

import asyncio
import itertools
import time

from .client import LarnitechError, Session

KEEPALIVE_SECONDS = 120

_watches: dict[str, "Watch"] = {}
_ids = itertools.count(1)


class Watch:
    def __init__(self, object_name: str, obj: dict, key: str, addr: str | None = None):
        self.id = f"w{next(_ids)}"
        self.object_name = object_name
        self.addr = addr
        self._obj = obj
        self._key = key
        self._session: Session | None = None
        self._tasks: list[asyncio.Task] = []
        self.meta: dict[str, dict] = {}      # addr -> name/type/area/sub_type
        self.baseline: dict[str, dict] = {}  # addr -> status when the watch opened
        self.current: dict[str, dict] = {}   # addr -> latest merged status
        self.events: list[dict] = []         # buffered, drained by read()
        self.started_at = time.time()
        self.events_seen = 0
        self.keepalives = 0
        self.error: str | None = None
        self.stopped = False

    # --- lifecycle -------------------------------------------------------

    async def start(self) -> None:
        session = Session(self._obj, self._key)
        await session.open()
        self._session = session

        # Subscribe responses and events are thin (addr + status), so take the
        # baseline from a detailed snapshot, which also carries name/type/area.
        snapshot = await session.request({"request": "get-devices", "status": "detailed"})
        for device in snapshot.get("devices", []):
            addr = device.get("addr")
            if not addr or (self.addr and addr != self.addr):
                continue
            meta = {k: device[k] for k in ("name", "type", "area") if device.get(k)}
            if device.get("sub-type"):
                meta["sub_type"] = device["sub-type"]
            self.meta[addr] = meta
            status = device.get("status")
            self.baseline[addr] = dict(status) if isinstance(status, dict) else {"_raw": status}
            self.current[addr] = dict(self.baseline[addr])

        subscribe: dict = {"request": "status-subscribe", "status": "detailed"}
        if self.addr:
            subscribe["addr"] = self.addr
        await session.request(subscribe)

        self._tasks = [
            asyncio.create_task(self._read_loop()),
            asyncio.create_task(self._keepalive_loop()),
        ]

    async def stop(self) -> dict:
        self.stopped = True
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        if self._session is not None:
            await self._session.close()
            self._session = None
        return self.summary()

    # --- background tasks ------------------------------------------------

    async def _read_loop(self) -> None:
        try:
            while not self.stopped:
                message = await self._session.recv_event(timeout=None)
                if message is None:          # undecodable frame, keep going
                    continue
                if message.get("event") == "statuses":
                    self._ingest(message.get("devices") or [])
        except asyncio.CancelledError:
            raise
        except LarnitechError as err:
            self.error = str(err)
        except Exception as err:             # noqa: BLE001 - surface, don't crash the server
            self.error = f"{type(err).__name__}: {err}"

    async def _keepalive_loop(self) -> None:
        try:
            while not self.stopped:
                await asyncio.sleep(KEEPALIVE_SECONDS)
                await self._session.send({"request": "get-devices"})
                self.keepalives += 1
        except asyncio.CancelledError:
            raise
        except LarnitechError as err:
            self.error = self.error or f"keepalive failed: {err}"

    # --- event handling --------------------------------------------------

    def _ingest(self, devices: list[dict]) -> None:
        at = round(time.time() - self.started_at, 1)
        for device in devices:
            addr = device.get("addr")
            if not addr or (self.addr and addr != self.addr):
                continue
            status = device.get("status")
            if not isinstance(status, dict):
                status = {"_raw": status}
            previous = self.current.setdefault(addr, {})
            changed = {
                k: {"from": previous.get(k), "to": v}
                for k, v in status.items()
                if previous.get(k) != v
            }
            if not changed:
                continue
            previous.update(status)
            self.events_seen += 1
            base = self.baseline.get(addr, {})
            self.events.append({
                "at": at,
                "addr": addr,
                **self.meta.get(addr, {}),
                "changed": changed,
                "new_keys": [k for k in changed if k not in base],
            })

    def drain(self) -> list[dict]:
        events, self.events = self.events, []
        return events

    def summary(self) -> dict:
        return {
            "watch_id": self.id,
            "object": self.object_name,
            "addr": self.addr,
            "watching": len(self.baseline),
            "running_for": round(time.time() - self.started_at, 1),
            "events_seen": self.events_seen,
            "keepalives": self.keepalives,
            "stopped": self.stopped,
            "error": self.error,
        }


# --- registry ------------------------------------------------------------


async def start(object_name: str, obj: dict, key: str, addr: str | None = None) -> Watch:
    watch = Watch(object_name, obj, key, addr)
    await watch.start()
    _watches[watch.id] = watch
    return watch


def get(watch_id: str) -> Watch:
    watch = _watches.get(watch_id)
    if watch is None:
        known = ", ".join(_watches) or "none"
        raise LarnitechError(f"unknown watch {watch_id!r} (active: {known})")
    return watch


async def stop(watch_id: str) -> dict:
    watch = get(watch_id)
    summary = await watch.stop()
    _watches.pop(watch_id, None)
    return summary


def active() -> list[dict]:
    return [w.summary() for w in _watches.values()]
