"""Modbus RTU framing for a Larnitech `com-port`.

The controller passes a raw frame onto the port's bus when it arrives as the
legacy string status (`"0x01060001002399D3"`, CRC included), and reports every
frame it RECEIVES back as the port's `hex` status — the device's answers, not
the requests. So a request is built here, sent as-is, and its answer has to be
picked out of whatever else the bus carries (the controller's own script polls
the same bus). Verified 2026-11-03 on object 190 — see `com-port.md` in the
knowledge base.

Kept in step with the Home Assistant integration's `modbus.py` (ha-larnitech),
which was verified on the same bus — change both together.
"""
from __future__ import annotations

import struct

READ_FUNCTIONS = (3, 4)
WRITE_FUNCTIONS = (6, 16)


class ModbusExceptionResponse(Exception):
    """The device answered with a Modbus exception (function | 0x80)."""

    def __init__(self, code: int) -> None:
        super().__init__(f"Modbus exception code {code}")
        self.code = code


def crc16(data: bytes) -> bytes:
    """Modbus CRC-16 (poly 0xA001, init 0xFFFF), low byte first."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return struct.pack("<H", crc)


def build_request(
    slave: int, function: int, address: int, count: int = 1, values: list[int] | None = None
) -> bytes:
    if function in READ_FUNCTIONS:
        pdu = struct.pack(">BBHH", slave, function, address, count)
    elif function == 6:
        pdu = struct.pack(">BBHH", slave, function, address, values[0])
    else:
        pdu = struct.pack(">BBHHB", slave, function, address, len(values), 2 * len(values))
        pdu += struct.pack(f">{len(values)}H", *values)
    return pdu + crc16(pdu)


def parse_answer(request: bytes, answer: bytes) -> list[int] | None:
    """What `answer` says about `request`, or None if it answers something else.

    Read: the registers. Write: `[]` once the device confirms it. Bytes past the
    CRC are ignored — a write echo has come back with two extra zero bytes.

    shortcut: a frame is matched by slave, function and size only (a read
    answer carries no register address), so the script master reading the same
    slave with the same function and count at the same moment is
    indistinguishable from our own answer; nothing on the bus can tell them
    apart."""
    slave, function = request[0], request[1]
    if len(answer) < 5 or answer[0] != slave:
        return None
    if answer[1] == function | 0x80:
        if answer[3:5] != crc16(answer[:3]):
            return None
        raise ModbusExceptionResponse(answer[2])
    if answer[1] != function:
        return None
    if function in READ_FUNCTIONS:
        size = answer[2]
        count = struct.unpack(">H", request[4:6])[0]
        if size != 2 * count or answer[3 + size : 5 + size] != crc16(answer[: 3 + size]):
            return None
        return list(struct.unpack(f">{count}H", answer[3 : 3 + size]))
    # FC06 echoes the whole request; FC16 answers with its first six bytes.
    if function == 6:
        return [] if answer[:8] == request else None
    return [] if answer[:6] == request[:6] and answer[6:8] == crc16(answer[:6]) else None


def frame(raw) -> bytes | None:
    """A port's `hex` status (`"0x0103…"`) as bytes, or None."""
    if not isinstance(raw, str) or raw[:2].lower() != "0x":
        return None
    try:
        return bytes.fromhex(raw[2:])
    except ValueError:
        return None


def looks_like_answer(request: bytes, frame_: bytes | None) -> bool:
    if frame_ is None:
        return False
    try:
        return parse_answer(request, frame_) is not None
    except ModbusExceptionResponse:
        return True


def separator(request: bytes) -> bytes:
    """A harmless read whose answer can never equal `request`'s: the same
    register with a different count (different size), or a one-register read
    for a write (different function)."""
    slave, function, address = request[0], request[1], int.from_bytes(request[2:4], "big")
    if function in READ_FUNCTIONS:
        count = int.from_bytes(request[4:6], "big")
        return build_request(slave, function, address, count + 1 if count < 125 else count - 1)
    return build_request(slave, 3, address, 1)
