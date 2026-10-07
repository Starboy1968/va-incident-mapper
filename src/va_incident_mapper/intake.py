"""Load a file downloaded from web/intake.html into the incident log."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from . import data

SCHEMA = "va-incident-mapper-intake/1"


def load(path: str | Path) -> dict[str, Any]:
    """Read and validate an intake file. Raises ValueError with a plain message."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"intake file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"intake file is not valid JSON ({exc.msg})") from exc
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise ValueError(f"not an intake file (expected schema {SCHEMA})")
    types = raw.get("attack_types") or []
    if not types:
        raise ValueError("intake file has no attack types; reopen the form and choose at least one")
    known = data.attacks()
    bad = [t for t in types if t not in known]
    if bad:
        raise ValueError("unknown attack type(s): " + ", ".join(bad))
    return raw


def _date(value: str) -> str:
    """Return a valid ISO date/time string or ''."""
    if not value:
        return ""
    try:
        datetime.fromisoformat(value)
        return value
    except ValueError:
        return ""


def to_append_kwargs(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate an intake payload into arguments for store.append()."""
    lines = ["Source: victim intake form."]
    first, last = _date(raw.get("occurred_first", "")), _date(raw.get("occurred_last", ""))
    if first or last:
        lines.append(f"First occurrence: {first or 'unknown'}. Most recent: {last or 'unknown'}.")
    lines.append("Still ongoing." if raw.get("ongoing") else "Not marked as ongoing.")
    if raw.get("frequency"):
        lines.append(f"Frequency: {raw['frequency']}.")
    if raw.get("know_in_person"):
        lines.append(f"Knows sender in person: {raw['know_in_person']}.")
    if raw.get("told_to_stop") == "yes":
        blocked = _date(raw.get("blocked_on", ""))
        lines.append("Told sender to stop or blocked them" + (f" on {blocked}." if blocked else "."))
    elif raw.get("told_to_stop") == "no":
        lines.append("Has not told sender to stop or blocked them.")
    if str(raw.get("money_lost") or "").strip() not in ("", "0"):
        lines.append(f"Money lost (USD): {raw['money_lost']}.")
    if (raw.get("impact") or "").strip():
        lines.append(f"Impact: {raw['impact'].strip()}")
    if raw.get("feelings"):
        lines.append("Felt at the time: " + "; ".join(raw["feelings"]) + ".")
    if (raw.get("feelings_text") or "").strip():
        lines.append(f"In their words: {raw['feelings_text'].strip()}")
    if raw.get("evidence_have"):
        lines.append("Evidence on hand: " + "; ".join(raw["evidence_have"]) + ".")
    if raw.get("actions_taken"):
        lines.append("Actions already taken: " + "; ".join(raw["actions_taken"]) + ".")
    # Reporter contact details (raw["reporter"]) are deliberately NOT imported.
    files = [f for f in raw.get("evidence_files") or [] if f.get("sha256")]
    if files:
        lines.append(
            "Evidence fingerprints (SHA-256): "
            + "; ".join(f"{f.get('name', 'file')} = {f['sha256']}" for f in files) + "."
        )
    if raw.get("agency"):
        lines.append(f"Report prepared for: {raw['agency']}.")
    if raw.get("requests"):
        lines.append("Requests to agency: " + "; ".join(raw["requests"]) + ".")
    messages = [
        {"account": m.get("account") or "unknown", "at": m.get("at") or "", "text": m.get("text") or ""}
        for m in raw.get("messages") or []
        if (m.get("text") or "").strip()
    ]
    return {
        "summary": (raw.get("summary") or "").strip() or "Reported through the intake form.",
        "attack_types": list(raw["attack_types"]),
        "occurred_at": first or None,
        "platform": raw.get("platform") or "",
        "accounts": list(raw.get("accounts") or []),
        "notes": " ".join(lines),
        "messages": messages,
    }
