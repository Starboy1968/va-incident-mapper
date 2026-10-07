"""Load and validate the bundled statute and attack-type tables."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

STRENGTHS = ("primary", "possible", "civil", "contested")


def _load(name: str) -> dict[str, Any]:
    with resources.files("va_incident_mapper").joinpath("data", name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def statutes_meta() -> dict[str, Any]:
    return _load("statutes.json")["_meta"]


@lru_cache(maxsize=1)
def statutes() -> dict[str, dict[str, Any]]:
    """Statutes keyed by id."""
    return {s["id"]: s for s in _load("statutes.json")["statutes"]}


@lru_cache(maxsize=1)
def attacks() -> dict[str, dict[str, Any]]:
    """Attack types keyed by id."""
    return {a["id"]: a for a in _load("attacks.json")["attacks"]}


def validate() -> list[str]:
    """Return a list of data problems (empty list means the tables are consistent)."""
    problems: list[str] = []
    table = statutes()
    for attack in attacks().values():
        for ref in attack["statutes"]:
            if ref["id"] not in table:
                problems.append(f"{attack['id']}: unknown statute id {ref['id']}")
            if ref["strength"] not in STRENGTHS:
                problems.append(f"{attack['id']}: bad strength {ref['strength']!r} on {ref['id']}")
        for key in ("name", "description", "keywords", "document", "report_to", "caveats"):
            if not attack.get(key):
                problems.append(f"{attack['id']}: missing {key}")
    for s in table.values():
        for key in ("cite", "title", "summary", "penalty", "jurisdiction"):
            if not s.get(key):
                problems.append(f"{s['id']}: missing {key}")
    return problems
