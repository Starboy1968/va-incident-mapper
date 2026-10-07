# Command-line guide

## 1. Pick the attack type

```bash
va-incident-mapper types
va-incident-mapper suggest "someone keeps making new accounts after I block them"
```

`suggest` counts keyword hits per type. It only ranks; you decide. An incident can have several types, and you can pass `--type` more than once.

## 2. Read the mapping

```bash
va-incident-mapper map cyberstalking cyber-harassment
va-incident-mapper map phishing --json
```

Each statute carries a fit label:

| Label | Meaning |
|---|---|
| Primary fit | The statute's core conduct matches this attack type |
| Possible fit | Fits if extra facts exist (a threat, a loss, repetition) |
| Civil remedy | Lets a victim sue for damages |
| Contested | Legal theory is unsettled; ask counsel |

When two types cite the same statute, the strongest label wins.

## 3. Log what happened

```bash
va-incident-mapper log \
  --summary "Plain facts: who, what, when, where" \
  --type cyberstalking \
  --occurred 2026-03-02T22:40:00-05:00 \
  --platform ExamplePlatform \
  --account @handle_one --account @handle_two \
  --evidence ./screenshot-001.png --evidence ./chat-export.txt \
  --note "Blocked at 21:55; new account appeared 22:40"
```

Tips for good entries:

- Write facts and observations. Avoid conclusions about who someone is or what they intended.
- Use ISO 8601 times with your offset (`-05:00` for EST, `-04:00` for EDT).
- Hash files as soon as you save them. Keep the originals unchanged in a separate folder.
- Log one incident per event. Patterns emerge from the report, not from long entries.

## 4. Analyze the messages

```bash
va-incident-mapper analyze "paste the message here"
va-incident-mapper analyze --file message.txt --json
```

You get three things:

- **Sentiment** from -1 (very hostile) to +1 (very positive), plus counts of hostility, intimidation, contempt and distress words.
- **Behavior markers**, each with the exact words that matched and a short note on why it matters legally. Weights run 1 (low) to 5 (direct threat).
- **Suggested attack types** drawn from the markers, ready for `map`.

The attention level comes from the strongest marker: `urgent` (a direct threat), `high`, `elevated`, `routine`. If it says urgent and you are in danger, call 911 first.

Log the messages with the incident so patterns build up:

```bash
va-incident-mapper log --summary "..." --type cyberstalking \
  --message "@handle_one | 2026-03-02T21:50:00-05:00 | message text" \
  --message "@handle_two | message text"
va-incident-mapper log --summary "..." --type threats --messages-file messages.txt
```

Message format is `account | text` or `account | ISO-time | text`, one per line in a file. If the text itself contains ` | `, use the three-part form.

```bash
va-incident-mapper trend      # escalation: rising attention, worse sentiment, new markers
va-incident-mapper compare    # per-account markers + style stats, pairwise overlap
```

`compare` only describes. A shared phrase is worth noting, but it does not show two accounts are one person.

## 5. Verify and report

```bash
va-incident-mapper verify
va-incident-mapper report --format md --out report.md
va-incident-mapper report --format html --out report.html --title "Incident Report - March 2026"
```

`report` exits with code 1 and prints `FAILED` in the header if the chain is broken.

## The log format

One JSON object per line (`incidents.jsonl`). Fields: `seq`, `id`, `logged_at` (UTC), `occurred_at`, `platform`, `accounts`, `summary`, `attack_types`, `evidence` (`name`, `sha256`, `bytes`), `notes`, `prev_hash`, `hash`. The `hash` covers every other field plus `prev_hash`.

The log is append-only by design. To correct a mistake, log a new entry that references the earlier `seq` in its notes.

## Back up the log

Copy `incidents.jsonl` and your evidence folder somewhere safe after each session. If you ever need to show integrity, run `verify` on the backup.
