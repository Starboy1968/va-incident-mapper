# va-incident-mapper

Document a cyber incident, see which Virginia and federal laws may apply, and produce reports you can hand to police, the FBI's IC3, or an attorney. Built for victims, advocates, small-business owners and IT staff.

> **Not legal advice.** This tool organizes facts and points to statutes worth reviewing. It cannot decide whether a crime occurred. Confirm with a licensed Virginia attorney or law enforcement. In an emergency, call 911.

![Incident Logger](docs/images/logger-log.png)

## Three tools, one data set

| Tool | Best for | Needs |
|---|---|---|
| [**Incident Logger**](docs/logger.md) (`web/logger.html`) | Logging incidents over time, spotting patterns, exporting reports as .txt, .xlsx and .pdf | A browser |
| [**Guided intake form**](docs/intake.md) (`web/intake.html`) | Someone who wants plain-language questions, then a report to send | A browser |
| [**Command line**](docs/cli.md) (`va-incident-mapper`) | A tamper-evident log, message analysis, scripting | Python 3.9+ |

Both web pages are single files. Download one, double-click it, and it works offline.

## What it does

- Maps 14 attack types to Virginia Code sections and related federal law, labeled primary fit, possible fit, civil remedy or contested.
- Flags threat and harassment behaviors in messages (14 in the guided form and CLI, 26 legal flags in the logger) and scores sentiment.
- Records how the victim felt at the time, since stalking and harassment laws often turn on fear or distress.
- Fingerprints evidence files with SHA-256 so you can later show they have not changed.
- Writes three report formats: Law Enforcement Update Report, IC3 Complaint Narrative, and Full Incident Log. Each ends with a plain-language key and support hotlines.
- Chains CLI log entries with SHA-256 so edits to old entries are detectable.

## Quick start

**Web tools.** Clone or download the repo, then open `web/logger.html` or `web/intake.html` in a browser.

**Command line.**

```bash
git clone https://github.com/Starboy1968/va-incident-mapper.git
cd va-incident-mapper
python -m pip install .

va-incident-mapper suggest "fake login page asked for my password"
va-incident-mapper log --summary "Lookalike payroll page" --type phishing --evidence ./email.eml
va-incident-mapper verify
va-incident-mapper report --format html --out report.html
```

No dependencies. Samples built from fictional data are in [`examples/`](examples).

## Privacy: the key tenet

Personal information is never stored by this tool. It is only exported, locally, by the person who typed it.

- No server, no accounts, no network requests (the browser is told to block them).
- No browser storage. Closing the tab erases the session. Use **Save case file** to keep work.
- Exports are open formats: .txt, .html, .json, .xlsx, .pdf.
- Contact details stay out of .json and case files unless the person opts in.

Details: [docs/privacy.md](docs/privacy.md).

## Documentation

| Doc | Contents |
|---|---|
| [Usage overview](docs/usage.md) | Which tool to use |
| [Incident Logger](docs/logger.md) | Tabs, saving, exports |
| [Guided intake form](docs/intake.md) | Steps, sending the report |
| [Command line](docs/cli.md) | Every command with examples |
| [File formats](docs/file-formats.md) | Intake, case file, log layouts |
| [Architecture](docs/architecture.md) | Layout, builds, enforcement |
| [Data and limits](docs/data-and-limits.md) | Sources, updating statutes, known gaps |
| [Privacy](docs/privacy.md) | What is and is not stored |

## Honest limits

- Virginia citations were checked against the Code of Virginia on 2026-10-05. Federal citations are marked `*` because they were not re-checked. Laws change.
- The Incident Logger's legal labels were corrected against the statute text on 2026-10-07 (for example § 18.2-60 is threats, not stalking, and doxxing is § 18.2-186.4). They have not had attorney review. See [data-and-limits.md](docs/data-and-limits.md).
- Language analysis uses word lists, English only. It misses sarcasm and can match harmless text.
- Account comparison is observation, not attribution.
- Some mappings are contested, for example platform bans under the CFAA after *Van Buren v. United States* (2021).
- The hash chain proves a log was not edited, not that events happened.

## Contributing

Corrections to statute text are the most valuable contribution. See [CONTRIBUTING.md](CONTRIBUTING.md). Report vulnerabilities per [SECURITY.md](SECURITY.md). Do not post real case data in issues.

## License

MIT. See [LICENSE](LICENSE). Bundled libraries keep their own licenses in `web/vendor/`.
