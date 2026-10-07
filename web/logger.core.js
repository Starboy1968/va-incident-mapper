// ─── CONSTANTS ────────────────────────────────────────────────────────────────
const PLATFORMS = ["TikTok","Discord","Instagram","Twitter/X","YouTube","Facebook","Reddit","Snapchat","LinkedIn","Email","Text/SMS","Phone Call","Other"];
const TYPES = ["Public Comment","@Mention","Reply to My Post","Reply to Others' Post","DM / Message Attempt","New Account Contact","Tagged Post","Live Comment","Story Mention","Share / Repost of My Content","Proxy Contact (via third party)","Email","Phone Call","Other"];

const STATUTES = {
  "Public Comment":["18 U.S.C. § 2261A — Course of Conduct","18 U.S.C. § 875(c) — Interstate Communication"],
  "@Mention":["18 U.S.C. § 2261A — Course of Conduct","18 U.S.C. § 1030 — CFAA (contested; only if post-ban)"],
  "Reply to My Post":["18 U.S.C. § 2261A — Course of Conduct"],
  "Reply to Others' Post":["18 U.S.C. § 2261A — Course of Conduct"],
  "DM / Message Attempt":["18 U.S.C. § 2261A — Surveillance/Contact","18 U.S.C. § 875(c) — if threatening"],
  "New Account Contact":["18 U.S.C. § 1030 — CFAA (contested)","18 U.S.C. § 2261A — Course of Conduct"],
  "Tagged Post":["18 U.S.C. § 2261A — Course of Conduct","18 U.S.C. § 875(c) — if threatening"],
  "Live Comment":["18 U.S.C. § 2261A — Course of Conduct"],
  "Story Mention":["18 U.S.C. § 2261A — Course of Conduct"],
  "Share / Repost of My Content":["18 U.S.C. § 2261A — Course of Conduct","VA § 18.2-152.7:1 — Harassment by Computer"],
  "Proxy Contact (via third party)":["18 U.S.C. § 2261A — Course of Conduct","42 U.S.C. § 1985(3) — Civil conspiracy remedy"],
  "Email":["18 U.S.C. § 2261A — Course of Conduct","47 U.S.C. § 223(a)(1) — Telecom Harassment"],
  "Phone Call":["18 U.S.C. § 2261A — Course of Conduct","47 U.S.C. § 223(a)(1) — Telecom Harassment"],
  "Other":["18 U.S.C. § 2261A — Course of Conduct"],
};

const FLAG_GROUPS = [
  { group:"THREAT & VIOLENCE", color:"#cc3333", flags:[
    {key:"explicitThreat",   label:"Explicit Threat of Violence",          statute:"18 U.S.C. § 875(c) — Interstate Threatening Communication"},
    {key:"impliedThreat",    label:"Implied / Veiled Threat",              statute:"18 U.S.C. § 875(c); Counterman v. Colorado (2023) recklessness standard"},
    {key:"deathThreat",      label:"Death Threat",                         statute:"18 U.S.C. § 875(c); VA § 18.2-60 — Threats of Death or Bodily Injury"},
    {key:"familyThreat",     label:"Threat Involving Family / Loved Ones", statute:"18 U.S.C. § 875(c); VA § 18.2-60 (covers family); 18 U.S.C. § 2261A"},
    {key:"propertyThreat",   label:"Threat to Property / Employment",      statute:"18 U.S.C. § 875(d) — only if made to extort; § 875(c) and VA § 18.2-60 cover injury threats, not property"},
  ]},
  { group:"IDENTITY & HATE CRIME", color:"#b044cc", flags:[
    {key:"racial",           label:"Racial / Ethnic Language",             statute:"Motive evidence only — 18 U.S.C. § 249 requires bodily injury"},
    {key:"religious",        label:"Religious Targeting",                  statute:"Motive evidence only — 18 U.S.C. § 249 requires bodily injury"},
    {key:"genderBased",      label:"Gender / Sexual Orientation Based",    statute:"Motive evidence only — 18 U.S.C. § 249(a)(2) requires bodily injury"},
    {key:"subordination",    label:"Racial Subordination Language",        statute:"Motive evidence only — 18 U.S.C. § 249 requires bodily injury"},
  ]},
  { group:"SURVEILLANCE & TRACKING", color:"#cc7700", flags:[
    {key:"surveillance",     label:"Surveillance / Tracking Admission",    statute:"18 U.S.C. § 2261A — Surveillance Element"},
    {key:"locationKnowledge",label:"Demonstrates Location Knowledge",      statute:"18 U.S.C. § 2261A — Surveillance; VA § 18.2-60.3 — Stalking"},
    {key:"employerKnowledge",label:"Demonstrates Employer Knowledge",      statute:"18 U.S.C. § 2261A — Surveillance Element"},
    {key:"routineKnowledge", label:"Demonstrates Routine / Schedule Knowledge", statute:"18 U.S.C. § 2261A — Surveillance Element"},
  ]},
  { group:"DOXXING & PRIVACY", color:"#cc5500", flags:[
    {key:"doxxThreat",       label:"Doxxing Threat (threatened to publish)", statute:"VA § 18.2-152.7:1 (computer threat of an illegal act); VA § 18.2-186.4 if published"},
    {key:"doxxCompleted",    label:"Doxxing Completed (PII published)",    statute:"VA § 18.2-186.4 — Use of Identity to Coerce, Intimidate or Harass; 18 U.S.C. § 2261A"},
    {key:"piiReference",     label:"References My Private Information",    statute:"VA § 18.2-152.7:1 — Harassment by Computer (if used to harass); § 18.2-186.4 if published"},
    {key:"familyPII",        label:"References Family Members' Information", statute:"VA § 18.2-186.4 if published; 18 U.S.C. § 2261A"},
  ]},
  { group:"PLATFORM / ACCOUNT", color:"#2288cc", flags:[
    {key:"postBan",          label:"Post-Ban — New Alt Account",           statute:"18 U.S.C. § 1030 — CFAA (contested after Van Buren)"},
    {key:"postBlock",        label:"Post-Block — Circumvented Block",      statute:"18 U.S.C. § 1030 — CFAA (contested); 18 U.S.C. § 2261A"},
    {key:"altAccountAdmit",  label:"Admitted to Multiple Accounts",        statute:"18 U.S.C. § 1030 — CFAA (contested); shows deliberate conduct"},
    {key:"impersonation",    label:"Impersonating Me / Identity Theft",    statute:"18 U.S.C. § 1028(a)(7) — only if another person's real identifying information is used in connection with a crime"},
  ]},
  { group:"PATTERN & INTENT", color:"#1a9e6e", flags:[
    {key:"postNotice",       label:"Post-Notice (after stop request)",     statute:"18 U.S.C. § 2261A — Intent / Course of Conduct After Notice"},
    {key:"permanence",       label:"Permanence / Won't Stop Declaration",  statute:"18 U.S.C. § 2261A — Substantial Emotional Distress Element"},
    {key:"entitlement",      label:"Entitlement / Impunity Language",      statute:"18 U.S.C. § 2261A — Intent; relevant to the Counterman recklessness standard"},
    {key:"coordination",     label:"Coordination with Other Actor",        statute:"42 U.S.C. § 1985(3) — Civil remedy; courts require class-based animus"},
    {key:"proxyHarassment",  label:"Proxy / Third-Party Harassment",       statute:"42 U.S.C. § 1985(3) — Civil remedy only; 18 U.S.C. § 2261A"},
    {key:"darvo",            label:"DARVO — Blaming Victim",               statute:"Consciousness of Guilt — Pattern Evidence"},
    {key:"manufactured",     label:"Manufactured Helplessness",            statute:"18 U.S.C. § 2261A — Substantial Emotional Distress"},
  ]},
];
const ALL_FLAGS = FLAG_GROUPS.flatMap(g => g.flags);

// ─── PLAIN-LANGUAGE KEY ─────────────────────────────────────────────────────
const STATUTE_KEY = [
  { code:"18 U.S.C. § 2261A", plain:"Federal cyberstalking law. Covers a course of conduct online, with intent to harass, intimidate or injure, that puts someone in reasonable fear of death or serious injury or causes substantial emotional distress. A direct threat is not required." },
  { code:"18 U.S.C. § 875(c)", plain:"Federal law against sending threats to injure or kidnap a person across state lines, including online. It does not cover threats to property." },
  { code:"18 U.S.C. § 1030 (CFAA)", plain:"Computer Fraud and Abuse Act. Covers unauthorized access to computers. Whether making a new account after a ban or block counts is contested after Van Buren v. United States (2021), so treat it as a possible theory for a lawyer to assess." },
  { code:"18 U.S.C. § 249", plain:"Federal hate crime law. It covers willfully causing bodily injury because of race, religion, national origin, gender, sexual orientation, gender identity or disability. Harassment or threats alone are not covered; bias language here is motive evidence." },
  { code:"18 U.S.C. § 1028", plain:"Federal identity theft law. Section 1028(a)(7) covers using another person's real identifying information, without permission, in connection with a crime. Fake profiles alone usually do not meet it." },
  { code:"18 U.S.C. § 2703(f)", plain:"Requires platforms to preserve records (IP addresses, account data, messages) once law enforcement requests it — used to stop evidence from being deleted." },
  { code:"42 U.S.C. § 1985(3)", plain:"Federal civil law. It lets a person sue for damages when two or more people conspire to deprive them of equal protection of the laws. Courts require class-based bias. It is not a criminal harassment law." },
  { code:"47 U.S.C. § 223", plain:"Federal telecom law. Section 223(a)(1) covers calls or other telecommunications-device use made with intent to abuse, threaten or harass a specific person: anonymously (C), or by repeated contact meant only to harass (E)." },
  { code:"VA § 18.2-152.7:1", plain:"Virginia's harassment-by-computer law. Covers using a computer or network, with intent to coerce, intimidate or harass, to send obscene or indecent language or threaten an illegal act. It does not mention doxxing." },
  { code:"VA § 18.2-186.4", plain:"Virginia law against publishing someone's name or photo together with identifying information, such as a home address, with intent to coerce, intimidate or harass them. This is the closest Virginia doxxing statute." },
  { code:"VA § 18.2-60.3", plain:"Virginia's stalking law. Covers conduct on more than one occasion, including by electronic communication, that intentionally places someone in reasonable fear of death, sexual assault or bodily injury." },
  { code:"VA § 18.2-60", plain:"Virginia's threat law. Covers threats to kill or injure a person or family member, including by email, text or social media post, that place them in reasonable fear." },
  { code:"Counterman Standard", plain:"Supreme Court standard (Counterman v. Colorado, 2023): a statement counts as a true threat if the person recklessly disregarded the risk their words would be seen as threatening." },
  { code:"Consciousness of Guilt", plain:"Not a statute — a legal concept. Behavior like blaming the victim (DARVO) or playing helpless after being confronted can be used as evidence the person knows what they did was wrong." },
];

const FLAG_GROUP_PLAIN = {
  "THREAT & VIOLENCE": "Any statement that threatens harm — direct, implied, or aimed at family, property, or a job.",
  "IDENTITY & HATE CRIME": "Language showing bias based on race, religion, gender, or sexual orientation. It is evidence of motive. Federal hate-crime law applies only when bodily injury occurs.",
  "SURVEILLANCE & TRACKING": "Statements proving the person knows details they shouldn't (location, workplace, schedule) — shows they're watching you.",
  "DOXXING & PRIVACY": "Publishing or threatening to publish private information about you or your family. Virginia's closest law covers publishing, not only threatening.",
  "PLATFORM / ACCOUNT": "Evidence the person is evading a ban or block, using fake accounts, or impersonating you.",
  "PATTERN & INTENT": "Evidence of a deliberate, ongoing pattern — continuing after being told to stop, coordinating with others, or manipulative behavior (DARVO, playing the victim).",
};

function plainLanguageKey() {
  const groupLines = FLAG_GROUPS.map(g => `  ${g.group}\n    ${FLAG_GROUP_PLAIN[g.group]}`).join("\n\n");
  const statuteLines = STATUTE_KEY.map(s => `  ${s.code}\n    ${s.plain}`).join("\n\n");
  return `${"═".repeat(60)}
KEY — PLAIN LANGUAGE (FOR NON-LAWYERS)
${"═".repeat(60)}
This section explains, in plain English, what the flag categories and
statute citations used in this report mean. Not legal advice.

FLAG CATEGORIES
${groupLines}

STATUTES REFERENCED
${statuteLines}
${"─".repeat(60)}`;
}

// ─── INTEGRITY / HASHING ─────────────────────────────────────────────────────
async function hashFile(file) {
  const buf = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", buf);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2,"0")).join("");
}

// ─── PATTERN / CLUSTERING (SIGNAL VS NOISE) ─────────────────────────────────
// Isolated incidents are noise; incidents clustering tightly in time are signal.
function computeClusters(incidents, windowDays=7, threshold=3) {
  const dated = incidents.filter(i=>i.incidentDate).map(i=>({...i, t:new Date(i.incidentDate+"T12:00:00").getTime()})).sort((a,b)=>a.t-b.t);
  const clusters = [];
  const msWindow = windowDays*24*60*60*1000;
  for (let i=0;i<dated.length;i++) {
    const windowIncs = dated.filter(d => d.t>=dated[i].t && d.t<dated[i].t+msWindow);
    if (windowIncs.length>=threshold) {
      const existing = clusters.find(c => c.start<=dated[i].t && dated[i].t<=c.end);
      if (!existing) clusters.push({ start: dated[i].t, end: dated[i].t+msWindow, incidents: windowIncs });
    }
  }
  // merge overlapping clusters
  const merged = [];
  clusters.sort((a,b)=>a.start-b.start).forEach(c=>{
    const last = merged[merged.length-1];
    if (last && c.start<=last.end) {
      last.end = Math.max(last.end,c.end);
      last.incidents = [...new Set([...last.incidents,...c.incidents])].sort((a,b)=>a.t-b.t);
    } else merged.push({...c});
  });
  return merged;
}

// ─── HELPERS ─────────────────────────────────────────────────────────────────
const todayStr = () => new Date().toISOString().split("T")[0];
const nowTimeStr = () => new Date().toTimeString().slice(0,5);
function displayTime(t24) {
  if (!t24) return "";
  const [h,m] = t24.split(":").map(Number);
  return `${h%12||12}:${String(m).padStart(2,"0")} ${h>=12?"PM":"AM"}`;
}
function longDate(isoDate) {
  if (!isoDate) return "[DATE NOT RECORDED]";
  return new Date(isoDate+"T12:00:00").toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"});
}
function shortDate(isoDate) {
  if (!isoDate) return "";
  return new Date(isoDate+"T12:00:00").toLocaleDateString("en-US",{month:"2-digit",day:"2-digit",year:"numeric"});
}

// ─── FEELINGS (added: how the victim felt at the time) ──────────────────────
function feelTxt(inc) {
  const a = [];
  if (inc.feelings?.length) a.push(inc.feelings.join("; "));
  if (inc.feelingsText) a.push(`In my words: "${inc.feelingsText}"`);
  return a.join(" | ");
}
function feelAll(incidents) {
  const f = [...new Set(incidents.flatMap(i => i.feelings || []))];
  const t = incidents.map(i => i.feelingsText).filter(Boolean)[0];
  const a = [];
  if (f.length) a.push(f.join("; "));
  if (t) a.push(`In my words: "${t}"`);
  return a.join(" | ");
}

function formatEntry(inc, stopDate, caseInfo) {
  const activeFlags = ALL_FLAGS.filter(f => inc.flags?.[f.key]);
  const flagStatutes = activeFlags.map(f => `    → ${f.statute}`).join("\n");
  const baseStatutes = (STATUTES[inc.type]||[]).map(s => `    → ${s}`).join("\n");
  const allStatutes = [baseStatutes, flagStatutes].filter(Boolean).join("\n");
  return `${"═".repeat(60)}
INCIDENT REPORT — INC-${String(inc.number).padStart(3,"0")}
${"═".repeat(60)}
${caseInfo?.localCase ? `Local Case #:     ${caseInfo.localCase}\n` : ""}${caseInfo?.ic3Number ? `IC3 Complaint #:  ${caseInfo.ic3Number}\n` : ""}
INCIDENT DATE/TIME
  Date:             ${longDate(inc.incidentDate)}
  Time:             ${inc.incidentTime ? displayTime(inc.incidentTime) : "[TIME NOT RECORDED]"}
  Logged:           ${inc.loggedDate} ${inc.loggedTime}

SUBJECT ACCOUNT
  Platform:         ${inc.platform}
  Display Name:     ${inc.displayName||"[NOT CAPTURED]"}
  Username/Handle:  ${inc.handle||"[NOT CAPTURED]"}
  User ID:          ${inc.userId||"[NOT CAPTURED]"}
  Profile URL:      ${inc.profileUrl||"[NOT CAPTURED]"}
  Archive Link:     ${inc.archiveUrl||"[NOT CAPTURED]"}

INCIDENT DETAILS
  Type:             ${inc.type}
  Content:          "${inc.content||"[NO CONTENT RECORDED]"}"
  Context:          ${inc.context||"N/A"}${feelTxt(inc) ? `\n  Felt at the time: ${feelTxt(inc)}` : ""}
  Screenshot:       ${inc.screenshot ? `YES — RETAINED (${inc.screenshotFilename||"file"})` : "Pending"}
  Screenshot Hash:  ${inc.screenshotHash ? `SHA-256: ${inc.screenshotHash}` : "N/A"}
  Screen Recording: ${inc.recording ? "YES — RETAINED" : "N/A"}

LEGAL FLAGS
  Active:           ${activeFlags.map(f=>f.label).join(", ")||"None"}

RESPONSE & REPORTING
  My Response:      NONE — SILENCE MAINTAINED
  Reported:         ${inc.reported ? `YES — ${inc.platform} | ${longDate(inc.incidentDate)}` : "PENDING"}
  Report Conf. #:   ${inc.reportConfirmation||"[NONE PROVIDED BY PLATFORM]"}
  Running Total:    ${inc.runningTotal}${stopDate ? `th contact since stop request on ${stopDate}` : "th documented incident"}

APPLICABLE STATUTES
${allStatutes || "    → 18 U.S.C. § 2261A — Course of Conduct"}
${"─".repeat(60)}`;
}

function formatIC3(incidents, caseInfo, stopDate) {
  const platforms = [...new Set(incidents.map(i=>i.platform))];
  const flagged = incidents.filter(i=>Object.values(i.flags||{}).some(Boolean));
  const first = incidents[0], last = incidents[incidents.length-1];
  const firstDate = first?.incidentDate ? longDate(first.incidentDate) : "[DATE]";
  const lastDate = last?.incidentDate ? longDate(last.incidentDate) : "[DATE]";
  const topThree = flagged.slice(0,3).map(i => {
    const st = ALL_FLAGS.filter(f=>i.flags?.[f.key]).map(f=>f.statute).slice(0,2).join("; ");
    return `  INC-${String(i.number).padStart(3,"0")} | ${shortDate(i.incidentDate)||i.loggedDate} | ${i.platform} | @${i.handle||"[handle]"}\n  Content: "${(i.content||"").substring(0,120)}${(i.content||"").length>120?"...":""}"\n  Statutes: ${st}`;
  }).join("\n\n");
  const allStatutesList = [...new Set(incidents.flatMap(i=>[...(STATUTES[i.type]||[]),...ALL_FLAGS.filter(f=>i.flags?.[f.key]).map(f=>f.statute)]))];
  return `${"═".repeat(60)}
IC3 COMPLAINT NARRATIVE — COPY INTO IC3 DETAILS FIELD
${"═".repeat(60)}
Generated: ${new Date().toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"})}
${caseInfo?.localCase ? `Local Case #: ${caseInfo.localCase}` : ""}
${caseInfo?.ic3Number ? `Prior IC3 #: ${caseInfo.ic3Number}` : ""}

COMPLAINT TYPE: Cyberstalking / Online Harassment / Coordinated Abuse

OVERVIEW:
I am filing this complaint regarding an ongoing cyberstalking and harassment
campaign. The campaign began on ${firstDate} and has continued to ${lastDate}.
I have documented ${incidents.length} separate incidents across ${platforms.join(", ")}.
I have not responded to any contact${stopDate ? ` since my stop request on ${stopDate}` : ""}.
All contact has continued despite my explicit requests to stop and platform bans.
${caseInfo?.localCase ? `References local law enforcement Case #${caseInfo.localCase}, ${caseInfo.agency||"[AGENCY]"}.` : ""}

${feelAll(incidents) ? `IMPACT ON REPORTING PARTY:\n  Felt at the time: ${feelAll(incidents)}\n\n` : ""}APPLICABLE FEDERAL STATUTES:
${allStatutesList.map(s=>`  - ${s}`).join("\n")}

DOCUMENTED INCIDENTS SUMMARY:
Total incidents: ${incidents.length}
Flagged / escalated: ${flagged.length}
Platforms: ${platforms.join(", ")}
${stopDate ? `Post-notice incidents: ${incidents.filter(i=>i.flags?.postNotice).length}` : ""}

PRIORITY EXHIBITS:
${topThree || "  [Log incidents with legal flags to auto-populate]"}

FULL INCIDENT LOG:
${incidents.map(i=>`INC-${String(i.number).padStart(3,"0")} | ${shortDate(i.incidentDate)||i.loggedDate} ${i.incidentTime?displayTime(i.incidentTime):""} | ${i.platform} | @${i.handle||"[handle]"} | ${i.type}\n"${(i.content||"[no content]").substring(0,200)}${(i.content||"").length>200?"...":""}"\n${ALL_FLAGS.filter(f=>i.flags?.[f.key]).length?"FLAGS: "+ALL_FLAGS.filter(f=>i.flags?.[f.key]).map(f=>f.label).join(", "):""}`).join("\n\n")}

EVIDENCE PRESERVATION REQUEST (18 U.S.C. § 2703(f)):
${platforms.map(p=>`  - ${p}`).join("\n")}
Records requested: IP addresses, device fingerprints, phone numbers used for
registration, account creation timestamps, all linked accounts, login history.

All evidence retained and available upon request.
${"═".repeat(60)}

${plainLanguageKey()}`;
}

function formatSheriff(incidents, caseInfo, stopDate, victimInfo) {
  const platforms = [...new Set(incidents.map(i=>i.platform))];
  const flagged = incidents.filter(i=>Object.values(i.flags||{}).some(Boolean));
  const first = incidents[0], last = incidents[incidents.length-1];
  return `${"═".repeat(60)}
LAW ENFORCEMENT UPDATE REPORT
${"═".repeat(60)}
Date: ${new Date().toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"})}
To: ${caseInfo?.detective||"[DETECTIVE NAME]"}, ${caseInfo?.agency||"[AGENCY]"}
Re: Case #${caseInfo?.localCase||"[CASE NUMBER]"} — Ongoing Cyberstalking/Harassment
${caseInfo?.ic3Number ? `IC3 #: ${caseInfo.ic3Number}` : ""}
From: ${victimInfo?.name||"[NAME]"} | ${victimInfo?.phone||"[PHONE]"} | ${victimInfo?.email||"[EMAIL]"}

SUMMARY:
${incidents.length} incidents documented between ${first?.incidentDate?longDate(first.incidentDate):first?.loggedDate||"[DATE]"} and ${last?.incidentDate?longDate(last.incidentDate):last?.loggedDate||"[DATE]"}.
${flagged.length} incidents flagged with elevated legal significance.
Platforms: ${platforms.join(", ")}
${stopDate ? `ALL incidents occurred AFTER stop request on ${stopDate}.\nEach is evidence of continued contact after notice, relevant to 18 U.S.C. § 2261A. Whether it is a violation is for law enforcement and the court to decide.` : ""}

${feelAll(incidents) ? `IMPACT ON REPORTING PARTY:\n  Felt at the time: ${feelAll(incidents)}\n\n` : ""}INCIDENT LOG:
${incidents.map(i=>{
  const af = ALL_FLAGS.filter(f=>i.flags?.[f.key]);
  return `INC-${String(i.number).padStart(3,"0")}  ${shortDate(i.incidentDate)||i.loggedDate} ${i.incidentTime?displayTime(i.incidentTime):""}
  Platform: ${i.platform} | Account: ${i.displayName||"[name]"} (@${i.handle||"[handle]"}) | User ID: ${i.userId||"[not captured]"}
  Type: ${i.type}
  Content: "${i.content||"[no content recorded]"}"
  ${af.length?"FLAGS: "+af.map(f=>f.label).join(" | "):""}
  Reported to platform: ${i.reported?"YES":"PENDING"}`;
}).join("\n\n")}

REQUESTED ACTIONS:
1. Issue 18 U.S.C. § 2703(f) preservation letters to: ${platforms.join(", ")}
2. Contact platform law enforcement portals with case number
3. Refer to FBI field office — interstate conduct satisfies federal jurisdiction
${flagged.some(i=>i.flags?.racial||i.flags?.subordination)?"4. Refer to FBI Civil Rights Division — racial bias language documented (18 U.S.C. § 249 applies only if bodily injury occurred; otherwise motive evidence)":""}

All screenshots and recordings retained and available upon request.
${"─".repeat(60)}

${plainLanguageKey()}`;
}

// ─── DOWNLOAD HELPER ─────────────────────────────────────────────────────────
function downloadTxt(text, filename) {
  const blob = new Blob([text], {type:"text/plain;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// ─── XLSX / PDF EXPORT ─────────────────────────────────────────────────────────
function downloadXlsx(incidents, stopDate, caseInfo, filename) {
  const rows = incidents.map(i => {
    const af = ALL_FLAGS.filter(f => i.flags?.[f.key]);
    return {
      "INC #": `INC-${String(i.number).padStart(3,"0")}`,
      "Incident Date": i.incidentDate ? longDate(i.incidentDate) : "",
      "Incident Time": i.incidentTime ? displayTime(i.incidentTime) : "",
      "Logged Date": i.loggedDate || "",
      "Logged Time": i.loggedTime || "",
      "Platform": i.platform || "",
      "Type": i.type || "",
      "Display Name": i.displayName || "",
      "Handle": i.handle || "",
      "User ID": i.userId || "",
      "Profile URL": i.profileUrl || "",
      "Archive Link": i.archiveUrl || "",
      "Content": i.content || "",
      "Context": i.context || "",
      "Screenshot": i.screenshot ? "YES" : "",
      "Screenshot SHA-256": i.screenshotHash || "",
      "Recording": i.recording ? "YES" : "",
      "Reported": i.reported ? "YES" : "PENDING",
      "Report Confirmation #": i.reportConfirmation || "",
      "Legal Flags": af.map(f=>f.label).join("; "),
      "Applicable Statutes": [...(STATUTES[i.type]||[]), ...af.map(f=>f.statute)].join("; "),
      "Post-Notice": stopDate ? "YES" : "",
    };
  });
  const ws = XLSX.utils.json_to_sheet(rows);
  ws["!cols"] = Object.keys(rows[0]||{}).map(k => ({ wch: Math.min(Math.max(k.length, 14), 45) }));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Incidents");
  if (caseInfo?.localCase || caseInfo?.ic3Number || stopDate) {
    const meta = [
      ["Local Case #", caseInfo?.localCase||""],
      ["IC3 Complaint #", caseInfo?.ic3Number||""],
      ["Agency", caseInfo?.agency||""],
      ["Stop Request Date", stopDate||""],
      ["Total Incidents", incidents.length],
    ];
    const metaWs = XLSX.utils.aoa_to_sheet(meta);
    XLSX.utils.book_append_sheet(wb, metaWs, "Case Info");
  }
  const keyRows = [
    ["FLAG CATEGORIES", ""],
    ...FLAG_GROUPS.map(g => [g.group, FLAG_GROUP_PLAIN[g.group]]),
    ["", ""],
    ["STATUTES REFERENCED", ""],
    ...STATUTE_KEY.map(s => [s.code, s.plain]),
  ];
  const keyWs = XLSX.utils.aoa_to_sheet(keyRows);
  keyWs["!cols"] = [{ wch: 26 }, { wch: 90 }];
  XLSX.utils.book_append_sheet(wb, keyWs, "Key (Plain Language)");
  XLSX.writeFile(wb, filename);
}

function downloadPdf(text, filename) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "pt", format: "letter" });
  const margin = 40;
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const maxWidth = pageWidth - margin*2;
  doc.setFont("Courier", "normal");
  doc.setFontSize(8.5);
  const safeText = text
    .replace(/[═─]/g, "-")
    .replace(/→/g, "->")
    .replace(/[""]/g, '"')
    .replace(/['']/g, "'")
    .replace(/[^\x00-\x7F]/g, "?");
  const lines = doc.splitTextToSize(safeText, maxWidth);
  let y = margin;
  const lineHeight = 11;
  lines.forEach(line => {
    if (y > pageHeight - margin) { doc.addPage(); y = margin; }
    doc.text(line, margin, y);
    y += lineHeight;
  });
  doc.save(filename);
}
