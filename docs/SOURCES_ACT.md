# SOURCES_ACT.md — DPDP Act 2023 (Act 22 of 2023) companion

> **DRAFT — pending verification against primary Act text.** Status: 2026-06-26.
>
> The DPDP **Rules 2025** are grounded in the actual Gazette text (see
> [`LEGAL_REFERENCE_DPDP_EUAI.md`](LEGAL_REFERENCE_DPDP_EUAI.md), fetched in full). The
> DPDP **Act 2023** sections below are currently grounded via the Rules + reputable
> secondary analysis (EY, Lexology, Ikigai, Securiti, PIB), **NOT yet line-by-line against
> the primary Act Gazette text.** Every Act-cited rule is therefore flagged
> `secondary_source_only` or pending in [`../LEGAL_REVIEW_NEEDED.md`](../LEGAL_REVIEW_NEEDED.md).
>
> **Required next step (grounding gate):** fetch and verify the primary Act text
> (India Code / MeitY Gazette) for ss.4–17 + the Schedule, then upgrade verification
> states. This is an engineering reference, **not legal advice.**

## Why this file exists
Many substantive DPDP obligations live in the **Act**, with the Rules only operationalising
them. Citing a Rule number for an Act-level obligation is incorrect. CompliSense rules use
**dual-layer citations** (`act_citation` + `rule_citation`); this file is the Act-side
source-of-truth they point at.

## Sections (to verify against primary text)

| Section | Subject | Used by rule(s) | Verification |
|---------|---------|-----------------|--------------|
| s.4 | Grounds for processing (consent or legitimate use) | (basis for s.5–s.7 rules) | pending |
| s.5 | **Notice** | DPDP-SEC5-NOTICE-001 | secondary |
| s.6 | **Consent** (free/specific/informed/unambiguous; withdrawal) | DPDP-SEC6-CONSENT-001 | secondary |
| s.7 | **Certain legitimate uses** | DPDP-SEC7-LEGITIMATE-USE-001 | secondary |
| s.8 | **Data Fiduciary duties** — accuracy, security (8(5)), breach (8(6)), retention (8(7)-(8)), processor responsibility (8(2)) | SEC8-* rules | secondary→primary via Rules 6/7/8 |
| s.9 | **Children & persons with disability** — bans on tracking/behavioural monitoring/targeted ads | DPDP-SEC9-CHILDREN-001 | secondary |
| s.10 | **Significant Data Fiduciary** additional obligations (DPO-in-India, audit, DPIA) | DPDP-SEC10-SDF-001 | secondary |
| s.11 | Right to access information | DPDP-SEC11-ACCESS-001 | secondary |
| s.12 | Right to correction & erasure | DPDP-SEC12-CORRECTION-001 | secondary |
| s.13 | Right of grievance redressal | DPDP-SEC13-GRIEVANCE-001 | secondary |
| s.14 | Right to nominate | (extended rights) | pending |
| s.15 | Duties of Data Principal | — | pending |
| s.16 | Processing/transfer outside India | DPDP-SEC16-TRANSFER-001 | secondary |
| s.17 | Exemptions | — | pending |
| Schedule | **Penalties** (₹250cr security; ₹200cr breach; ₹200cr children; ₹150cr SDF; ₹10k principal duties) | (severity weighting; verify exact figures) | pending |

## Caveat on penalties
Penalty magnitudes (crore-level) are corroborated by multiple secondary sources but the
exact splits vary between analyses. Treat figures as "verify against the Act Schedule
before publishing." Do not surface a penalty figure as certain in user-facing output until
verified.
