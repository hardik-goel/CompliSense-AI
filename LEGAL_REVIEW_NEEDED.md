# LEGAL_REVIEW_NEEDED.md — living professional-review checklist

> **Status: Rule content pending professional legal review as of 2026-06-26.**
> CompliSense rulepacks are compliance-readiness engineering artefacts, NOT legal
> advice and NOT a legal determination of compliance. Every rule below must be
> reviewed by (a) a qualified Indian data-protection practitioner (DPDP) and
> (b) an EU AI Act specialist before any unqualified public compliance claim.
>
> This file is generated from `rulepacks/*.yaml`. Regenerate after pack changes.
> When a reviewer signs off a pack, set its `legal_review_status: reviewed`,
> `reviewer`, and `reviewed_on` in the pack header and tick the rows here.

## Priority flags
- ⚠️ **secondary_source_only** / **interpretation_uncertain** = NOT yet verified
  against primary statute text. Highest review priority.
- 🕒 **provisional_pending_amendment** = enforcement date may move (EU Digital
  Omnibus). Re-verify date on each review.

## dpdp_india_core_v1.yaml  (`legal_review_status: pending`)

| ✓ | Rule ID | Act citation | Rule citation | Status | Enforce | date_status | Verification |
|---|---------|--------------|---------------|--------|---------|-------------|--------------|
| [ ] | DPDP-SEC5-NOTICE-001 | DPDP Act 2023, s.5 (Notice) | DPDP Rules 2025, Rule 3 (Notice given by Data Fiduciary) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC8-OBLIGATIONS-001 | DPDP Act 2023, s.8(5) (reasonable security safeguards) | DPDP Rules 2025, Rule 6 (safeguards (a)-(g): encryption/obfuscation/masking/tokens; access control; logging; backups; 1-yr log retention; processor-contract clause; T&O measures) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC8-OBLIGATIONS-002 | DPDP Act 2023, s.8(6) (breach intimation) | DPDP Rules 2025, Rule 7 (two tracks: affected principals 'without delay'; Board 'without delay' + detailed report within 72h) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC9-CHILDREN-001 | DPDP Act 2023, s.9 (substantive bans: no tracking / behavioural monitoring / targeted advertising to children) | DPDP Rules 2025, Rule 10 (verifiable parental-consent mechanics) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC10-SDF-001 | DPDP Act 2023, s.10 (additional obligations of Significant Data Fiduciaries) | DPDP Rules 2025, Rule 13 (12-monthly DPIA + audit, algorithmic-risk diligence, data-localisation) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC13-GRIEVANCE-001 | DPDP Act 2023, s.13 (right to grievance redressal; rights ss.11-14) | DPDP Rules 2025, Rule 14 (publish request means + respond within 90 days) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC6-CONSENT-001 | DPDP Act 2023, s.6 (Consent) | DPDP Rules 2025, Rule 3 (notice enabling specific, informed consent) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | secondary_source_only ⚠️ |

## dpdp_india_extended_v1.yaml  (`legal_review_status: pending`)

| ✓ | Rule ID | Act citation | Rule citation | Status | Enforce | date_status | Verification |
|---|---------|--------------|---------------|--------|---------|-------------|--------------|
| [ ] | DPDP-SEC5-NOTICE-001 | DPDP Act 2023, s.5 (Notice) | DPDP Rules 2025, Rule 3 (Notice given by Data Fiduciary) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC8-OBLIGATIONS-001 | DPDP Act 2023, s.8(5) (reasonable security safeguards) | DPDP Rules 2025, Rule 6 (safeguards (a)-(g)) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC8-OBLIGATIONS-002 | DPDP Act 2023, s.8(6) (breach intimation) | DPDP Rules 2025, Rule 7 (two tracks; Board detailed report within 72h) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC8-OBLIGATIONS-003 | DPDP Act 2023, s.8(7)-(8) (retention limitation & erasure) | DPDP Rules 2025, Rule 8 (8(3) universal 1-yr retention floor; 8(1) 3-yr class-based erasure) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC9-CHILDREN-001 | DPDP Act 2023, s.9 (substantive bans on tracking/behavioural monitoring/targeted ads to children) | DPDP Rules 2025, Rule 10 (verifiable parental-consent mechanics) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC10-SDF-001 | DPDP Act 2023, s.10 (additional SDF obligations) | DPDP Rules 2025, Rule 13 (DPIA + audit, algorithmic-risk diligence, localisation) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC11-ACCESS-001 | DPDP Act 2023, s.11 (right to access information about personal data) | DPDP Rules 2025, Rule 14 (publish request means + identifier) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC12-CORRECTION-001 | DPDP Act 2023, s.12 (right to correction and erasure) | DPDP Rules 2025, Rule 14 (rights exercise mechanics) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC13-GRIEVANCE-001 | DPDP Act 2023, s.13 (right to grievance redressal) | DPDP Rules 2025, Rule 14 (respond within 90 days) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC16-TRANSFER-001 | DPDP Act 2023, s.16 (processing/transfer of personal data outside India) | DPDP Rules 2025, Rule 15 (transfer permitted subject to Central Govt restrictions) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC8-PROCESSOR-001 | DPDP Act 2023, s.8(2) (Data Fiduciary responsible for processing by a Data Processor under contract) | DPDP Rules 2025, Rule 6(f) (processor-contract safeguard clause) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | primary_source_verified  |
| [ ] | DPDP-SEC6-CONSENT-001 | DPDP Act 2023, s.6 (Consent) | DPDP Rules 2025, Rule 3 (notice enabling specific, informed consent) | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | secondary_source_only ⚠️ |
| [ ] | DPDP-SEC7-LEGITIMATE-USE-001 | DPDP Act 2023, s.7 (Certain legitimate uses) | — | phased_not_yet_in_force | 2027-05-13 | phased_confirmed | secondary_source_only ⚠️ |

## euai_core_v1.yaml  (`legal_review_status: pending`)

| ✓ | Rule ID | Act citation | Rule citation | Status | Enforce | date_status | Verification |
|---|---------|--------------|---------------|--------|---------|-------------|--------------|
| [ ] | EUAI-ART9-RISK-MGMT-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 9 (risk management system) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART10-DATA-GOV-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 10 (data and data governance) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART11-TECHDOC-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 11 + Annex IV (technical documentation) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART11-TECHDOC-002 | Regulation (EU) 2024/1689 (EU AI Act), Art. 11 + Annex IV (technical documentation) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART13-TRANSPARENCY-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 13 (transparency & provision of information to deployers) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART14-HUMAN-OVERSIGHT-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 14 (human oversight) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART15-ACCURACY-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 15 (accuracy, robustness and cybersecurity) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART16-QUALITY-MGMT-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 16-17 (provider obligations / quality management system) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART18-DATA-GOV-002 | Regulation (EU) 2024/1689 (EU AI Act), Art. 18 (documentation keeping) / Art. 10 (data governance) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART20-RECORD-KEEPING-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 12 + Art. 19-20 (record-keeping / automatically generated logs) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |

## euai_extended_v1.yaml  (`legal_review_status: pending`)

| ✓ | Rule ID | Act citation | Rule citation | Status | Enforce | date_status | Verification |
|---|---------|--------------|---------------|--------|---------|-------------|--------------|
| [ ] | EUAI-ART9-RISK-MGMT-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 9 (risk management system) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART10-DATA-GOV-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 10 (data and data governance) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART11-TECHDOC-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 11 + Annex IV (technical documentation) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART11-TECHDOC-002 | Regulation (EU) 2024/1689 (EU AI Act), Art. 11 + Annex IV (technical documentation) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART13-TRANSPARENCY-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 13 (transparency & provision of information to deployers) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART14-HUMAN-OVERSIGHT-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 14 (human oversight) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART15-ACCURACY-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 15 (accuracy, robustness and cybersecurity) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART16-QUALITY-MGMT-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 16-17 (provider obligations / quality management system) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART18-DATA-GOV-002 | Regulation (EU) 2024/1689 (EU AI Act), Art. 18 (documentation keeping) / Art. 10 (data governance) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART20-RECORD-KEEPING-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 12 + Art. 19-20 (record-keeping / automatically generated logs) | — | phased_not_yet_in_force | 2027-12-02 | provisional_pending_amendment | secondary_source_only ⚠️ 🕒 |
| [ ] | EUAI-ART5-PROHIBITED-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 5 (prohibited AI practices) | — | in_force | 2025-02-02 | in_force | secondary_source_only ⚠️ |
| [ ] | EUAI-ART4-LITERACY-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 4 (AI literacy) | — | in_force | 2025-02-02 | in_force | secondary_source_only ⚠️ |
| [ ] | EUAI-ART50-TRANSPARENCY-001 | Regulation (EU) 2024/1689 (EU AI Act), Art. 50 (transparency obligations for certain AI systems) | — | phased_not_yet_in_force | 2026-08-02 | phased_confirmed | secondary_source_only ⚠️ |
| [ ] | EUAI-ART53-GPAI-001 | Regulation (EU) 2024/1689 (EU AI Act), Arts. 53-55 (general-purpose AI model obligations) | — | in_force | 2025-08-02 | in_force | secondary_source_only ⚠️ |


---

## Post-audit additions (2026-06-28) — pending counsel

- **EU AI Act readiness scoring is now enabled (role-gated)** for project + MCP scoring. EU rules
  remain `secondary_source_only` and are **not yet primary-verified**. EU *posture* predicates are
  not implemented, so applicable EU rules surface as **NEEDS_REVIEW** ("prepare-by") gaps rather
  than pass/fail — honest, but a counsel-reviewed EU posture model is still needed.
- **Open-source exemption mechanism added** (`applicability.open_source_exempt` + manifest
  `is_open_source`). WHICH EU rules actually carry the open-source carve-out is **not yet mapped**
  to the packs — counsel must decide before any rule sets `open_source_exempt: true`.
- **New rule `DPDP-SEC8-RETENTION-CLASS-001`** (Rule 8(1) Third-Schedule 3-year inactivity erasure,
  gated to `third_schedule_class_only`). Cited to DPDP Rules 2025 Rule 8(1) + Third Schedule;
  verify the erasure-period framing against primary text.
