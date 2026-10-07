import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from va_incident_mapper import cli, data, intake, mapper, report, store  # noqa: E402

FIXED = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


class DataTests(unittest.TestCase):
    def test_tables_consistent(self):
        self.assertEqual(data.validate(), [])

    def test_every_va_statute_is_verified(self):
        for s in data.statutes().values():
            if s["jurisdiction"] == "VA":
                self.assertTrue(s["verified"], s["id"])

    def test_every_statute_used(self):
        used = {r["id"] for a in data.attacks().values() for r in a["statutes"]}
        self.assertEqual(set(data.statutes()) - used, set())


class MapperTests(unittest.TestCase):
    def test_suggest_phishing(self):
        ranked = mapper.suggest("Got a phishing email with a fake login page")
        self.assertEqual(ranked[0][0], "phishing")

    def test_suggest_nothing(self):
        self.assertEqual(mapper.suggest("lovely weather today"), [])

    def test_map_primary_first_and_deduped(self):
        m = mapper.map_types(["cyber-harassment", "cyberstalking"])
        cites = [s["id"] for s in m["statutes"]]
        self.assertEqual(len(cites), len(set(cites)))
        # 18.2-60.3 is 'possible' for harassment but 'primary' for stalking: strongest wins
        row = next(s for s in m["statutes"] if s["id"] == "va-18.2-60.3")
        self.assertEqual(row["strength"], "primary")
        self.assertEqual(m["statutes"][0]["strength"], "primary")

    def test_va_before_federal_within_tier(self):
        m = mapper.map_types(["unauthorized-access"])
        primaries = [s for s in m["statutes"] if s["strength"] == "primary"]
        self.assertEqual(primaries[0]["jurisdiction"], "VA")

    def test_unknown_type(self):
        with self.assertRaises(KeyError):
            mapper.map_types(["nope"])

    def test_ban_evasion_cfaa_flagged_contested(self):
        m = mapper.map_types(["alt-account-evasion"])
        row = next(s for s in m["statutes"] if s["id"] == "us-18-1030")
        self.assertEqual(row["strength"], "contested")
        self.assertTrue(any("Van Buren" in c for c in m["caveats"]))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "log.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, **kw):
        base = dict(summary="Test event", attack_types=["phishing"], now=FIXED)
        base.update(kw)
        return store.append(self.log, **base)

    def test_chain_valid_then_tamper(self):
        self.add()
        self.add(summary="Second")
        self.assertEqual(store.verify(self.log), [])
        lines = self.log.read_text().splitlines()
        edited = json.loads(lines[0])
        edited["summary"] = "Changed after the fact"
        lines[0] = json.dumps(edited, sort_keys=True)
        self.log.write_text("\n".join(lines) + "\n")
        self.assertTrue(store.verify(self.log))

    def test_deleted_line_detected(self):
        self.add()
        self.add(summary="Second")
        self.add(summary="Third")
        lines = self.log.read_text().splitlines()
        del lines[1]
        self.log.write_text("\n".join(lines) + "\n")
        self.assertTrue(store.verify(self.log))

    def test_evidence_hash(self):
        f = Path(self.tmp.name) / "e.txt"
        f.write_text("hello")
        e = self.add(evidence_files=[str(f)])
        self.assertEqual(e["evidence"][0]["sha256"], "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.add(summary="  ")
        with self.assertRaises(ValueError):
            self.add(attack_types=[])
        with self.assertRaises(ValueError):
            self.add(attack_types=["bogus"])
        with self.assertRaises(ValueError):
            self.add(occurred_at="yesterday")
        with self.assertRaises(ValueError):
            self.add(evidence_files=["/no/such/file"])
        self.assertFalse(self.log.exists())

    def test_empty_log_verifies(self):
        self.assertEqual(store.verify(self.log), [])


class ReportTests(unittest.TestCase):
    def entries(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "l.jsonl"
            store.append(log, summary="<script>alert(1)</script> phishing", attack_types=["phishing"], now=FIXED)
            return store.read_all(log)

    def test_markdown_has_disclaimer_and_statute(self):
        md = report.to_markdown(self.entries())
        self.assertIn("not legal advice", md)
        self.assertIn("Va. Code § 18.2-152.5:1", md)

    def test_html_escapes_user_text(self):
        out = report.to_html(self.entries())
        self.assertNotIn("<script>alert(1)</script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_failed_chain_is_called_out(self):
        self.assertIn("FAILED", report.to_markdown(self.entries(), chain_ok=False))


class CliTests(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            log = str(Path(d) / "l.jsonl")
            out = str(Path(d) / "r.html")
            self.assertEqual(cli.main(["--log", log, "log", "--summary", "Fake bank login email", "--type", "phishing"]), 0)
            self.assertEqual(cli.main(["--log", log, "verify"]), 0)
            self.assertEqual(cli.main(["--log", log, "report", "--format", "html", "--out", out]), 0)
            self.assertIn("<h1>Incident Report</h1>", Path(out).read_text())
            self.assertEqual(cli.main(["--log", log, "log", "--summary", "x", "--type", "bogus"]), 2)

    def test_check_data(self):
        self.assertEqual(cli.main(["check-data"]), 0)


if __name__ == "__main__":
    unittest.main()


class LanguageTests(unittest.TestCase):
    def test_validate(self):
        from va_incident_mapper import analyze
        self.assertEqual(analyze.validate(), [])

    def test_sentiment_direction(self):
        from va_incident_mapper import analyze
        self.assertGreater(analyze.sentiment("Thanks, I really appreciate the help")["valence"], 0.3)
        self.assertLess(analyze.sentiment("I hate you, you worthless idiot")["valence"], -0.5)
        self.assertEqual(analyze.sentiment("The meeting is at noon")["valence"], 0.0)

    def test_negation_flips(self):
        from va_incident_mapper import analyze
        self.assertGreater(analyze.sentiment("this is not terrible")["valence"], analyze.sentiment("this is terrible")["valence"])

    def test_direct_threat_is_urgent(self):
        from va_incident_mapper import analyze
        r = analyze.analyze("I will kill you")
        self.assertEqual(r["attention"], "urgent")
        self.assertIn("threats", r["suggested_attack_types"])
        self.assertIn("911", r["attention_note"])

    def test_benign_text_is_routine(self):
        from va_incident_mapper import analyze
        for text in ["I'm not going to kill the process, or I will go home", "Please be careful on the ice", "Pay the invoice by Friday"]:
            self.assertEqual(analyze.analyze(text)["attention"], "routine", text)

    def test_conditional_and_surveillance(self):
        from va_incident_mapper import analyze
        ids = {b["id"] for b in analyze.behaviors("If you tell anyone I will post your address. I've been tracking you.")}
        self.assertTrue({"conditional-threat", "doxxing-threat", "surveillance-claim"} <= ids)

    def test_curly_apostrophes(self):
        from va_incident_mapper import analyze
        ids = {b["id"] for b in analyze.behaviors("It won’t stop. I’ve been tracking you.")}
        self.assertIn("permanence-declaration", ids)
        self.assertIn("surveillance-claim", ids)

    def test_every_behavior_maps_to_attack_types_and_statutes(self):
        from va_incident_mapper import analyze
        for b in analyze.behavior_table():
            self.assertTrue(mapper.map_types(b["attack_types"])["statutes"], b["id"])

    def test_compare_pairwise_and_cautions(self):
        from va_incident_mapper import analyze
        r = analyze.compare({
            "a": ["Rules don't apply to me."],
            "b": ["Rules don't apply to me. it won't stop"],
            "c": ["Have a nice day"],
        })
        pair = next(p for p in r["pairs"] if {p["a"], p["b"]} == {"a", "b"})
        self.assertEqual(pair["shared_behaviors"], ["entitlement-defiance"])
        self.assertIn("rules don't apply to me", pair["identical_phrases"]["entitlement-defiance"])
        self.assertIn("not proof", r["caution"])

    def test_trend_flags_escalation(self):
        from va_incident_mapper import analyze
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "l.jsonl"
            store.append(log, summary="a", attack_types=["cyber-harassment"], messages=[{"account": "x", "text": "answer me"}], now=FIXED)
            store.append(log, summary="b", attack_types=["threats"], messages=[{"account": "x", "text": "I will kill you"}], now=FIXED)
            r = analyze.trend(store.read_all(log))
        self.assertTrue(any("rose" in f for f in r["flags"]))


class LanguageStoreCliTests(unittest.TestCase):
    def test_store_keeps_messages_and_analysis_and_chain(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "l.jsonl"
            e = store.append(log, summary="s", attack_types=["threats"], messages=[{"account": "@a", "text": "watch your back"}], now=FIXED)
            self.assertEqual(e["messages"][0]["account"], "@a")
            self.assertEqual(e["analysis"]["attention"], "elevated")
            self.assertEqual(store.verify(log), [])
            with self.assertRaises(ValueError):
                store.append(log, summary="s", attack_types=["threats"], messages=[{"account": "@a", "text": " "}], now=FIXED)

    def test_old_entries_without_messages_still_report(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "l.jsonl"
            store.append(log, summary="s", attack_types=["phishing"], now=FIXED)
            md = report.to_markdown(store.read_all(log))
            self.assertNotIn("Language analysis", md)

    def test_report_includes_language_trend_and_comparison(self):
        sample = Path(__file__).resolve().parent.parent / "examples" / "sample-incidents.jsonl"
        entries = store.read_all(sample)
        md = report.to_markdown(entries)
        self.assertIn("Language analysis", md)
        self.assertIn("Escalation over time", md)
        self.assertIn("Account comparison", md)
        self.assertEqual(store.verify(sample), [])
        self.assertIn("&lt;", report.to_html([dict(entries[1], summary="<b>x</b>")]))

    def test_cli_log_message_analyze_compare_trend(self):
        import contextlib, io
        with tempfile.TemporaryDirectory() as d:
            log = str(Path(d) / "l.jsonl")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(cli.main(["--log", log, "log", "--summary", "s1", "--type", "cyberstalking",
                                           "--message", "@a | Answer me. Rules don't apply to me."]), 0)
                self.assertEqual(cli.main(["--log", log, "log", "--summary", "s2", "--type", "threats",
                                           "--message", "@b | 2026-03-05T20:10:00-05:00 | Rules don't apply to me. I will kill you"]), 0)
                self.assertEqual(cli.main(["--log", log, "compare"]), 0)
                self.assertEqual(cli.main(["--log", log, "trend"]), 0)
                self.assertEqual(cli.main(["analyze", "watch", "your", "back"]), 0)
            out = buf.getvalue()
            self.assertIn("urgent", out)
            self.assertIn("identical phrases", out)
            self.assertIn("Attention level rose", out)
            self.assertEqual(cli.main(["--log", log, "compare", "--account", "@a"]), 2)

    def test_parse_message(self):
        self.assertEqual(cli.parse_message("@a | hi"), {"account": "@a", "at": "", "text": "hi"})
        self.assertEqual(cli.parse_message("just text")["account"], "unknown")
        self.assertEqual(cli.parse_message("@a | 2026-01-01T00:00:00 | text")["at"], "2026-01-01T00:00:00")


class IntakeTests(unittest.TestCase):
    def payload(self, **over):
        p = {
            "schema": "va-incident-mapper-intake/1", "summary": "New accounts after block",
            "attack_types": ["cyberstalking", "alt-account-evasion"],
            "occurred_first": "2026-02-16", "occurred_last": "2026-03-05", "ongoing": True,
            "platform": "ExamplePlatform", "frequency": "Many times", "accounts": ["@a", "@b"],
            "know_in_person": "I have a guess", "told_to_stop": "yes", "blocked_on": "2026-02-20",
            "messages": [{"account": "@b", "at": "", "text": "You blocked me but it won't stop."}, {"account": "@b", "at": "", "text": "  "}],
            "money_lost": "0", "impact": "Afraid to go out alone", "evidence_have": ["Screenshots"], "actions_taken": ["Blocked the person"],
        }
        p.update(over)
        return p

    def write(self, d, payload):
        f = Path(d) / "intake.json"
        f.write_text(json.dumps(payload), encoding="utf-8")
        return str(f)

    def test_round_trip_into_log(self):
        from va_incident_mapper import intake
        with tempfile.TemporaryDirectory() as d:
            kwargs = intake.to_append_kwargs(intake.load(self.write(d, self.payload())))
            log = Path(d) / "l.jsonl"
            e = store.append(log, now=FIXED, **kwargs)
            self.assertEqual(e["occurred_at"], "2026-02-16")
            self.assertEqual(len(e["messages"]), 1)
            self.assertIn("Still ongoing", e["notes"])
            self.assertIn("2026-02-20", e["notes"])
            self.assertEqual(e["analysis"]["attention"], "elevated")
            self.assertEqual(store.verify(log), [])

    def test_rejects_bad_files(self):
        from va_incident_mapper import intake
        with tempfile.TemporaryDirectory() as d:
            for bad in (self.payload(schema="other"), self.payload(attack_types=[]), self.payload(attack_types=["nope"])):
                with self.assertRaises(ValueError):
                    intake.load(self.write(d, bad))
            (Path(d) / "x.json").write_text("{not json")
            with self.assertRaises(ValueError):
                intake.load(str(Path(d) / "x.json"))
            with self.assertRaises(ValueError):
                intake.load(str(Path(d) / "missing.json"))

    def test_bad_date_is_dropped_not_fatal(self):
        from va_incident_mapper import intake
        with tempfile.TemporaryDirectory() as d:
            kwargs = intake.to_append_kwargs(intake.load(self.write(d, self.payload(occurred_first="yesterday"))))
            self.assertIsNone(kwargs["occurred_at"])

    def test_cli_import(self):
        import contextlib, io
        with tempfile.TemporaryDirectory() as d:
            log = str(Path(d) / "l.jsonl")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(cli.main(["--log", log, "import", self.write(d, self.payload())]), 0)
                self.assertEqual(cli.main(["--log", log, "verify"]), 0)
            self.assertIn("Imported intake as incident 1", buf.getvalue())
            self.assertEqual(cli.main(["--log", log, "import", str(Path(d) / "nope.json")]), 2)


class IntakePageTests(unittest.TestCase):
    def test_intake_html_is_in_sync_with_data(self):
        root = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(root / "tools"))
        import build_intake
        built = (root / "web" / "intake.html").read_text(encoding="utf-8")
        self.assertEqual(built, build_intake.render(), "run: python tools/build_intake.py")

    def test_intake_has_safety_banner_and_no_storage(self):
        html = (Path(__file__).resolve().parent.parent / "web" / "intake.html").read_text(encoding="utf-8")
        self.assertIn("Call 911", html)
        for banned in ("localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "document.cookie"):
            self.assertNotIn(banned, html)
        self.assertIn("Content-Security-Policy", html)
        self.assertIn("connect-src 'none'", html)
        self.assertIn("default-src 'none'", html)


class IntakeOutputTests(unittest.TestCase):
    def test_download_buttons_and_three_formats(self):
        html = (Path(__file__).resolve().parent.parent / "web" / "intake.html").read_text(encoding="utf-8")
        for needle in ("Download report (.html)", "Download report (.txt)", "Send it to law enforcement",
                       "crypto.subtle", "LAW ENFORCEMENT UPDATE REPORT", "IC3 COMPLAINT NARRATIVE",
                       "KEY - PLAIN LANGUAGE (FOR NON-LAWYERS)", "Full incident log"):
            self.assertIn(needle, html)

    def test_sample_outputs_exist_and_agree(self):
        ex = Path(__file__).resolve().parent.parent / "examples"
        for mode, head in (("law-enforcement-report", "LAW ENFORCEMENT UPDATE REPORT"),
                           ("ic3-narrative", "IC3 COMPLAINT NARRATIVE"),
                           ("full-incident-log", "INCIDENT REPORT - INC-001")):
            txt = (ex / f"sample-{mode}.txt").read_text(encoding="utf-8")
            page = (ex / f"sample-{mode}.html").read_text(encoding="utf-8")
            for needle in (head, "Va. Code § 18.2-60.3", "KEY - PLAIN LANGUAGE", "911", "organizing tool", "SHA-256"):
                self.assertIn(needle, txt)
            self.assertIn(head, page)
            self.assertNotIn("<script", page)
        for mode in ("law-enforcement-report", "ic3-narrative", "full-incident-log"):
            self.assertIn("How I felt at the time", (ex / f"sample-{mode}.txt").read_text(encoding="utf-8"))
        le = (ex / "sample-law-enforcement-report.txt").read_text(encoding="utf-8")
        self.assertIn("Signature:", le)
        self.assertIn("REQUESTED ACTIONS", le)


class IntakeReporterPrivacyTests(unittest.TestCase):
    def test_feelings_import_into_notes(self):
        ex = Path(__file__).resolve().parent.parent / "examples" / "sample-intake.json"
        kw = intake.to_append_kwargs(intake.load(ex))
        self.assertIn("Felt at the time", kw["notes"])
        self.assertIn("In their words", kw["notes"])

    def test_json_file_leaves_out_contact_by_default(self):
        ex = Path(__file__).resolve().parent.parent / "examples" / "sample-intake.json"
        self.assertEqual(json.loads(ex.read_text(encoding="utf-8"))["reporter"], {})
        html = (Path(__file__).resolve().parent.parent / "web" / "intake.html").read_text(encoding="utf-8")
        self.assertIn("payload($(\"incc\").checked)", html)

    def test_no_pii_style_data_in_repo_samples(self):
        import re
        root = Path(__file__).resolve().parent.parent
        for f in list((root / "examples").glob("*")) + [root / "README.md"]:
            if f.suffix not in (".txt", ".md", ".json", ".html", ".jsonl"):
                continue
            text = f.read_text(encoding="utf-8")
            for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
                self.assertTrue(m.endswith(".invalid") or m.endswith("example.com"), f"{f.name}: {m}")
            self.assertIsNone(re.search(r"\b\d{3}-\d{2}-\d{4}\b", text), f.name)

    def test_import_ignores_reporter_contact_but_keeps_fingerprints(self):
        ex = Path(__file__).resolve().parent.parent / "examples" / "sample-intake.json"
        kw = intake.to_append_kwargs(intake.load(ex))
        blob = json.dumps(kw)
        self.assertNotIn("555-0100", blob)
        self.assertNotIn("Example Person", blob)
        self.assertIn("SHA-256", kw["notes"])
        self.assertIn("Requests to agency", kw["notes"])


class LoggerPageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parent.parent

    def test_logger_html_is_in_sync(self):
        sys.path.insert(0, str(self.ROOT / "tools"))
        import build_logger
        built = (self.ROOT / "web" / "logger.html").read_text(encoding="utf-8")
        self.assertEqual(built, build_logger.render(), "run: python tools/build_logger.py")

    def test_logger_never_uses_storage_or_network(self):
        web = self.ROOT / "web"
        for name in ("logger.template.html", "logger.core.js"):
            text = (web / name).read_text(encoding="utf-8")
            for banned in ("localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "document.cookie", "https://"):
                self.assertNotIn(banned, text, f"{name}: {banned}")
        built = (web / "logger.html").read_text(encoding="utf-8")
        self.assertIn("connect-src 'none'", built)
        self.assertIn("default-src 'none'", built)
        self.assertNotIn("<script src", (web / "logger.template.html").read_text(encoding="utf-8"))

    def test_logger_has_the_original_tabs_exports_and_flags(self):
        built = (self.ROOT / "web" / "logger.html").read_text(encoding="utf-8")
        for needle in ("INCIDENT LOGGER", "LOG INCIDENT", "HISTORY", "EXPORT", "SETTINGS",
                       "THREAT &amp; VIOLENCE" if False else "THREAT & VIOLENCE", "IDENTITY & HATE CRIME", "SURVEILLANCE & TRACKING",
                       "DOXXING & PRIVACY", "PLATFORM / ACCOUNT", "PATTERN & INTENT",
                       "PATTERN ANALYSIS", "DOWNLOAD AS .XLSX FILE", "DOWNLOAD AS .PDF FILE", "COPY TO CLIPBOARD",
                       "Full Incident Log", "IC3 Complaint Narrative", "Law Enforcement Report",
                       "AUDIT LOG", "DANGER ZONE", "STOP REQUEST DATE", "SAVED ACCOUNTS", "CASE FILE",
                       "HOW YOU FELT AT THE TIME", "SHA-256"):
            self.assertIn(needle, built)

    def test_vendor_licenses_ship_with_bundled_libraries(self):
        v = self.ROOT / "web" / "vendor"
        for name in ("xlsx.full.min.js", "xlsx.LICENSE", "jspdf.umd.min.js", "jspdf.LICENSE"):
            self.assertTrue((v / name).exists(), name)

    def test_intake_messages_carry_flag_ids_for_the_logger(self):
        raw = json.loads((self.ROOT / "examples" / "sample-intake.json").read_text(encoding="utf-8"))
        self.assertTrue(all("flags" in m for m in raw["messages"]))
