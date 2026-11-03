"""Pre-flight checks for `status-set`.

`set_device` writes as soon as these pass, so this is the gate: a malformed
or out-of-range command is rejected here and never reaches the controller.

Every rule encodes a value **documented** in the device-type wiki — a
vocabulary, a range, a read-only type, or a confirmed silent-failure trap.
Where the device reports its own bound (an AC's `t-min`/`t-delta`, a
climate zone's `modes`), that wins over any default, since widgets are
configured individually. Undocumented keys and types pass through
unchecked rather than guessed at: a second copy of the rules drifts from the
wiki, and a stale rule is worse than no rule (this module once shipped a
`valve` warning that recommended the opposite of what live testing later
established). Change a rule here only together with its doc.

`check` returns (errors, warnings): errors block the write, warnings ride
along in the result.
"""
from __future__ import annotations

import re

ADDR_RE = re.compile(r"^\d+:\d+$")

# AC/conditioner reject anything outside this set outright with
# {"code":9,"description":"set-status has invalid parameter"}.
AC_FAN = ("auto", "low", "middle", "high")

# Setting state/mode without target in the same call resets target to -128.
TARGET_SENTINEL_TYPES = ("ac", "conditioner", "fancoil", "valve-heating", "climate-control")

PERCENT_KEYS = {
    "dimmer-lamp": ("level", "color-temp"),
    "rgb-lamp": ("level", "hue", "saturation"),
    "fancoil": ("fan",),
    "vent": ("fan",),
    "blinds": ("position", "target"),
    "speaker": ("volume",),
}

# Documented read-only: a write has nothing to land on.
READ_ONLY_TYPES = (
    "humidity-sensor", "co2-sensor", "illumination-sensor", "percent-sensor",
    "float-sensor", "current-sensor", "voltage-sensor",
    "mic", "security-card-reader", "rtsp",
)

# `state` documented as plain on/off.
ON_OFF_TYPES = (
    "ac", "climate-control", "dimmer-lamp", "lamp", "light-scheme", "script", "ventilation",
)

CLIMATE_MODES = ("heat", "cool", "auto")  # climate-control, confirmed live

SETPOINT_TYPES = ("ac", "conditioner", "fancoil", "valve-heating", "climate-control", "ventilation")
SETPOINT_KEYS = ("target", "setpoint-heat", "setpoint-cool", "setpoint-warm-floor")

# AC setpoint bounds when the widget does not report its own (XML defaults).
AC_T_MIN, AC_T_DELTA = 16.0, 16.0

# An unrecognised speaker `state` is not rejected by the controller — it
# drives the widget into `error` (BUG-009). Only the confirmed vocabulary.
SPEAKER_STATES = ("play", "playing", "pause", "stop", "next", "previous")
SPEAKER_PRIORITY = (0, 250)

# Motorized types read their position as a participle but are driven with a
# verb. Writing the read vocabulary back is acked with success:true and then
# silently ignored — the single nastiest confirmed failure mode in the base.
VERB_DRIVEN_TYPES = ("gate", "jalousie")
VERB_FORMS = {"opened": "open", "closed": "close"}

# Types whose status carries no semantic keys at all — only an opaque `hex`
# blob (or nothing). Key-level reasoning does not apply to them.
HEX_ONLY_TYPES = ("switch",)
HEX_ONLY_VIRTUAL_SUBTYPES = ("prf", "sunrise", "jalousie", "jalousie120", "gate", "gate120")

# Writes these types re-evaluate on their own, landing *after* a too-quick
# second key in the same frame. Each entry: (trigger keys, key that loses).
# See the per-type wiki Notes for the confirmed sequences.
SEQUENCE_REQUIRED = {
    "vent": ("state", "fan"),
    "fancoil": ("mode", "state"),
}


def check_addr(addr: str) -> list[str]:
    if not isinstance(addr, str) or not ADDR_RE.match(addr.strip()):
        return [f"addr must look like MODULE:ADDR (e.g. 1:101), got {addr!r}"]
    return []


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _bound(raw, default: float) -> float:
    """A device-reported bound (sent as a string, e.g. "10"), or the default."""
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def is_hex_only(device: dict) -> bool:
    dtype = (device.get("type") or "").lower()
    sub_type = (device.get("sub-type") or device.get("sub_type") or "").lower()
    if dtype in HEX_ONLY_TYPES:
        return True
    return dtype == "virtual" and sub_type in HEX_ONLY_VIRTUAL_SUBTYPES


def check(device: dict, status: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(status, dict) or not status:
        return ["status must be a non-empty object, e.g. {\"state\": \"on\"}"], []
    bad_keys = [k for k in status if not isinstance(k, str)]
    if bad_keys:
        errors.append(f"status keys must be strings, got {bad_keys!r}")

    dtype = (device.get("type") or "").lower()
    sub_type = (device.get("sub-type") or device.get("sub_type") or "").lower()
    current = device.get("status") if isinstance(device.get("status"), dict) else {}

    if dtype in READ_ONLY_TYPES:
        errors.append(f"{dtype} is read-only — there is nothing to write to")
        return errors, warnings

    if is_hex_only(device):
        label = f"{dtype}/{sub_type}" if sub_type else dtype
        errors.append(
            f"{label} carries no semantic status keys — its status is an opaque `hex` blob "
            f"(got {sorted(status)}). Writing named keys to it does nothing; check "
            f"get_docs(\"{dtype}\") for what this type actually supports"
        )
        return errors, warnings

    # Keys the device does not currently report are the usual cause of a
    # silent no-op: the controller accepts the frame and ignores the key.
    # Skipped when the device is reporting a fault instead of a normal status.
    if current and "malfunction" not in current:
        unknown = [k for k in status if k not in current]
        if unknown:
            warnings.append(
                f"{', '.join(unknown)} not present in this device's current status — "
                "may be unsupported and silently ignored"
            )
    if "malfunction" in current:
        warnings.append(
            f"device is currently reporting a fault (malfunction={current['malfunction']!r}) "
            "instead of a normal status — writes may not behave normally"
        )

    if dtype in VERB_DRIVEN_TYPES and "state" in status:
        value = status["state"]
        if isinstance(value, str) and value.lower() in VERB_FORMS:
            want = VERB_FORMS[value.lower()]
            errors.append(
                f"{dtype} is driven with the verb form: write state={want!r}, not {value!r}. "
                f"Writing the read vocabulary back is acknowledged with success:true and then "
                f"silently ignored — the device never moves"
            )

    if dtype in ON_OFF_TYPES and "state" in status and status["state"] not in ("on", "off"):
        errors.append(f"{dtype}.state is \"on\" or \"off\", got {status['state']!r}")

    if dtype in SETPOINT_TYPES:
        for key in SETPOINT_KEYS:
            if key in status and not _number(status[key]):
                errors.append(f"{dtype}.{key} is a temperature in °C — a number, got {status[key]!r}")

    if dtype == "ac" and _number(status.get("target")):
        low = _bound(device.get("t-min"), AC_T_MIN)
        high = low + _bound(device.get("t-delta"), AC_T_DELTA)
        if not low <= status["target"] <= high:
            errors.append(
                f"ac.target {status['target']!r} is outside this unit's range "
                f"{low:g}..{high:g} °C (t-min + t-delta)"
            )

    if dtype == "climate-control" and "mode" in status:
        value = status["mode"]
        if value not in CLIMATE_MODES:
            errors.append(f"climate-control.mode is one of {', '.join(CLIMATE_MODES)}, got {value!r}")
        elif isinstance(device.get("modes"), list) and value not in device["modes"]:
            warnings.append(
                f"mode {value!r} is not in this zone's modes {device['modes']} — if the active "
                "automation cannot do it, the zone silently does nothing"
            )

    if dtype == "speaker":
        if "state" in status and status["state"] not in SPEAKER_STATES:
            errors.append(
                f"speaker.state accepts {', '.join(SPEAKER_STATES)}, got {status['state']!r} — "
                "anything else is not rejected but drives the widget into `error` (BUG-009)"
            )
        if "priority" in status:
            low, high = SPEAKER_PRIORITY
            value = status["priority"]
            if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
                errors.append(f"speaker.priority is an integer {low}-{high}, got {value!r}")

    if dtype in ("ac", "conditioner") and "fan" in status:
        value = status["fan"]
        if not isinstance(value, str) or value.lower() not in AC_FAN:
            errors.append(
                f"{dtype}.fan accepts only {', '.join(AC_FAN)} (got {value!r}); "
                "numbers, 'medium' and 'silent' are rejected by the controller"
            )

    for key in PERCENT_KEYS.get(dtype, ()):  # 0-100 integer percent, not 0.0-1.0
        if key not in status:
            continue
        value = status[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{dtype}.{key} must be a number 0-100, got {value!r}")
        elif not 0 <= value <= 100:
            errors.append(f"{dtype}.{key} is a 0-100 percent, got {value!r}")
        elif dtype == "rgb-lamp" and key == "hue":
            warnings.append("rgb-lamp.hue is a percent of the colour wheel, not degrees — divide degrees by 3.6")
        elif dtype == "blinds":
            warnings.append(
                f"blinds {key} is inverted from the usual convention: 0 = fully OPEN, "
                f"100 = fully CLOSED (writing {value!r})"
            )

    # Two keys the controller re-evaluates against each other must not share
    # one frame — the second one loses. Steps + delay_after handle this.
    trigger_and_loser = SEQUENCE_REQUIRED.get(dtype)
    if trigger_and_loser:
        trigger, loser = trigger_and_loser
        if trigger in status and loser in status:
            errors.append(
                f"{dtype}: {trigger!r} and {loser!r} cannot be written in the same call — "
                f"the controller re-evaluates after {trigger!r} and {loser!r} is lost. "
                f"Send them as two steps ~1s apart: "
                f"[{{\"status\": {{\"{trigger}\": ...}}, \"delay_after\": 1.0}}, "
                f"{{\"status\": {{\"{loser}\": ...}}}}]"
            )

    # Clearing an automation makes the channel re-run its own on/off logic,
    # which lands after an `off` sent in the same burst.
    if dtype in ("valve-heating", "fancoil", "vent") and "automation" in status and "state" in status:
        errors.append(
            f"{dtype}: clearing/changing 'automation' together with 'state' in one call does not "
            "stick — the channel re-evaluates itself right after and overrides the state. "
            "Send as two steps ~1s apart: automation first, then state"
        )

    if dtype in TARGET_SENTINEL_TYPES and ("state" in status or "mode" in status):
        if "target" not in status and "target" in current:
            warnings.append(
                "setting state/mode without target in the same call resets target to -128 — "
                f"include target (currently {current.get('target')!r}) to keep it"
            )

    if dtype == "fancoil" and "target" in status and "automation" not in current:
        warnings.append(
            "fancoil target may be silently ignored while no named automation is active "
            "(observed live, unconfirmed) — verify the value actually landed"
        )

    if dtype == "lamp" and sub_type == "lock" and "state" in status:
        warnings.append("lamp/lock polarity is inverted: state=off means LOCKED, state=on means unlocked")

    if dtype == "valve" and "state" in status:
        value = status["state"]
        if isinstance(value, str) and value.lower() in ("opened", "closed"):
            errors.append(
                f"bare `valve` reads its state as opened/closed but writing that vocabulary back "
                f"is confirmed NOT to work ({value!r} was not even acknowledged). Try on/off, or "
                f"the open/close verb form that drives gate/jalousie"
            )

    return errors, warnings
