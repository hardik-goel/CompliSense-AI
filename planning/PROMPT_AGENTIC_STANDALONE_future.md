# CLAUDE CODE — STANDALONE PROMPT: Planning & Building the Agentic Stage (use in a FUTURE session)

Save this on its own. Open it when you're ready to start the agentic stage of
CompliSense — likely months from now, after the core product has real users. It is
SELF-CONTAINED: it re-establishes context from scratch, because a future Claude Code
session will not remember the earlier planning. Do not assume any of that history is
in context.

---

## STEP 0 — Re-orient before anything (do this first, every time)
You are working in my proprietary repo **CompliSense-AI**: a FastAPI + MongoDB hosted
compliance platform with a local agent and regulatory rulepacks (India DPDP Act/Rules
2025, EU AI Act). It scans a company's data practices and produces readiness findings +
remediation. There is a separate open-source repo (`complykit`) that is the free tier;
THIS repo is the paid product and owns everything stateful, discovery-based, current,
team-oriented, and AI-assisted.

Before proposing or building anything, READ these files in the repo and confirm back to
me what you found (if any are missing, say so and stop):
- `docs/LEGAL_REFERENCE_DPDP_EUAI.md` and `docs/SOURCES_ACT.md` — legal source of truth.
- `LEGAL_REVIEW_NEEDED.md` — review gate status.
- `docs/DATA_HANDLING.md` — current data-flow + the "without storing your data" stance.
- `AUDIT_REPORT.md` if present — last known state of the build.
- The rulepacks, the findings/manifest data model, the connector interface, and the
  MCP server.
Then give me a 1-page summary: what's built, what's stable, what the current LLM
features are (expected: MCP server, LLM remediation copilot, human-in-the-loop
rule-watcher, LLM-assisted manifest building), and anything that looks unfinished.
STOP and wait for me after this summary.

## STEP 1 — Confirm we should be doing agentic work at all
The agentic stage is deliberately gated. Before planning a feature, confirm with me
that BOTH are true (ask me directly; do not assume):
1. The feature's preconditions are built, tested, and stable.
2. A real design partner / user has explicitly asked for this capability, OR usage data
   shows the need. We do NOT build agentic features speculatively.
If either is not met, tell me so and recommend we wait. Be willing to say "not yet."

## STEP 2 — The candidate agentic features (pick ONE with me, in this order of safety)
Do not build more than one at a time. Help me choose based on what my users actually
asked for.

**9.1 — Conversational compliance agent (lowest risk; usually first).**
Reads and explains, never acts. Answers STRICTLY from the user's own findings, manifest,
and the cited rule reference. "Why am I failing the breach rule?" → explains using their
data + the real citation. Grounded only in their state + cited rules; if it can't
ground an answer, it says so. No legal advice; readiness framing.
Preconditions: real findings exist; rule reference stable; MCP server live.

**9.2 — Agentic evidence-collection loop (highest value; needs connectors first).**
A planner that, given a target regulation + connected stack, works out what evidence is
still needed, gathers it across read-only connectors, notices gaps, and asks the user
only for what it genuinely can't resolve. Turns "scanner" into "runs a readiness
program."
Preconditions: Tier-1 connectors (AWS + ≥1 more) working and trusted; Tier-2 inference
proven; manifest auto-population reliable; human-confirm step solid.
BLOCKER: resolve the "without storing your data" decision first (see Step 4).

**9.3 — Posture-drift monitoring (needs tenure + connectors).**
Monitors the CUSTOMER's own changing surface (new privacy policy, new subprocessor in
billing, new data-collecting SDK in a repo) and flags drift from their declared
manifest. Distinct from the rule-watcher, which monitors the LAW. Flags for human
review; never silently re-scores.
Preconditions: connectors + a baseline manifest stable long enough to drift from;
customers with enough tenure to have drift.

## STEP 3 — Non-negotiable guardrails for ANY agentic feature
Inherit all of these from the existing product; do not relax them:
- **Human-in-the-loop** for anything that asserts compliance or changes a rule. The
  agent assists; a human decides.
- **Read-only** by default. Every inferred fact is "suggested, user confirms."
- **Grounded, not generative, on law.** Agents answer from the cited rule reference +
  the user's state, never from open-ended legal generation.
- **Readiness, not violation** framing everywhere; "not legal advice" disclaimer
  intact; per-finding verification signal preserved.
- **Full audit trail** of what the agent did, read, inferred, and why.

## STEP 4 — Hard limits (do NOT build these without a separate decision + legal sign-off)
- **No auto-remediation that mutates the customer's systems** (editing cookie banners,
  IAM policies, configs). Drafting documents is fine; changing their environment is not
  part of this stage.
- **No autonomous regulator submission** (e.g. filing a breach report). Any submission
  to a regulator on a customer's behalf requires a human signature. Full stop.
- **Resolve "without storing your data" BEFORE 9.2.** An agent that gathers and reasons
  over customer data cannot also store nothing. Decide and document whether the tagline
  survives, narrows (e.g. "we don't train on or sell your data"), or the agentic tier
  becomes explicit opt-in with clear data-handling terms. Do not break the promise
  feature by feature.

## STEP 5 — Build discipline (once I pick a feature and approve)
- Confirm: "This is what we're going to build: <feature> — <1-paragraph plan>. Should I
  go ahead?" and WAIT.
- Build only that feature.
- "<feature> is done now" + summary + exact test steps, then STOP. I test, push to a
  feature branch, merge to dev, and start the next.
- Never bundle features. Never start the next without my go-ahead.
- For anything touching legal content, re-check against `docs/LEGAL_REFERENCE_*` and add
  anything unverifiable to `LEGAL_REVIEW_NEEDED.md` rather than guessing.

## RULE OF ENGAGEMENT
Start with Step 0 (read + summarize + stop). Do not propose a build until Steps 1–2 are
done with me. Be willing to tell me it's too early. One feature at a time, fully gated.
