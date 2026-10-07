"""Rebuild the sample log and reports from fictional data. Run from the repo root:
    python examples/make_sample.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from va_incident_mapper import report, store  # noqa: E402

HERE = Path(__file__).resolve().parent
log = HERE / "sample-incidents.jsonl"
log.unlink(missing_ok=True)


def t(day, hour):
    return datetime(2026, 3, day, hour, 0, tzinfo=timezone.utc)


store.append(
    log,
    summary="Employee at Example Corp received an email styled as a payroll portal notice. Link led to a lookalike login page at payroll-example.invalid. Employee entered credentials before noticing the mismatch.",
    attack_types=["phishing", "unauthorized-access"],
    occurred_at="2026-03-01T09:15:00-05:00", platform="Email", accounts=["payroll-alerts@example.invalid"],
    notes="Password reset within 20 minutes. Provider login history shows one sign-in from an unfamiliar IP before the reset.",
    now=t(1, 15),
)
store.append(
    log,
    summary="@example_user_a received repeated vulgar messages from @example_main, then from a new account @example_alt_1 after blocking. Messages continued on a second platform.",
    attack_types=["cyber-harassment", "cyberstalking", "alt-account-evasion"],
    occurred_at="2026-03-02T22:40:00-05:00", platform="ExamplePlatform", accounts=["@example_main", "@example_alt_1"],
    notes="Block times and account creation dates are in the attached timeline.",
    messages=[
        {"account": "@example_main", "at": "2026-03-02T21:50:00-05:00", "text": "Answer me. You think you're so smart, little boy? Rules don't apply to me."},
        {"account": "@example_alt_1", "at": "2026-03-02T22:40:00-05:00", "text": "You blocked me but it won't stop. Rules don't apply to me. I made a new account, honey."},
    ],
    now=t(2, 16),
)
store.append(
    log,
    summary="Ransom note appeared on a small office file server demanding payment in cryptocurrency to restore encrypted files. Backups from the prior night are intact.",
    attack_types=["ransomware-extortion"],
    occurred_at="2026-03-03T06:05:00-05:00", platform="Office file server",
    notes="Server disconnected from the network and disk image taken before any cleanup.",
    messages=[{"account": "unknown", "at": "2026-03-03T06:05:00-05:00", "text": "Your files are encrypted. Pay 0.5 bitcoin within 48 hours or we will leak your customer data. Do not call the police."}],
    now=t(3, 17),
)
store.append(
    log,
    summary="Follow-up messages to @example_user_a from a third new account after another block, now referencing the user's workplace and schedule.",
    attack_types=["cyberstalking", "cyber-harassment", "threats"],
    occurred_at="2026-03-05T20:10:00-05:00", platform="ExamplePlatform", accounts=["@example_alt_2"],
    messages=[{"account": "@example_alt_2", "at": "2026-03-05T20:10:00-05:00", "text": "I've been tracking you for weeks. I know where you work. You can't hide and it won't stop, watch your back."}],
    now=t(5, 22),
)
assert not store.verify(log)
entries = store.read_all(log)
title = "Sample Incident Report (fictional data)"
(HERE / "sample-report.md").write_text(report.to_markdown(entries, title=title), encoding="utf-8")
(HERE / "sample-report.html").write_text(report.to_html(entries, title=title), encoding="utf-8")
print("wrote", log.name, "sample-report.md", "sample-report.html")
