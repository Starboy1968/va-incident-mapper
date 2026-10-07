# Privacy and interoperability

This tool is built on one rule: **personal information is never stored by the tool. It is only exported, locally, by the person who typed it.**

## What the intake form does

- It has no server. It makes no network requests. The page carries a Content-Security-Policy that tells the browser to block every connection from it (`default-src 'none'`, `connect-src 'none'`), so this holds even if the code were changed by mistake. A test checks the policy is present.
- It uses no browser storage (no localStorage, sessionStorage, IndexedDB or cookies). Closing or reloading the tab erases everything. A test enforces this.
- Evidence files are fingerprinted (SHA-256) in the browser. They are not uploaded or copied.
- Nothing leaves the device unless the person downloads a file, copies text, prints, or presses "Email it" (which hands a short text to their own mail app).

## The Incident Logger

Same rules as the intake form: no server, a Content-Security-Policy that blocks all network connections, no browser storage, and a warning before the page closes with unsaved work. The earlier logger saved to the browser automatically; this one deliberately does not. The case file (.json) leaves out your name, phone and email unless you tick the box. The spreadsheet and PDF libraries are bundled in the file, so exporting needs no internet.

## What gets exported

| File | Contains contact details? | Use |
|------|---------------------------|-----|
| Report (.html, .txt) in three formats | Yes, because it is the filing the person hands to an agency | Print, attach, paste into a form |
| Log file (.json) | **No, unless the person ticks the box** | Move the case into other tools or the incident log |

All exports are open, plain formats (text, HTML, JSON). Nothing needs this tool to read it.

## The .json schema (`va-incident-mapper-intake/1`)

`schema`, `created_at`, `summary`, `attack_types` (ids from `attacks.json`), `occurred_first`, `occurred_last`, `ongoing`, `platform`, `frequency`, `accounts`, `know_in_person`, `told_to_stop`, `blocked_on`, `messages` (`account`, `at`, `text`), `money_lost`, `impact`, `feelings` (list), `feelings_text`, `evidence_have`, `actions_taken`, `evidence_files` (`name`, `bytes`, `sha256`), `agency`, `requests`, `case` (`agency`, `officer`, `local_case`, `ic3`), `reporter` (empty unless opted in).

Any tool can read this file. `va-incident-mapper import` loads it into the incident log and **never reads `reporter`**.

## The command-line incident log

The log stores what is needed as evidence: your summary, the subject's accounts, the messages received, and evidence fingerprints. It never stores the reporter's name, phone, email or address. It is a local file you control. `.gitignore` excludes the log, intake files, evidence and generated reports, so none of it is committed by accident.

## Keeping the repository clean

The samples in `examples/` are fictional (addresses end in `.invalid`). A test fails if a real-looking email address or SSN appears in the samples or README.
