"""Build web/intake.html from web/intake.template.html and the JSON data tables.

Run from the repo root after changing any file in src/va_incident_mapper/data/:
    python tools/build_intake.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "va_incident_mapper" / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def render() -> str:
    st, at, lx, bh = load("statutes.json"), load("attacks.json"), load("lexicon.json"), load("behaviors.json")
    payload = {
        "statutes": {s["id"]: s for s in st["statutes"]},
        "attacks": at["attacks"],
        "lexicon": {k: lx[k] for k in ("negative", "positive", "intensifiers", "negators", "categories")},
        "behaviors": [{k: b[k] for k in ("id", "name", "weight", "patterns", "attack_types", "legal_note", "description")} for b in bh["behaviors"]],
        "verified": st["_meta"]["va_verified_on"],
    }
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    template = (ROOT / "web" / "intake.template.html").read_text(encoding="utf-8")
    return template.replace("__DATA__", blob)


def main():
    out = render()
    (ROOT / "web" / "intake.html").write_text(out, encoding="utf-8")
    print(f"wrote web/intake.html ({len(out):,} bytes)")


if __name__ == "__main__":
    main()
