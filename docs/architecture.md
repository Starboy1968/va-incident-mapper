# Architecture

```
src/va_incident_mapper/   Python package, standard library only
  data/*.json             statutes, attacks, behaviors, lexicon (single source of truth)
  data.py                 loads and validates the tables
  mapper.py               attack type -> statutes, caveats, evidence checklist
  analyze.py              sentiment, behavior markers, trend, account comparison
  store.py                hash-chained JSONL log, evidence hashing
  report.py               markdown and HTML reports
  intake.py               reads intake files into the log
  cli.py                  argparse commands
web/
  intake.template.html    guided form source
  logger.template.html    Incident Logger source
  logger.core.js          Incident Logger logic
  vendor/                 SheetJS (Apache-2.0), jsPDF (MIT)
  intake.html, logger.html  generated single-file pages, committed
tools/                    build_intake.py, build_logger.py
tests/test_all.py         unit and sync tests
examples/                 fictional samples and make_sample.py
```

## One source of data

The JSON tables in `data/` feed the CLI directly. `tools/build_intake.py` embeds them into `intake.html`, so the form and the CLI cannot disagree. A test rebuilds the page and fails if the committed file differs. The Incident Logger carries its own legal-flag labels from the original tool; see [data-and-limits.md](data-and-limits.md).

## Why single-file pages

Each page is one HTML file with inlined script and style. A person can save it, open it offline, email it, or read the whole source. There is nothing to install and no server to trust.

## Privacy enforcement

- A Content-Security-Policy meta tag blocks all network requests (`default-src 'none'`, `connect-src 'none'`, `form-action 'none'`).
- Tests fail if either page contains `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, `fetch(`, `XMLHttpRequest`.
- Export is always a user-triggered download.

## Tamper evidence

Each log entry stores the hash of the previous entry. Changing, removing or reordering any entry changes every later hash, which `verify` detects. This shows the file was edited after writing; it does not prove the events happened.

## Build and test

```bash
python tools/build_intake.py
python tools/build_logger.py
python -m unittest discover -s tests
```
