# SOURCES.md — source-of-truth registry for CompliSense rulepacks

> **Last verified: 2026-06-26.** Built from primary text where marked
> `primary_source_verified`; from official/secondary analysis otherwise. This is an
> engineering reference, **not legal advice**. The detailed narrative grounding lives in
> [`LEGAL_REFERENCE_DPDP_EUAI.md`](LEGAL_REFERENCE_DPDP_EUAI.md); the DPDP Act-level
> companion is [`SOURCES_ACT.md`](SOURCES_ACT.md). Every rule's review state is tracked in
> [`../LEGAL_REVIEW_NEEDED.md`](../LEGAL_REVIEW_NEEDED.md).

Each row: obligation → Act citation → Rule/Article → enforcement date → source → 1-line summary.

## Enforcement timeline (honest framing)

- **DPDP (India):** Board/procedural Rules (1, 2, 17–21) in force 13 Nov 2025. Consent
  Manager (Rule 4) ~Nov 2026. **Operational bulk (Rules 3, 5–16): ~13 May 2027.** This is
  a *prepare-for-May-2027* tool, not a "you are in violation today" tool.
- **EU AI Act:** Art. 5 prohibitions + Art. 4 literacy in force 2 Feb 2025. GPAI (Arts.
  53–55) in force 2 Aug 2025. Art. 50 transparency from 2 Aug 2026. **High-risk (Annex
  III) deferred by the Digital Omnibus from 2 Aug 2026 to ~2 Dec 2027 — PROVISIONAL,
  pending formal adoption.**

## Part A — DPDP (India)

Primary source (Rules): DPDP Rules 2025 Gazette G.S.R. 846(E), 13 Nov 2025 —
`https://dpdpa.com/DPDP_Rules_2025_English_only.pdf` (fetched in full).

| Obligation | Act | Rule | Enforce | Verification | Summary |
|------------|-----|------|---------|--------------|---------|
| Notice | s.5 | Rule 3 | 2027-05-13 | primary | Standalone, plain-language, itemised data + purpose + how to withdraw/exercise rights/complain. |
| Consent | s.6 | Rule 3 | 2027-05-13 | secondary | Free, specific, informed, unambiguous; withdrawal as easy as giving. |
| Legitimate uses | s.7 | — | 2027-05-13 | secondary | Limited non-consent grounds (e.g. voluntary provision, state functions). |
| Security safeguards | s.8(5) | Rule 6(a)-(g) | 2027-05-13 | primary | Encryption/obfuscation/masking/tokens; access control; logging; backups; **1-yr log retention**; processor-contract clause; T&O measures. NOT "7 controls + MFA". |
| Breach intimation | s.8(6) | Rule 7 | 2027-05-13 | primary | Two tracks: affected principals "without delay"; Board "without delay" + **detailed report within 72h**. |
| Retention/erasure | s.8(7)-(8) | Rule 8 | 2027-05-13 | primary | Universal **1-yr** retention floor (8(3), all); **3-yr** inactivity erasure (8(1), Third-Schedule classes only); 48h pre-erasure notice. |
| Children | s.9 (bans) | Rule 10 (verification) | 2027-05-13 | primary | Verifiable parental consent; bans on tracking/behavioural monitoring/targeted ads. Fourth-Schedule exemptions (Rule 12). |
| SDF duties | s.10 | Rule 13 | 2027-05-13 | primary | DPIA + audit (12-monthly), algorithmic-risk diligence, data-localisation — **SDF-notified entities only**. |
| Contact / responder | s.9 (Act) | Rule 9 | 2027-05-13 | primary | Publish DPO (if SDF) or responder contact. Non-SDFs need a responder, **not a DPO**. |
| Rights (access) | s.11 | Rule 14 | 2027-05-13 | primary | Right to access summary of processing. |
| Rights (correction/erasure) | s.12 | Rule 14 | 2027-05-13 | primary | Right to correct/complete/update/erase. |
| Grievance | s.13 | Rule 14 | 2027-05-13 | primary | Publish means; respond within **90 days**. |
| Nomination | s.14 | Rule 14 | 2027-05-13 | secondary | Nominate another to exercise rights on death/incapacity. |
| Cross-border | s.16 | Rule 15 | 2027-05-13 | primary | Transfer permitted subject to Central-Govt restrictions (liberalised; no hard block). |

## Part B — EU AI Act (Regulation (EU) 2024/1689)

Primary source: EUR-Lex consolidated text — `https://eur-lex.europa.eu/eli/reg/2024/1689/oj`.
Corroborated via European Commission digital-strategy pages + 2026 Omnibus-deferral analyses.
**All EU rows are `secondary_source_only` pending verification against the consolidated
EUR-Lex text and the Omnibus final adoption.**

| Obligation | Article | Enforce | date_status | Summary |
|------------|---------|---------|-------------|---------|
| Prohibited practices | Art. 5 | 2025-02-02 | in_force | Social scoring, untargeted facial scraping, workplace/edu emotion recognition, etc. banned. |
| AI literacy | Art. 4 | 2025-02-02 | in_force | Providers/deployers ensure staff AI literacy. |
| GPAI model obligations | Arts. 53–55 | 2025-08-02 | in_force | Technical docs, downstream info, copyright policy, training-content summary; systemic-risk extras. |
| Transparency (limited risk) | Art. 50 | 2026-08-02 | phased_confirmed | Disclose chatbots; label deepfake/synthetic content. |
| Risk management | Art. 9 | ~2027-12-02 | provisional | High-risk provider risk-management system. |
| Data governance | Art. 10 | ~2027-12-02 | provisional | High-risk training/validation/test data governance. |
| Technical documentation | Art. 11 + Annex IV | ~2027-12-02 | provisional | High-risk technical documentation. |
| Record-keeping / logging | Arts. 12, 19–20 | ~2027-12-02 | provisional | Automatic logs + record-keeping. |
| Transparency to deployers | Art. 13 | ~2027-12-02 | provisional | Instructions for use to deployers. |
| Human oversight | Art. 14 | ~2027-12-02 | provisional | Designed-in human oversight. |
| Accuracy/robustness/cyber | Art. 15 | ~2027-12-02 | provisional | Accuracy, robustness, cybersecurity. |
| Quality management | Arts. 16–17 | ~2027-12-02 | provisional | Provider QMS. |

> ⚠️ EU high-risk dates are **provisional** (Digital Omnibus, political agreement
> 7 May 2026, pending formal adoption). Re-verify on every review; this is the single
> biggest accuracy risk in the EU pack.
