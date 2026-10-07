"""Append-only, hash-chained incident log (JSON Lines).

Each entry stores the SHA-256 of the previous entry, so editing or deleting an
earlier line breaks verification. This shows tampering after the fact. It does
not prove an incident happened; it is a record-keeping aid.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import analyze, data

GENESIS = "0" * 64
DEFAULT_LOG = "incidents.jsonl"


def log_path(explicit: str | None = None) -> Path:
    return Path(explicit or os.environ.get("VA_INCIDENT_LOG") or DEFAULT_LOG)


def _digest(entry: dict[str, Any]) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_all(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    with path.open("r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{n}: not valid JSON ({exc.msg})") from exc
    return entries


def append(
    path: Path,
    *,
    summary: str,
    attack_types: list[str],
    occurred_at: str | None = None,
    platform: str = "",
    accounts: list[str] | None = None,
    evidence_files: list[str] | None = None,
    notes: str = "",
    messages: list[dict[str, str]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate and append one incident. Returns the stored entry."""
    if not summary.strip():
        raise ValueError("summary is required")
    if not attack_types:
        raise ValueError("at least one attack type is required")
    known = data.attacks()
    for t in attack_types:
        if t not in known:
            raise ValueError(f"unknown attack type: {t}")
    if occurred_at:
        try:
            datetime.fromisoformat(occurred_at)
        except ValueError as exc:
            raise ValueError("occurred_at must be ISO 8601, e.g. 2026-03-01T14:30:00-05:00") from exc

    evidence = []
    for f in evidence_files or []:
        p = Path(f)
        if not p.is_file():
            raise ValueError(f"evidence file not found: {f}")
        evidence.append({"name": p.name, "sha256": sha256_file(p), "bytes": p.stat().st_size})

    msgs = []
    for m in messages or []:
        text = (m.get("text") or "").strip()
        if not text:
            raise ValueError("each message needs text")
        msgs.append({"account": (m.get("account") or "unknown").strip(), "at": (m.get("at") or "").strip(), "text": text})

    entries = read_all(path)
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    entry: dict[str, Any] = {
        "seq": len(entries) + 1,
        "id": uuid.uuid4().hex[:12],
        "logged_at": stamp.isoformat(timespec="seconds"),
        "occurred_at": occurred_at or "",
        "platform": platform,
        "accounts": accounts or [],
        "summary": summary.strip(),
        "attack_types": attack_types,
        "evidence": evidence,
        "notes": notes,
        "messages": msgs,
        "analysis": analyze.analyze_messages(msgs),
        "prev_hash": entries[-1]["hash"] if entries else GENESIS,
    }
    entry["hash"] = _digest(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def verify(path: Path) -> list[str]:
    """Return problems found in the hash chain (empty list means intact)."""
    problems: list[str] = []
    prev = GENESIS
    for i, entry in enumerate(read_all(path), 1):
        if entry.get("seq") != i:
            problems.append(f"entry {i}: sequence number is {entry.get('seq')}, expected {i}")
        if entry.get("prev_hash") != prev:
            problems.append(f"entry {i}: previous-hash link is broken")
        if entry.get("hash") != _digest(entry):
            problems.append(f"entry {i}: contents do not match stored hash")
        prev = entry.get("hash", "")
    return problems
