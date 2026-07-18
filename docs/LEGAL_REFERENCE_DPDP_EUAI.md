# DPDP & EU AI Act — Detailed Legal Reference (for ComplyKit / CompliSense rulepacks)

> **version: 1.0.0 · last_verified: 2026-06-26**
> Companion files: [`SOURCES.md`](SOURCES.md), [`SOURCES_ACT.md`](SOURCES_ACT.md),
> review tracker [`../LEGAL_REVIEW_NEEDED.md`](../LEGAL_REVIEW_NEEDED.md).
>
> Built 2026-06-26 from primary sources. DPDP section is grounded in the **actual
> Gazette text** of the DPDP Rules 2025 (G.S.R. 846(E), 13 Nov 2025) fetched directly.
> EU AI Act section is grounded in the European Commission digital-strategy pages,
> EUR-Lex Regulation (EU) 2024/1689, and corroborating legal analyses.
> **This is an engineering reference, NOT legal advice. Every rule built from this
> must still pass professional legal review (see CAVEATS at end).**

---

# PART A — INDIA: DPDP ACT 2023 + DPDP RULES 2025

## A.0 Structure & enforcement timeline (VERIFIED from Gazette)
- **Act:** Digital Personal Data Protection Act, 2023 (22 of 2023) — principles, rights,
  penalties, definitions.
- **Rules:** Digital Personal Data Protection Rules, 2025 — notified 13 Nov 2025,
  published in Gazette 14 Nov 2025. Operationalise the Act.
- **Commencement (Rule 1(2)–(4), verbatim):**
  - Rules **1, 2, 17–21**: in force **on publication (13 Nov 2025)** — Board
    constitution, definitions, procedural machinery.
  - Rule **4** (Consent Manager registration/obligations): in force **one year after
    publication (~Nov 2026)**.
  - Rules **3, 5–16, 22, 23**: in force **eighteen months after publication (~13 May
    2027)** — this is the bulk of operational compliance.
- **Three-phase enforcement (single source of truth for marketing + rulepack copy; verified
  18 Jul 2026 against Shardul Amarchand Mangaldas, iPleaders, Astra, Vratex, Kraver):**
  Notified 13/14 Nov 2025 (gazette G.S.R. 846(E)); staggered, 3 phases.
  - **PHASE 1 — LIVE NOW (since 13 Nov 2025):** Data Protection Board of India established
    and operational; all 28 definitions (s.2) legally operative; administrative machinery +
    complaint portal live; the penalty framework under **s.33 exists in law (up to ₹250 crore
    per violation)**. What is live is the *machinery*, not the substantive duties.
  - **PHASE 2 — 13 Nov 2026:** Consent Manager registration opens; the Board's enforcement /
    inquiry powers and penalty imposition for breach of registration conditions begin. NOTE:
    Jan 2026 MeitY consultations proposed compressing the 18-month window to 12 months — a real
    acceleration risk; frame as "may move up", not certain.
  - **PHASE 3 — 13 May 2027:** substantive operational obligations (notice, consent, security,
    breach, retention, data-principal rights, cross-border) fully enforceable. **NO grace period.**
- **Accuracy guardrail (counsel instruction):** do NOT claim substantive obligations
  (e.g. "you can be fined today for lacking a privacy notice") are enforced now — they are not
  until 13 May 2027. "Live now" claims are limited to: the Board being operational, definitions
  in force, the complaint portal, and the penalty framework existing in law. Overstating current
  enforcement damages a compliance brand's credibility; precision is the selling point.
- **Framing for the product:** the Board + penalty framework are LIVE NOW, but the core
  operational obligations are NOT yet enforceable — this is a "prepare for 13 May 2027" tool,
  NOT a "you are in violation today" tool. Say so everywhere.
- **Territorial scope:** applies to processing within India AND extraterritorially to
  entities offering goods/services to individuals in India (Act s.3).
- **Key roles:** Data Fiduciary (≈ controller; determines purpose & means), Data
  Processor (processes on behalf), Data Principal (the individual), Consent Manager
  (registered intermediary), Significant Data Fiduciary (SDF; govt-notified).

## A.1 Penalties (from the Schedule to the DPDP Act 2023 — verify exact figures)
- ₹250 crore — failure to take reasonable security safeguards (s.8(5)).
- ₹200 crore — failure to notify Board/Data Principals of a breach (s.8(6)).
- ₹200 crore — non-compliance with children's-data provisions (s.9).
- ₹150 crore — failure of additional SDF obligations (s.10).
- ₹10,000 — breach of Data Principal duties (s.15).
- Board weighs nature, gravity, duration, affected count, history, remediation.
- NOTE: secondary sources vary slightly (one said ₹150cr SDF, another implied
  different splits). Treat figures as "verify against the Act Schedule before
  publishing." The crore-level magnitudes are correct.

## A.2 Rule-by-rule (VERIFIED from Gazette text)

**Rule 3 — Notice by Data Fiduciary.** The consent notice must:
- (a) be presented & understandable **independently** of any other info (no burying in
  a 20-page T&C);
- (b) in clear & plain language, give a fair account enabling specific & informed
  consent, including **at minimum**: (i) an **itemised description** of the personal
  data; (ii) the **specified purpose(s)** AND a specific description of the goods/
  services/uses enabled;
- (c) give the communication link (website/app) + description of other means by which
  the Data Principal may (i) **withdraw consent** with ease comparable to giving it,
  (ii) exercise her rights, (iii) complain to the Board.
- (Eighth Schedule language availability is an Act-level point reflected in analyses;
  the Rule text itself emphasises plain language + independent presentation.)
- Enforcement: ~May 2027.

**Rule 4 — Consent Manager registration & obligations.** Registration via the Board;
conditions in First Schedule Part A; obligations in Part B. Enforcement: ~Nov 2026.
First Schedule Part A (registration conditions, VERIFIED): company incorporated in
India; sufficient technical/operational/financial capacity; sound financials;
**net worth ≥ ₹2 crore**; fit-and-proper management; MoA/AoA provisions; operations in
Data Principals' interest; independent certification of interoperable platform.
First Schedule Part B (Consent Manager obligations, VERIFIED, key ones):
- enable give/manage/review/withdraw consent;
- **must NOT be able to read the contents** of personal data shared;
- maintain record of consents given/denied/withdrawn, notices, and data sharing;
- give Data Principal access to that record, in **machine-readable form** on request;
- **retain such record ≥ 7 years** (or longer if agreed/required);
- website/app as primary interface;
- **no sub-contracting/assignment** of obligations;
- reasonable security safeguards; act in fiduciary capacity; avoid conflicts of
  interest; transparency disclosures; audit mechanisms reporting to Board; control not
  transferred without Board approval.

**Rule 5 — State processing for subsidy/benefit/service/etc.** Governed by Second
Schedule standards. Lawful, purpose-limited, accurate, secure, accountable. Mostly
relevant to govt bodies & their tech partners. Enforcement: ~May 2027.

**Rule 6 — Reasonable security safeguards (VERIFIED, the operational core).** A Data
Fiduciary (incl. for processing by its Data Processor) must take safeguards including
**at minimum**:
- (a) data security measures such as **encryption, obfuscation, masking, or virtual
  tokens** mapped to the personal data;
- (b) **access controls** on the computer resources used;
- (c) **visibility via logs, monitoring & review** to detect/investigate/remediate
  unauthorised access;
- (d) reasonable measures for **continued processing** if confidentiality/integrity/
  availability is compromised, e.g. **data backups**;
- (e) **retain logs and personal data for one year** (for detection/investigation/
  remediation/continuity) unless another law requires otherwise;
- (f) **contractual safeguard provisions** in the Data Fiduciary–Data Processor
  contract;
- (g) appropriate technical & organisational measures for effective observance.
- Enforcement: ~May 2027.
- NOTE: secondary sources said "seven controls" / "MFA mandatory" — the **Gazette text
  does NOT enumerate seven, and does NOT explicitly mandate MFA**. It lists (a)–(g)
  above. Build rules from (a)–(g), not the secondary "7 controls/MFA" gloss. This is
  exactly the kind of secondary-source drift the grounding step exists to catch.

**Rule 7 — Intimation of personal data breach (VERIFIED, two tracks).**
- To **each affected Data Principal**: on becoming aware, **without delay**, via her
  user account / registered comms — describe the breach (nature, extent, timing);
  likely consequences to her; mitigation measures taken/being taken; safety measures
  she can take; business contact of a responder.
- To the **Board**: (a) **without delay** — a description (nature, extent, timing,
  location, likely impact); (b) **within 72 hours** (or longer if Board allows on
  written request) — updated detailed info, broad facts/causes, mitigation measures,
  findings on who caused it, remedial measures to prevent recurrence, and a report on
  the intimations given to affected principals.
- Enforcement: ~May 2027.
- NOTE: the "72 hours" applies to the **detailed Board report**, with an initial
  "without delay" intimation preceding it. Earlier secondary framing ("72h to Board
  and principals") was imprecise. Principals get "without delay," not a 72h clock.

**Rule 8 — Erasure / retention time periods (VERIFIED).**
- (1) Data Fiduciaries of a **class specified in the Third Schedule** must erase
  personal data when the Data Principal neither approaches them for the purpose nor
  exercises rights for the specified period — unless retention needed for legal
  compliance.
- (2) **At least 48 hours before** erasure, inform the Data Principal that data will be
  erased unless she logs in / initiates contact / exercises rights.
- (3) **Separate one-year minimum retention**: for ANY processing, retain personal
  data, associated traffic data & logs **≥ 1 year** (per Seventh Schedule purposes),
  then erase unless another law requires longer.
- **Third Schedule classes & period (VERIFIED):** (1) e-commerce entity ≥ **2 crore**
  registered users; (2) online gaming intermediary ≥ **50 lakh** registered users;
  (3) social media intermediary ≥ **2 crore** registered users. Period = **3 years**
  from last approach/rights-exercise OR Rules commencement, whichever is latest.
  Exceptions: accessing user account / accessing a virtual token for money/goods/
  services.
- IMPORTANT for our ICP: the 3-year-erasure rule applies ONLY to those large classes.
  **Most startups are NOT in scope of Rule 8(1)** — but the **1-year retention floor
  (8(3)) applies to all.** A rule must check class applicability.
- Enforcement: ~May 2027.

**Rule 9 — Contact info for processing questions (VERIFIED).** Every Data Fiduciary
must prominently publish on website/app, and include in every rights-response, the
business contact of the **DPO (if applicable)** or a person who can answer Data
Principal questions. (DPO is only mandatory for SDFs; others publish a responder.)
Enforcement: ~May 2027.

**Rule 10 — Verifiable parental consent for children (VERIFIED).**
- Obtain **verifiable consent of the parent** before processing any child's data;
  due diligence that the self-identified parent is an **adult (≥18)**, identifiable if
  required by law, by reference to: (a) reliable identity/age details already held; or
  (b) details voluntarily provided by the individual or via a **virtual token** issued
  by an **authorised entity** (incl. **Digital Locker Service Provider**).
- "Child" = under 18 (Act definition).
- NOTE: the **Act s.9** carries the substantive bans (no tracking/behavioural
  monitoring/targeted advertising to children); Rule 10 operationalises the
  *verification*. Secondary sources merged these — keep the citation precise:
  bans = Act s.9; verification mechanics = Rule 10.
- Enforcement: ~May 2027.

**Rule 11 — Verifiable consent for persons with disability w/ lawful guardian
(VERIFIED).** Verify the guardian is appointed by a court / designated authority /
local-level committee under applicable guardianship law (RPwD Act 2016; National Trust
Act 1999). Enforcement: ~May 2027.

**Rule 12 — Exemptions for children's-data obligations (VERIFIED).** Section 9(1)&(3)
do NOT apply to classes in **Fourth Schedule Part A** (e.g. clinical/mental-health
establishments & healthcare professionals; allied healthcare; **educational
institutions** for educational activity / child safety; crèche/daycare; child
transport — each restricted to its safety/health purpose) and purposes in **Part B**
(e.g. legal duties in a child's interest; subsidies/benefits; **email-account
creation**; real-time location for child safety; blocking detrimental content;
confirming a user is not a child). Enforcement: ~May 2027.

**Rule 13 — Additional SDF obligations (VERIFIED).**
- Every 12 months: **Data Protection Impact Assessment (DPIA) + audit**; the assessor
  furnishes a report of significant observations to the Board.
- Due diligence that **algorithmic software** used does not pose risk to Data
  Principals' rights.
- Comply with Central-Govt-specified **data-localisation** restrictions (certain
  personal & traffic data not transferred outside India), per a govt committee.
- Applies ONLY to entities **notified as SDF** by the Central Government (by volume/
  sensitivity/risk). **Most startups are NOT SDFs** — rules must gate on this.
- (DPO-in-India requirement is an Act s.10 SDF obligation; reflected here.)
- Enforcement: ~May 2027.

**Rule 14 — Rights of Data Principals (VERIFIED).**
- Data Fiduciary (and Consent Manager where applicable) must **prominently publish**
  the means to make a rights request + any required identifier.
- Data Principal exercises rights by request to the Fiduciary she gave consent to.
- **Grievance redressal**: publish the system and respond within a period **not
  exceeding 90 days**.
- Right to nominate; "identifier" defined broadly (customer ID, email, mobile, etc.).
- Rights themselves (access, correction, erasure, grievance, nomination) come from the
  **Act ss.11–14**; Rule 14 operationalises exercise + the 90-day grievance window.
- Enforcement: ~May 2027.

**Rule 15 — Cross-border transfer (VERIFIED).** Personal data MAY be transferred
outside India, **subject to restrictions the Central Government may specify** by
general/special order re making data available to foreign States/entities under their
control. (Liberalised "blacklist" approach, not a GDPR-style adequacy whitelist.)
Enforcement: ~May 2027.

**Rule 16 — Research/archiving/statistical exemption (VERIFIED).** Act does not apply
to such processing if done per Second Schedule standards. Enforcement: ~May 2027.

**Rules 17–23 — Board/Tribunal machinery (VERIFIED).** Board composition, salaries,
meetings, digital-office functioning (17–21, in force now), appeals to Appellate
Tribunal (22), Central Govt calling for information (23). Mostly not relevant to a
Data Fiduciary self-assessment scanner, except Rule 23 (govt info requests) and the
Board's 6-month (extendable +3) inquiry window.

## A.3 Implications for our `dpdp_india_core_v1` pack (corrections)
1. **Reframe to "readiness for May 2027"** everywhere. Nothing operational is live yet.
2. **Rule 6 controls = Gazette (a)–(g), not "7 controls + MFA."** Drop the secondary
   gloss. Encryption/obfuscation/masking/tokens; access control; logging/monitoring;
   backups; 1-yr log+data retention; processor-contract clause; T&O measures.
3. **Breach (Rule 7) = two tracks** with different clocks: principals "without delay";
   Board "without delay" + detailed report "within 72h." Encode both.
4. **Retention is two distinct obligations:** 8(1) class-based 3-yr erasure (ONLY for
   the 3 large classes) + 8(3) universal 1-yr retention floor. Most startups: only
   8(3) applies. Gate on class.
5. **Children (Rule 10) cite correctly:** verification mechanics = Rule 10; the
   substantive no-tracking/no-targeted-ads bans = Act s.9. Add the Fourth-Schedule
   exemptions (Rule 12) so e.g. ed-tech / health aren't false-flagged.
6. **SDF (Rule 13) must gate on "notified as SDF."** Do NOT flag DPIA/audit/
   localisation gaps for a normal startup. Applicability condition mandatory.
7. **DPO (Rule 9 vs s.10):** a DPO is only mandatory for SDFs; everyone else must
   publish a contact/responder. Don't tell a 5-person startup it needs a DPO.
8. **Consent Manager (Rule 4 / First Schedule):** an *extended-pack* readiness item
   (integration + 7-yr consent records), live earlier (~Nov 2026). Most startups will
   integrate WITH consent managers, not become one.
9. **Cross-border (Rule 15):** currently liberalised; encode as "transfer allowed
   subject to future govt restrictions" — do NOT assert a hard block.

---

# PART B — EU AI ACT (Regulation (EU) 2024/1689)

## B.0 Structure & timeline (VERIFIED — and CHANGED in 2026; READ THIS)
- Entered into force **1 Aug 2024**. Phased application.
- **Prohibited practices (Art. 5) + AI-literacy (Art. 4): in force since 2 Feb 2025.**
- **GPAI model obligations (Arts. 51–55, Chapter V): in force since 2 Aug 2025.**
- **Transparency (Art. 50): from 2 Aug 2026 — UNCHANGED, now IMMINENT.** The Omnibus did
  NOT move this date. Art. 50(2) machine-readable marking for systems already on the
  market (legacy) is scheduled for **2 Dec 2026**.
- **High-risk (Annex III) obligations — Digital Omnibus on AI now FINAL:** the Digital
  Omnibus on AI was **adopted by the European Parliament on 16 June 2026 and by the
  Council on 29 June 2026, and is in force from July 2026**. It **CONFIRMS** the
  deferral of Annex III stand-alone high-risk obligations (Arts 9–15, 17, 43, 49, 72) to
  **2 December 2027**, and Annex I product-embedded high-risk to **2 August 2028**.
  - As of 2026-07-18 these dates are treated as **`phased_confirmed`** in the v2 packs
    (was `provisional_pending_amendment` in v1). They remain **secondary-sourced** —
    verify against the consolidated OJ text before any unqualified public claim.
- **New Art. 5 prohibition (Omnibus):** AI systems generating **non-consensual intimate
  imagery (NCII) and CSAM** ("nudifiers") are prohibited from **2 December 2026**
  (`EUAI-ART5-PROHIBITED-002`, secondary-sourced, pending legal review).
- **Omnibus timeline (as of 2026-07-18):** EP adoption **16 Jun 2026** → Council adoption
  **29 Jun 2026** → **in force Jul 2026**. Art. 50 transparency **2 Aug 2026**; Art. 50(2)
  legacy marking + new NCII/CSAM prohibition **2 Dec 2026**; Annex III high-risk
  **2 Dec 2027**; Annex I embedded high-risk **2 Aug 2028**.
- **Penalties (Art. 99):** up to **€35M or 7%** global turnover (prohibited practices);
  **€15M or 3%** (high-risk non-compliance); **€7.5M or 1%** (incorrect info to
  authorities). SME/startup proportionate caps apply.
- **Extraterritorial (Art. 2):** applies to providers placing systems on the EU market,
  deployers in the EU, AND providers/deployers outside the EU if the **output is used
  in the EU**. Open-source AI systems are exempt UNLESS prohibited or high-risk.

## B.1 Roles (Art. 3) — misidentifying role = wrong obligations
- **Provider** — develops / has developed and places on market under own name/mark.
  Heaviest obligations.
- **Deployer** — uses an AI system under its authority (in the EU, or output used in
  EU). Lighter but real obligations (human oversight, monitoring, transparency to
  affected persons, incident reporting).
- **Importer / Distributor / Product manufacturer** — supply-chain roles.
- **Quasi-provider (Art. 25)** — a deployer who substantially modifies / rebrands can
  become a provider.
- A single org can hold multiple roles. CRITICAL for our scanner: ask role first; a
  startup *using* ChatGPT/Copilot is a **deployer**, not a provider.

## B.2 Risk tiers
- **Unacceptable (Art. 5, BANNED since Feb 2025):** social scoring; untargeted facial-
  image scraping; emotion recognition in workplace/education; biometric categorisation
  inferring sensitive attributes; subliminal/manipulative techniques; certain real-time
  remote biometric ID in public for law enforcement (narrow exceptions).
- **High-risk (Art. 6 + Annex III):** biometrics; critical infrastructure; education;
  employment/recruitment; access to essential private/public services (credit scoring,
  insurance pricing); law enforcement; migration/border; justice. Plus Annex I
  product-safety-component systems.
- **Limited risk (Art. 50 transparency):** chatbots, deepfakes, AI-generated content —
  must disclose AI nature / label synthetic content.
- **Minimal risk:** no mandatory obligations (spam filters, game AI).

## B.3 Obligations by bucket
**Provider of high-risk (Arts. 9–17, applies Dec 2027 per Omnibus):** risk-management
system; data governance (Art. 10); technical documentation (Annex IV); record-keeping/
logging; transparency & instructions to deployers; human-oversight design (Art. 14);
accuracy/robustness/cybersecurity (Art. 15); quality-management system; conformity
assessment + CE marking; EU database registration; post-market monitoring; serious-
incident reporting.
**Deployer of high-risk (Art. 26–27):** use per instructions; ensure human oversight;
monitor; keep logs; transparency to affected persons; **Fundamental Rights Impact
Assessment (FRIA, Art. 27)** for certain deployers (public bodies, essential
services); serious-incident reporting.
**GPAI model provider (Arts. 53–55, LIVE since Aug 2025):** technical documentation
(Annex XI); info/documentation to downstream providers; **copyright policy** (text-&-
data-mining); **public summary of training content**. Free-and-open-licence GPAI: only
copyright + training-summary, **unless systemic**. **Systemic-risk GPAI** (>10^25 FLOPs
or Commission-designated): + model evaluations, adversarial testing, serious-incident
tracking/reporting, cybersecurity. **GPAI Code of Practice** (July 2025) = voluntary,
gives presumption of conformity.
**Art. 50 transparency (from Aug 2026):** disclose AI interaction (chatbots); label
AI-generated/deepfake content; emotion-recognition/biometric-categorisation notice.
**Art. 4 AI literacy (LIVE since Feb 2025):** providers & deployers ensure staff AI
literacy.

## B.4 Implications for a future `euai_*` pack (when we build it; not in the free
core launch)
1. **The timeline is contested and moving (Omnibus).** Encode `enforcement_date` as
   provisional with a source + "as of" date. This is the #1 accuracy risk. Auto-update
   watcher (CompliSense Phase 5) is genuinely needed here, not optional.
2. **Role-gate everything.** Ask provider/deployer/GPAI first; most startups are
   *deployers* of third-party AI or *GPAI downstream integrators*, with far lighter
   duties than they fear. Don't over-flag.
3. **What's LIVE now (build these first):** Art. 5 prohibitions, Art. 4 AI literacy,
   GPAI provider obligations (Arts. 53–55). These are enforceable today.
4. **What's deferred (frame as "prepare"):** high-risk provider/deployer obligations
   (Dec 2027), Art. 50 transparency (Aug 2026).
5. **GPAI = the relevant hook for AI startups** building on/with foundation models:
   technical docs, downstream documentation, copyright policy, training-data summary;
   systemic-risk only for frontier labs.
6. **Open-source exemption** matters for your ICP — many will be exempt unless
   prohibited/high-risk. Encode the exemption.

---

# PART C — CAVEATS & WHAT THIS CHANGES

## What the grounding caught (proof the step was worth it)
- DPDP **Rule 6** does NOT mandate "7 controls + MFA" (a common secondary-source
  gloss); the Gazette lists (a)–(g). We'd have shipped a wrong check.
- DPDP **breach** clocks: principals = "without delay"; Board detailed report = 72h.
  Not "72h to everyone."
- DPDP **retention** is two separate obligations (class-based 3yr vs universal 1yr
  floor); only large classes hit the 3yr rule.
- DPDP **SDF / DPO** obligations must be applicability-gated; most startups are neither
  SDF nor DPO-required. Over-flagging would destroy credibility with the exact ICP.
- DPDP enforcement is **~May 2027**, not now → "readiness," not "violation."
- EU AI Act high-risk deadline **moved** (Omnibus): Aug 2026 → **2 Dec 2027**, now
  CONFIRMED by the final Digital Omnibus on AI (EP 16 Jun 2026, Council 29 Jun 2026,
  in force Jul 2026). v2 packs tag this `phased_confirmed` (secondary-sourced).

## Hard caveats
- This doc is an engineering reference compiled from primary text + reputable analysis.
  It is NOT legal advice and is NOT exhaustive (e.g. interactions with sectoral laws,
  the Act's own sections behind each Rule, and pending notifications are not fully
  reproduced here).
- DPDP figures (penalties) and a few Act-level specifics should be cross-checked
  against the **Act Schedule and ss.7–17** before any rule asserts them.
- The Digital Omnibus on AI is now FINAL (in force Jul 2026), so the headline EU high-risk
  dates are `phased_confirmed` rather than provisional. They remain **secondary-sourced** —
  verify against the consolidated OJ text before any unqualified public claim.
- **Required next step:** professional review by (a) an Indian data-protection
  practitioner for DPDP and (b) an EU AI Act specialist, before unqualified public
  compliance claims. Maintain `LEGAL_REVIEW_NEEDED.md` and a per-pack reviewer sign-off.

## Primary sources used
- DPDP Rules 2025 full Gazette text: dpdpa.com/DPDP_Rules_2025_English_only.pdf
  (G.S.R. 846(E), MeitY, 13 Nov 2025) — fetched in full.
- DPDP Act 2023 (22 of 2023) — referenced via Rules + analyses (EY, Lexology, Ikigai,
  Securiti, PIB release).
- EU AI Act: European Commission digital-strategy (ec.europa.eu), EUR-Lex Reg (EU)
  2024/1689, artificialintelligenceact.eu high-level summary, White & Case, plus
  2026 Omnibus-deferral analyses (legiscope, surecloud, decodethefuture).
