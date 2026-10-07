# Data, sources and limits

## Where the data lives

- `src/va_incident_mapper/data/statutes.json`: one record per statute (cite, title, summary, penalty, `verified` flag).
- `src/va_incident_mapper/data/attacks.json`: one record per attack type (keywords, statute links with fit labels, evidence checklist, where to report, caveats).

- `src/va_incident_mapper/data/behaviors.json`: behavior markers. Each has regular-expression `patterns`, a `weight` (1-5), the `attack_types` it points to, and a `legal_note`.
- `src/va_incident_mapper/data/lexicon.json`: sentiment word scores, intensifiers, negators, and emotion-category word lists (stems end in `*`).

- `web/intake.template.html`: the intake form source. `tools/build_intake.py` embeds the four data tables into it to produce `web/intake.html`.

## Sources

Virginia entries were read from the Code of Virginia at <https://law.lis.virginia.gov/vacode/> on 2026-10-05 and carry `"verified": true`. Federal entries use standard U.S. Code references and carry `"verified": false` until someone re-checks them at <https://uscode.house.gov>.

Summaries are paraphrases, kept short on purpose. Always read the statute itself.

## Updating a statute

1. Open the section on law.lis.virginia.gov and read the current text.
2. Edit its record in `statutes.json`. Update `va_verified_on` in `_meta` if you re-checked the whole set.
3. Run `va-incident-mapper check-data` and `python -m unittest discover -s tests`.
4. In your pull request, link the official page you read.

## Adding an attack type

Add a record to `attacks.json` with every field the validator requires (`name`, `description`, `keywords`, `statutes`, `document`, `report_to`, `caveats`). Every statute id must exist in `statutes.json`, and `check-data` fails otherwise. The test suite also fails if a statute is not used by any attack type.

## Extending the language analysis

Add a behavior by appending a record to `behaviors.json`. Keep patterns specific: a pattern that fires on everyday sentences ("be careful", "or I will go home") buries real signals. After editing, run `va-incident-mapper check-data` and the tests; there are tests that check benign sentences stay at the `routine` level. Add the benign sentence you worried about as a new test.

Sentiment uses a small hand-built word list, so it understates hostility that uses words the list lacks. Add words to `lexicon.json` rather than raising weights.

## Known gaps

- Virginia law on wiretapping (Va. Code § 19.2-62 and following), revenge-porn-adjacent civil remedies, and protective-order procedure are not mapped yet.
- Other states and local ordinances are out of scope.
- The intake form's language scan is a JavaScript port of `analyze.py`. A test would catch drift only for the cases it covers, so after editing patterns in `behaviors.json`, rebuild the form and spot-check a few messages in both.
- Language analysis is English-only and keyword-based. It cannot judge sarcasm, quotes, jokes between friends, or reclaimed language. Writing-style statistics are descriptive and weak as identification evidence.
- Federal penalties are summarized loosely. Check the statute.
- The tool does not assess evidence strength, jurisdiction, venue, limitations periods (other than the Computer Crimes Act civil deadline), or defenses.

## Support numbers shown in the intake form

National Domestic Violence Hotline 1-800-799-7233 (text START to 88788), Virginia Family Violence & Sexual Assault Hotline 1-800-838-8238, and the CCRI helpline 844-878-2274 were confirmed on each organization's or the Virginia Department of Health's site on 2026-10-05. Re-check them when you update the data.

## Not legal advice

Nothing here creates an attorney-client relationship or predicts how a prosecutor, court or platform will act.


## The Incident Logger's statute labels

`web/logger.html` keeps the original Incident Logger's flag groups and report layout. Its legal labels were checked on 2026-10-07 against law.lis.virginia.gov and law.cornell.edu and corrected. They are still separate from `statutes.json`, so a statute change must be made in both places (`web/logger.core.js` for the logger).

What changed from the original:

| Original | Corrected |
|---|---|
| Va. Code § 18.2-60 called a stalking law | § 18.2-60 covers threats of death or bodily injury, including electronic ones. Stalking is § 18.2-60.3 |
| Doxxing cited § 18.2-152.7:1 | Publishing someone's identifying information to coerce, intimidate or harass is § 18.2-186.4. § 18.2-152.7:1 covers computer harassment and does not mention doxxing |
| Threats to property or jobs cited § 875(c) and § 18.2-60 | Both cover threats to injure a person only. Property threats appear in 18 U.S.C. § 875(d), and only with intent to extort |
| 18 U.S.C. § 249 labeled "hate crime" for harassment | § 249 requires bodily injury. Bias language is now labeled motive evidence only |
| 18 U.S.C. § 1028 for impersonation | § 1028(a)(7) needs another person's real identifying information used in connection with a crime. A fake profile alone usually does not meet it |
| 42 U.S.C. § 1985(3) as conspiracy law | It is a civil damages remedy, and courts require class-based bias |
| 47 U.S.C. § 223 for harassing messages | Cites § 223(a)(1), covering telecommunications-device use with intent to abuse, threaten or harass |
| CFAA for post-ban or post-block accounts | Marked contested after Van Buren v. United States (2021) |
| Report text said each incident "constitutes a knowing willful violation" of § 2261A | Now says each is evidence of continued contact after notice, and that a violation is for law enforcement and the court to decide |

Still open for attorney review:

- The statute summaries come from the statute text and a quick reading, not from case law. The class-based animus point for § 1985(3) and the Counterman recklessness standard for threats come from court decisions, not the statute text.
- 18 U.S.C. § 2703(f) (preservation requests) and the Counterman standard were not re-checked. § 2261A, § 875, § 249, § 1028, § 223 and § 1985 were read against current statute text.
- Wording should be reviewed by a Virginia attorney or victim-services group before public use.

## Bundled libraries

`web/vendor/` holds SheetJS 0.18.5 (Apache-2.0) and jsPDF 2.5.1 (MIT), copied unchanged and inlined into `logger.html` by `python tools/build_logger.py`. Rebuild after any change to `logger.template.html` or `logger.core.js`.
