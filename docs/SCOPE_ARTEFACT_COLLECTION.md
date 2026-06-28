# Scope — Artefact Collection (pull existing documents from sources)

> Status: **6.1 BUILT** (agent-side local-folder collector + LLM classifier). Decisions taken:
> agent-side/local · local-folder first · LLM classifier now (deterministic fallback). Remaining
> phases 6.2–6.6 (S3/GCS/Azure/GitHub/Drive + hosted config UI) still open — see §6.

## 1. What it is (vs. what exists today)
Today's Tier-1 connectors are **read-only metadata**: they read cloud *configuration* (encryption
on? logging on? MFA?) — never file contents — and the artefact generator *drafts* new documents.

This capability is different: **find and collect the customer's EXISTING compliance documents**
from where they actually live (object storage, repos, drives), classify which ones are
artefacts, and put them into the scan **input folder** so the engine evaluates real evidence.

## 2. The privacy line (the load-bearing decision)
Reading document *contents* can expose personal data and breaks the current "we read metadata,
not your data" stance. To keep the **"without storing your data"** promise, collection must
**run on the client machine (agent-side), not on our servers**:

- The hosted app stores only the **collection config** (which sources, paths, filename patterns).
- The **downloaded agent** uses credentials supplied **locally** to read the source, copies
  matching files into the local input folder, scans them, and uploads only **findings**
  (metadata) — document contents never touch our backend.

This mirrors how the agent already works (local scan, no artefact upload) and is the only design
that doesn't break the privacy promise. Server-side collection is possible but would route
customer documents through our infrastructure — not recommended.

## 3. Sources (in build order)
1. **Local / on-prem folder** — already supported (agent scans a path). Add recursive
   classification so it labels which files are which artefact.
2. **Cloud object storage** — AWS **S3**, then GCS, Azure Blob. Read objects under a
   prefix; needs read-object permission (broader than today's describe-only policy — publish a
   new least-privilege *read* policy and warn the user).
3. **Code repos** — GitHub (read repo files: `/docs`, `/compliance`, model cards, configs).
4. **Doc stores (later, OAuth-heavy)** — Google Drive, SharePoint/OneDrive, Notion, Confluence.

## 4. How it works (agent-side collector)
1. **Declare sources** (hosted UI on the project): source type + path/prefix/repo + filename
   patterns (defaults provided). Stored as config only.
2. **Download agent** (config embedded). Agent prompts for / reads creds locally.
3. **Crawl** the source under the path, **filter by patterns + size cap**, **classify** each
   candidate (filename + extension + lightweight keyword sniff) → artefact type.
4. **Stage** matched files into `./collected_artefacts/`; print a manifest (file → artefact type
   → confidence). The user reviews/prunes.
5. **Scan** `./collected_artefacts/` → findings → upload findings only.

Classifier v1 = deterministic (filename/extension + keyword sniff). LLM/content classification is
an optional later upgrade (reads content → cost + privacy → keep local + opt-in).

## 5. What stays honest / the limits
- Only sources we build a collector for (S3/GCS/Azure/GitHub/Drive/local) — **not** arbitrary
  servers.
- Object-storage **read** permissions are broader than current describe-only — flagged to the user.
- Classification has false positives → the user reviews the staged set before scanning.
- Caps on file count/size; pattern-filter before download.

## 6. Phasing
- **6.1** ✅ Collector framework + classifier (agent-side) + recursive **local-folder** collector
  → stages + labels files. LLM classifier (Claude, local; deterministic fallback). Ships in the
  agent bundle (`agent/collectors/`, `python -m agent.collectors.collect`).
- **6.2** **S3** read collector + least-privilege read policy.
- **6.3** GCS + Azure Blob collectors.
- **6.4** GitHub repo-file collector.
- **6.5** Hosted "declare sources" config + bundle wiring + review UI.
- **6.6** (optional) Drive/SharePoint/Notion (OAuth) + content/LLM classification.

## 7. Decisions needed before build
1. **Collection locus** — agent-side/local (recommended; preserves the privacy promise) vs
   server-side (we read the docs).
2. **First source** — local-folder classifier first (fast, no creds) vs go straight to S3.
3. **Classifier** — deterministic v1 only, or include the LLM content classifier from the start
   (needs an Anthropic key + reads content).
