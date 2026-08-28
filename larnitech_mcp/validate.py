"""Pre-flight checks for `status-set`.

Deliberately narrow. The device-type wiki is the source of truth for how a
type behaves, and `set_device` attaches that type's own quirk list to every
preview — so this module does **not** try to mirror the wiki. It only
encodes the handful of facts that are (a) confirmed live, (b) mechanically
checkable, and (c) cause a *silent* wrong result rather than an error the
controller would report itself.

Anything softer than that belongs in the docs, not here: a second copy of
the rules in code drifts from the wiki, and a stale rule is worse than no
rule (this module previously shipped a `valve` warning that recommended the
opposite of what live testing later established).

`check` returns (errors, warnings): errors block the write, warnings ride
along in the preview so the user sees them before confirming.
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
}

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
