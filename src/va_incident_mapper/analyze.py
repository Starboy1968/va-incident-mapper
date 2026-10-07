"""Rough, offline language analysis for logged messages.

Three tools:
  * sentiment(): lexicon-based valence plus emotion-category counts
  * behaviors(): marker phrases for threat and harassment behaviors, each tied to attack types
  * compare(): side-by-side markers for different accounts (an observation, never attribution)

Limits: English only, no sarcasm or context understanding, easy to over- or under-match.
Treat output as a triage aid for a human reader, not as evidence of intent or identity.
"""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from importlib import resources
from typing import Any, Iterable

from . import mapper

TOKEN = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")
LEVELS = ("routine", "elevated", "high", "urgent")
DISCLAIMER = (
    "Keyword-based triage aid. It cannot read tone, sarcasm or context, and a match does not prove intent. "
    "Overlap between accounts is an observation, not proof that one person wrote them."
)


def _load(name: str) -> dict[str, Any]:
    with resources.files("va_incident_mapper").joinpath("data", name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def lexicon() -> dict[str, Any]:
    return _load("lexicon.json")


@lru_cache(maxsize=1)
def behavior_table() -> list[dict[str, Any]]:
    out = []
    for b in _load("behaviors.json")["behaviors"]:
        b = dict(b)
        b["_re"] = [re.compile(p, re.IGNORECASE) for p in b["patterns"]]
        out.append(b)
    return out


def validate() -> list[str]:
    """Check behaviors point at real attack types."""
    from . import data

    problems = []
    known = data.attacks()
    for b in behavior_table():
        for t in b["attack_types"]:
            if t not in known:
                problems.append(f"behavior {b['id']}: unknown attack type {t}")
        if not 1 <= b["weight"] <= 5:
            problems.append(f"behavior {b['id']}: weight must be 1-5")
    return problems


def _norm(text: str) -> str:
    return text.replace("’", "'")


def _matches_category(token: str, entries: list[str]) -> bool:
    for e in entries:
        if e.endswith("*"):
            if token.startswith(e[:-1]):
                return True
        elif token == e:
            return True
    return False


def sentiment(text: str) -> dict[str, Any]:
    """Valence from -1 (very hostile) to +1 (very positive), plus emotion counts and intensity cues."""
    lex = lexicon()
    tokens = TOKEN.findall(_norm(text).lower())
    neg, pos = lex["negative"], lex["positive"]
    boost, negators = lex["intensifiers"], set(lex["negators"])
    total = 0.0
    for i, tok in enumerate(tokens):
        base = neg.get(tok, pos.get(tok))
        if base is None:
            continue
        score = float(base)
        window = tokens[max(0, i - 3):i]
        for w in window:
            score *= boost.get(w, 1.0)
        if any(w in negators for w in window):
            score *= -0.6
        total += score
    valence = total / math.sqrt(total * total + 15) if total else 0.0
    emotions = {
        cat: sum(1 for t in tokens if _matches_category(t, entries))
        for cat, entries in lex["categories"].items()
    }
    letters = [c for c in text if c.isalpha()]
    caps_ratio = (sum(1 for c in letters if c.isupper()) / len(letters)) if len(letters) >= 10 else 0.0
    label = "very negative" if valence <= -0.6 else "negative" if valence <= -0.2 else "positive" if valence >= 0.2 else "neutral"
    return {
        "valence": round(valence, 3),
        "label": label,
        "emotions": emotions,
        "caps_ratio": round(caps_ratio, 2),
        "exclamations": text.count("!"),
        "words": len(tokens),
    }


def behaviors(text: str) -> list[dict[str, Any]]:
    """Return behavior markers found in `text`, each with the exact matched phrases."""
    found = []
    flat = _norm(text)
    for b in behavior_table():
        quotes: list[str] = []
        for rx in b["_re"]:
            for m in rx.finditer(flat):
                q = m.group(0).strip()
                if q and q.lower() not in (x.lower() for x in quotes):
                    quotes.append(q)
        if quotes:
            found.append({
                "id": b["id"], "name": b["name"], "weight": b["weight"],
                "quotes": quotes, "attack_types": b["attack_types"], "legal_note": b["legal_note"],
            })
    found.sort(key=lambda x: (-x["weight"], x["id"]))
    return found


def attention(found: Iterable[dict[str, Any]]) -> str:
    """Triage level from the strongest marker. A reading aid, not a risk prediction."""
    top = max((f["weight"] for f in found), default=0)
    if top >= 5:
        return "urgent"
    if top == 4:
        return "high"
    if top == 3:
        return "elevated"
    return "routine"


ATTENTION_NOTE = {
    "urgent": "Direct threat language present. If you are in danger, call 911 first, then preserve the message.",
    "high": "Strong coercion, tracking or exposure language present. Preserve evidence and consider reporting promptly.",
    "elevated": "Menacing or persistence language present. Keep logging; patterns matter.",
    "routine": "No high-weight markers matched. This does not mean nothing happened.",
}


def analyze(text: str) -> dict[str, Any]:
    found = behaviors(text)
    types: dict[str, int] = {}
    for f in found:
        for t in f["attack_types"]:
            types[t] = types.get(t, 0) + f["weight"]
    suggested = [t for t, _ in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))][:5]
    level = attention(found)
    return {
        "sentiment": sentiment(text),
        "behaviors": found,
        "suggested_attack_types": suggested,
        "attention": level,
        "attention_note": ATTENTION_NOTE[level],
        "disclaimer": DISCLAIMER,
    }


def analyze_messages(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Compact, reproducible summary stored with a log entry (no quotes duplicated)."""
    if not messages:
        return {}
    sents = [sentiment(m["text"]) for m in messages]
    counts: dict[str, int] = {}
    top_weight = 0
    for m in messages:
        for f in behaviors(m["text"]):
            counts[f["id"]] = counts.get(f["id"], 0) + len(f["quotes"])
            top_weight = max(top_weight, f["weight"])
    mean = sum(s["valence"] for s in sents) / len(sents)
    level = "urgent" if top_weight >= 5 else "high" if top_weight == 4 else "elevated" if top_weight == 3 else "routine"
    return {
        "lexicon_version": lexicon()["version"],
        "messages": len(messages),
        "valence_mean": round(mean, 3),
        "valence_min": min(s["valence"] for s in sents),
        "behaviors": dict(sorted(counts.items())),
        "attention": level,
    }


_STYLE_WORD = re.compile(r"[A-Za-z']+")


def style_profile(texts: list[str]) -> dict[str, float]:
    """Plain surface statistics. Descriptive only."""
    joined = " ".join(texts)
    words = _STYLE_WORD.findall(joined)
    sentences = [s for s in re.split(r"[.!?]+\s*", joined) if s.strip()]
    msgs = [t for t in texts if t.strip()]
    lower_start = sum(1 for t in msgs if t.strip()[0].islower())
    emoji = sum(1 for c in joined if ord(c) > 0x1F000)
    return {
        "messages": len(msgs),
        "avg_words_per_message": round(len(words) / max(1, len(msgs)), 1),
        "avg_word_length": round(sum(len(w) for w in words) / max(1, len(words)), 2),
        "avg_sentence_words": round(len(words) / max(1, len(sentences)), 1),
        "lowercase_start_rate": round(lower_start / max(1, len(msgs)), 2),
        "exclamations_per_message": round(joined.count("!") / max(1, len(msgs)), 2),
        "emoji_per_message": round(emoji / max(1, len(msgs)), 2),
    }


def compare(by_account: dict[str, list[str]]) -> dict[str, Any]:
    """Per-account markers plus pairwise overlap. Describes; never concludes identity."""
    per = {}
    for acct, texts in by_account.items():
        marks: dict[str, set[str]] = {}
        for t in texts:
            for f in behaviors(t):
                marks.setdefault(f["id"], set()).update(q.lower() for q in f["quotes"])
        per[acct] = {
            "marks": marks,
            "style": style_profile(texts),
            "valence": round(sum(sentiment(t)["valence"] for t in texts) / max(1, len(texts)), 3),
        }
    accts = list(per)
    pairs = []
    for i, a in enumerate(accts):
        for b in accts[i + 1:]:
            ids_a, ids_b = set(per[a]["marks"]), set(per[b]["marks"])
            shared = sorted(ids_a & ids_b)
            union = ids_a | ids_b
            identical = {}
            for bid in shared:
                common = per[a]["marks"][bid] & per[b]["marks"][bid]
                if common:
                    identical[bid] = sorted(common)
            pairs.append({
                "a": a, "b": b, "shared_behaviors": shared,
                "overlap": round(len(shared) / len(union), 2) if union else 0.0,
                "identical_phrases": identical,
            })
    pairs.sort(key=lambda p: (-p["overlap"], p["a"], p["b"]))
    return {
        "accounts": {a: {"behaviors": sorted(v["marks"]), "style": v["style"], "valence_mean": v["valence"]} for a, v in per.items()},
        "pairs": pairs,
        "caution": DISCLAIMER,
    }


def trend(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Escalation view across logged incidents that carry an analysis block."""
    rows = []
    for e in entries:
        a = e.get("analysis") or {}
        if not a:
            continue
        top = a.get("attention", "routine")
        rows.append({"seq": e["seq"], "when": e.get("occurred_at") or e["logged_at"], "valence": a["valence_mean"], "attention": top, "behaviors": list(a.get("behaviors", {}))})
    flags = []
    if len(rows) >= 2:
        first, last = rows[0], rows[-1]
        if LEVELS.index(last["attention"]) > LEVELS.index(first["attention"]):
            flags.append(f"Attention level rose from {first['attention']} (entry {first['seq']}) to {last['attention']} (entry {last['seq']}).")
        if last["valence"] < first["valence"] - 0.2:
            flags.append("Average sentiment became more negative over time.")
        new = set(last["behaviors"]) - set(first["behaviors"])
        if new:
            flags.append("New behavior markers appeared later: " + ", ".join(sorted(new)) + ".")
    return {"rows": rows, "flags": flags, "caution": DISCLAIMER}
