"""Suggest attack types from free text and map attack types to statutes."""

from __future__ import annotations

import re
from typing import Any, Iterable

from . import data

_ORDER = {"primary": 0, "possible": 1, "contested": 2, "civil": 3}


def suggest(text: str) -> list[tuple[str, int]]:
    """Rank attack types by how many of their keywords appear in `text`.

    Returns [(attack_id, hits)] with hits > 0, best first. This is a keyword aid
    for the person logging the incident; the person always picks the final types.
    """
    haystack = re.sub(r"\s+", " ", text.lower())
    scored: list[tuple[str, int]] = []
    for attack_id, attack in data.attacks().items():
        hits = sum(1 for kw in attack["keywords"] if kw in haystack)
        if hits:
            scored.append((attack_id, hits))
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored


def map_types(attack_ids: Iterable[str]) -> dict[str, Any]:
    """Map attack types to a de-duplicated, ranked statute list plus checklists.

    The strongest tier for a statute wins when several types cite it.
    """
    attacks = data.attacks()
    table = data.statutes()
    best: dict[str, str] = {}
    sources: dict[str, list[str]] = {}
    document: list[str] = []
    report_to: list[str] = []
    caveats: list[str] = []
    names: list[str] = []

    for attack_id in attack_ids:
        if attack_id not in attacks:
            raise KeyError(f"unknown attack type: {attack_id}")
        attack = attacks[attack_id]
        names.append(attack["name"])
        for ref in attack["statutes"]:
            sid, strength = ref["id"], ref["strength"]
            if sid not in best or _ORDER[strength] < _ORDER[best[sid]]:
                best[sid] = strength
            sources.setdefault(sid, [])
            if attack_id not in sources[sid]:
                sources[sid].append(attack_id)
        for target, items in ((document, attack["document"]), (report_to, attack["report_to"]), (caveats, attack["caveats"])):
            for item in items:
                if item not in target:
                    target.append(item)

    rows = []
    for sid, strength in best.items():
        s = table[sid]
        rows.append({
            "id": sid,
            "cite": s["cite"],
            "title": s["title"],
            "summary": s["summary"],
            "penalty": s["penalty"],
            "jurisdiction": s["jurisdiction"],
            "verified": s["verified"],
            "strength": strength,
            "from": sources[sid],
        })
    rows.sort(key=lambda r: (_ORDER[r["strength"]], r["jurisdiction"] != "VA", r["cite"]))
    return {
        "attack_types": list(attack_ids) if not isinstance(attack_ids, list) else attack_ids,
        "attack_names": names,
        "statutes": rows,
        "document": document,
        "report_to": report_to,
        "caveats": caveats,
    }
