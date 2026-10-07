# Contributing

## Most useful

1. Corrections to statute text, citations or fit labels, with a link to the official source (law.lis.virginia.gov for Virginia, uscode.house.gov for federal).
2. Wording that is clearer for non-lawyers.
3. Bug reports with fictional reproduction data.

## Setup

```bash
python -m pip install -e .
python -m unittest discover -s tests
```

## Rules

- **No real case data**, names, handles, messages, or evidence anywhere: code, tests, issues, screenshots. Use fictional data and `.invalid` or `example.com` addresses.
- **Keep the privacy tenet.** No server calls, no browser storage, no analytics, no remote scripts. Tests enforce this.
- **Python stays standard-library only.** Web pages stay single files.
- Edit sources, not generated pages. Change `web/*.template.html` or `web/logger.core.js`, then run `python tools/build_intake.py` and `python tools/build_logger.py`.
- Data tables live in `src/va_incident_mapper/data/`. Run `va-incident-mapper check-data` after editing. Add a verification date for any statute you check.
- Add a test for new behavior.

## Pull requests

Describe what changed and why, and link the source for any legal change. Say what you did not verify.
