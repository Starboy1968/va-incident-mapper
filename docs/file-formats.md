# File formats

Every file the tools write is an open format. Nothing is encrypted or proprietary.

## Intake file: `va-incident-mapper-intake/1`

Written by `web/intake.html` (advanced .json download). Read by `va-incident-mapper import` and by the Incident Logger's Open case file.

| Key | Type | Notes |
|---|---|---|
| `schema` | string | Always `va-incident-mapper-intake/1` |
| `created_at` | string | ISO time |
| `summary` | string | Plain-language account |
| `attack_types` | string[] | Ids from `attacks.json`; at least one |
| `occurred_first`, `occurred_last` | string | ISO date or empty |
| `ongoing` | bool | |
| `platform`, `frequency`, `accounts` | string, string, string[] | |
| `know_in_person`, `told_to_stop`, `blocked_on` | string | |
| `messages` | object[] | `account`, `at`, `text`, `flags` (behavior ids) |
| `money_lost`, `impact` | string | |
| `feelings`, `feelings_text` | string[], string | What the person felt at the time |
| `evidence_have`, `actions_taken` | string[] | |
| `evidence_files` | object[] | `name`, `bytes`, `sha256` (or `note` if skipped). Files are never included |
| `agency`, `requests` | string, string[] | Who the report is for, what is requested |
| `case` | object | `agency`, `officer`, `local_case`, `ic3` |
| `reporter` | object | Empty `{}` unless the person ticks the contact box |

`import` never reads `reporter`.

## Case file: `va-incident-logger/1`

Written by Settings, then Save case file in the Incident Logger.

Keys: `incidents`, `stopDate`, `caseInfo`, `victimInfo`, `handles`, `auditLog`, `evidenceFiles`, `exportedAt`. `victimInfo` (name, phone, email) is left out unless the person ticks the box. Backups from the earlier Incident Logger open too.

## Log file: `incidents.jsonl`

One JSON object per line, append-only: `seq`, `id`, `logged_at` (UTC), `occurred_at`, `platform`, `accounts`, `summary`, `attack_types`, `evidence` (`name`, `sha256`, `bytes`), `notes`, `messages`, `prev_hash`, `hash`.

`hash` is the SHA-256 of the entry's other fields plus `prev_hash`. The first entry's `prev_hash` is 64 zeros. `verify` recomputes the chain and reports the first break.

## Reports

| Format | Where | Extension |
|---|---|---|
| Law Enforcement Update Report, IC3 Complaint Narrative, Full Incident Log | Intake, Logger | `.txt`, `.html` |
| Same three, tabular | Logger | `.xlsx`, `.pdf` |
| Mapping report | CLI `report` | `.md`, `.html` |

Fictional samples of each are in [`../examples`](../examples).
