"""Command-line interface: `va-incident-mapper`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, analyze, data, intake, mapper, report, store


def _print_statutes(rows: list[dict]) -> None:
    for s in rows:
        flag = "" if s["verified"] else "  (federal, not re-checked)"
        print(f"{STRENGTH_TAG.get(s.get('strength', ''), ''):<9}{s['cite']}  {s['title']}{flag}")
        print(f"         {s['summary']}")
        print(f"         Penalty: {s['penalty']}\n")


STRENGTH_TAG = {"primary": "[PRIMARY]", "possible": "[possible]", "civil": "[civil]", "contested": "[CONTEST]"}


def cmd_types(args) -> int:
    for a in data.attacks().values():
        print(f"{a['id']:<22} {a['name']}")
    return 0


def cmd_statutes(args) -> int:
    rows = [s for s in data.statutes().values() if not args.jurisdiction or s["jurisdiction"] == args.jurisdiction.upper()]
    _print_statutes(rows)
    return 0


def cmd_suggest(args) -> int:
    ranked = mapper.suggest(" ".join(args.text))
    if not ranked:
        print("No keyword matches. Run `types` to pick a type by hand.")
        return 1
    for attack_id, hits in ranked:
        print(f"{attack_id:<22} {hits} keyword hit(s)  {data.attacks()[attack_id]['name']}")
    return 0


def cmd_map(args) -> int:
    result = mapper.map_types(args.types)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print("Types: " + ", ".join(result["attack_names"]) + "\n")
    _print_statutes(result["statutes"])
    print("Caveats:")
    for c in result["caveats"]:
        print(f"  - {c}")
    print("\nNot legal advice. Review with a licensed attorney.")
    return 0


def parse_message(line: str) -> dict:
    """'@account | text' (optionally '@account | 2026-03-02T22:40:00-05:00 | text')."""
    parts = [p.strip() for p in line.split(" | ")]
    if len(parts) >= 3:
        return {"account": parts[0], "at": parts[1], "text": " | ".join(parts[2:])}
    if len(parts) == 2:
        return {"account": parts[0], "at": "", "text": parts[1]}
    return {"account": "unknown", "at": "", "text": line.strip()}


def _read_messages(args) -> list:
    msgs = [parse_message(m) for m in (args.message or [])]
    if args.messages_file:
        for line in Path(args.messages_file).read_text(encoding="utf-8").splitlines():
            if line.strip():
                msgs.append(parse_message(line))
    return msgs


def cmd_log(args) -> int:
    path = store.log_path(args.log)
    try:
        entry = store.append(
            path,
            summary=args.summary,
            attack_types=args.type,
            occurred_at=args.occurred,
            platform=args.platform or "",
            accounts=args.account,
            evidence_files=args.evidence,
            notes=args.note or "",
            messages=_read_messages(args),
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Logged incident {entry['seq']} (id {entry['id']}) to {path}")
    for ev in entry["evidence"]:
        print(f"  evidence {ev['name']} sha256={ev['sha256']}")
    if entry["analysis"]:
        a = entry["analysis"]
        print(f"  language: {a['messages']} message(s), sentiment {a['valence_mean']:+.2f}, attention {a['attention']}")
        if a["attention"] == "urgent":
            print("  " + analyze.ATTENTION_NOTE["urgent"])
    return 0


def cmd_import(args) -> int:
    path = store.log_path(args.log)
    try:
        kwargs = intake.to_append_kwargs(intake.load(args.file))
        entry = store.append(path, evidence_files=args.evidence, **kwargs)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Imported intake as incident {entry['seq']} (id {entry['id']}) into {path}")
    print(f"  types: {', '.join(entry['attack_types'])}; messages: {len(entry['messages'])}")
    if entry["analysis"]:
        a = entry["analysis"]
        print(f"  language: sentiment {a['valence_mean']:+.2f}, attention {a['attention']}")
        if a["attention"] == "urgent":
            print("  " + analyze.ATTENTION_NOTE["urgent"])
    return 0


def cmd_analyze(args) -> int:
    text = Path(args.file).read_text(encoding="utf-8") if args.file else " ".join(args.text)
    if not text.strip():
        print("error: give text or --file", file=sys.stderr)
        return 2
    r = analyze.analyze(text)
    if args.json:
        print(json.dumps(r, indent=2))
        return 0
    s = r["sentiment"]
    print(f"Sentiment: {s['label']} ({s['valence']:+.2f})  emotions: " + ", ".join(f"{k}={v}" for k, v in s["emotions"].items() if v) or "none")
    print(f"Attention: {r['attention'].upper()} - {r['attention_note']}\n")
    if r["behaviors"]:
        print("Behavior markers (weight, name, matched words):")
        for b in r["behaviors"]:
            print(f"  [{b['weight']}] {b['name']}: " + "; ".join(f'"{q}"' for q in b["quotes"]))
            print(f"      {b['legal_note']}")
        print("\nSuggested attack types: " + ", ".join(r["suggested_attack_types"]))
        print("Next: va-incident-mapper map " + " ".join(r["suggested_attack_types"][:3]))
    else:
        print("No behavior markers matched.")
    print("\n" + r["disclaimer"])
    return 0


def _accounts(entries) -> dict:
    by: dict = {}
    for e in entries:
        for m in e.get("messages", []):
            by.setdefault(m["account"], []).append(m["text"])
    return by


def cmd_compare(args) -> int:
    by = _accounts(store.read_all(store.log_path(args.log)))
    if args.account:
        by = {a: t for a, t in by.items() if a in args.account}
    if len(by) < 2:
        print("error: need logged messages from at least two accounts (use `log --message '@acct | text'`)", file=sys.stderr)
        return 2
    r = analyze.compare(by)
    if args.json:
        print(json.dumps(r, indent=2))
        return 0
    for a, v in r["accounts"].items():
        print(f"{a}: sentiment {v['valence_mean']:+.2f}; markers: {', '.join(v['behaviors']) or 'none'}")
        print("   style: " + ", ".join(f"{k}={x}" for k, x in v["style"].items()))
    print()
    for p in r["pairs"]:
        if not p["shared_behaviors"]:
            continue
        print(f"{p['a']} vs {p['b']}: shared markers {', '.join(p['shared_behaviors'])} (overlap {p['overlap']:.0%})")
        for bid, ph in p["identical_phrases"].items():
            print(f"    identical phrases for {bid}: " + "; ".join(f'"{x}"' for x in ph))
    if not any(p["shared_behaviors"] for p in r["pairs"]):
        print("No shared behavior markers between accounts.")
    print("\n" + r["caution"])
    return 0


def cmd_trend(args) -> int:
    r = analyze.trend(store.read_all(store.log_path(args.log)))
    if not r["rows"]:
        print("No incidents with logged messages yet.")
        return 0
    for row in r["rows"]:
        print(f"{row['seq']:>3}  {row['when']:<26} sentiment {row['valence']:+.2f}  attention {row['attention']:<8} {', '.join(row['behaviors'])}")
    print()
    print("\n".join("! " + f for f in r["flags"]) if r["flags"] else "No escalation flags.")
    print("\n" + r["caution"])
    return 0


def cmd_list(args) -> int:
    entries = store.read_all(store.log_path(args.log))
    if not entries:
        print("No incidents logged.")
        return 0
    for e in entries:
        print(f"{e['seq']:>3}  {e['occurred_at'] or e['logged_at']:<26} {','.join(e['attack_types']):<28} {e['summary'][:60]}")
    return 0


def cmd_verify(args) -> int:
    path = store.log_path(args.log)
    problems = store.verify(path)
    if problems:
        print("LOG INTEGRITY FAILED")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"Log intact: {len(store.read_all(path))} entries, hash chain verified.")
    return 0


def cmd_report(args) -> int:
    path = store.log_path(args.log)
    entries = store.read_all(path)
    if not entries:
        print("error: no incidents to report", file=sys.stderr)
        return 2
    ok = not store.verify(path)
    render = report.to_html if args.format == "html" else report.to_markdown
    text = render(entries, title=args.title, chain_ok=ok)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0 if ok else 1


def cmd_check_data(args) -> int:
    problems = data.validate() + analyze.validate()
    if problems:
        print("\n".join(problems))
        return 1
    print(f"Data tables consistent: {len(data.attacks())} attack types, {len(data.statutes())} statutes.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="va-incident-mapper", description="Log cyber incidents and map them to Virginia and federal statutes. Not legal advice.")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--log", help=f"incident log path (default: $VA_INCIDENT_LOG or ./{store.DEFAULT_LOG})")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("types", help="list attack types").set_defaults(fn=cmd_types)

    s = sub.add_parser("statutes", help="list statutes in the reference table")
    s.add_argument("--jurisdiction", choices=["va", "us", "VA", "US"])
    s.set_defaults(fn=cmd_statutes)

    s = sub.add_parser("suggest", help="suggest attack types from a description")
    s.add_argument("text", nargs="+")
    s.set_defaults(fn=cmd_suggest)

    s = sub.add_parser("map", help="show statutes for one or more attack types")
    s.add_argument("types", nargs="+")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_map)

    s = sub.add_parser("log", help="append an incident to the log")
    s.add_argument("--summary", required=True, help="what happened, in plain facts")
    s.add_argument("--type", required=True, action="append", help="attack type id (repeatable)")
    s.add_argument("--occurred", help="ISO 8601 date/time the incident happened")
    s.add_argument("--platform")
    s.add_argument("--account", action="append", help="account or handle involved (repeatable)")
    s.add_argument("--evidence", action="append", help="evidence file to hash (repeatable)")
    s.add_argument("--note")
    s.add_argument("--message", action="append", help="message text: '@account | text' or '@account | ISO-time | text' (repeatable)")
    s.add_argument("--messages-file", help="file with one message per line in the same format")
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("import", help="load a file downloaded from web/intake.html into the log")
    s.add_argument("file")
    s.add_argument("--evidence", action="append", help="evidence file to hash and attach (repeatable)")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("analyze", help="sentiment and behavior markers for pasted text")
    s.add_argument("text", nargs="*")
    s.add_argument("--file")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_analyze)

    s = sub.add_parser("compare", help="side-by-side markers for accounts in the log (observation only)")
    s.add_argument("--account", action="append")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_compare)

    sub.add_parser("trend", help="escalation view across logged incidents").set_defaults(fn=cmd_trend)

    sub.add_parser("list", help="list logged incidents").set_defaults(fn=cmd_list)
    sub.add_parser("verify", help="check the log hash chain").set_defaults(fn=cmd_verify)

    s = sub.add_parser("report", help="write a report from the log")
    s.add_argument("--format", choices=["md", "html"], default="md")
    s.add_argument("--out")
    s.add_argument("--title", default="Incident Report")
    s.set_defaults(fn=cmd_report)

    sub.add_parser("check-data", help="validate bundled tables").set_defaults(fn=cmd_check_data)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except KeyError as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
