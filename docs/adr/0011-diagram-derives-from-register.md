# ADR 0011 — The data-flow diagram is derived from the ROPA, not built beside it

## Status

Accepted (2026-08-11). Implemented in `compliance/dfd.py` (`build_dfd(ropa)`).

## Context

A DPDPA gap assessment ships two artefacts that describe the same reality: the **Record of
Processing Activities** (what is processed, why, where, how long, by whom) and the
**data-flow diagram** (how it moves). In consulting practice they are produced separately —
a spreadsheet and a PowerPoint — by different people at different times.

They therefore disagree. The register lists a processor the diagram omits; the diagram shows
a store the register never mentions. When a reviewer notices, the credibility of both drops to
zero, because there is no way to tell which one is wrong.

Building them as two independent generators would reproduce that defect in software, where it
would be *permanent* rather than merely likely.

## Decision

The diagram is a **pure projection of the register**. `build_dfd()` takes the ROPA as its only
argument. There is no second data path.

- Nodes come from ROPA rows: data principals → processing activity → store → processor.
- Edge labels are the row's categories. Cross-border edges and the India trust boundary come
  from the row's `cross_border` flag.
- Domain badges come from the same `compliance/domains.py` functions the register uses.
- Even the applicability facts the overlay needs (SDF status, children's data) are recovered
  from the register's own `controller` block — deliberately **not** passed as a second
  parameter, because a second parameter is a second source of truth and therefore a way for
  the two artefacts to drift apart.
- Only *named* processors become nodes. "Declared but not named" is a string in the register,
  and inventing a node for it would fabricate a data flow — the failure
  [[0007-deterministic-records]] exists to prevent.

Rendering is a single self-contained `<svg>`: no scripts, no external references, no fonts to
fetch, escaped labels, and a `prefers-color-scheme` block so it reads in light and dark. It can
be inlined into the HTML report, the evidence pack or an email without a network request.

## Consequences

- **Positive.** The picture and the table cannot disagree. That is a structural guarantee, not
  a process promise.
- **Positive.** One set of facts to maintain. Improving the register improves the diagram.
- **Positive.** `UNKNOWN` propagates honestly — an undeclared purpose shows as
  "(purpose not declared)" on the diagram instead of being quietly prettified.
- **Negative.** The diagram cannot express anything the register does not model. Real DFDs
  carry admin/config layers, decision points and API boundaries — visible in the deliverables
  we are matching, absent here. Adding them means extending the *register* first, which is the
  correct order and the slower one.
- **Negative.** Layout is a fixed four-column flow. It will not suit every topology, and a
  general graph layout engine is a much larger undertaking.

## Alternatives considered

- **Independent diagram builder with its own inputs.** Rejected: reintroduces the drift this
  ADR exists to eliminate.
- **Let the client hand-edit the diagram.** Rejected for now: an edited diagram is no longer
  derived, so the guarantee is void. If clients need this, the edit belongs in the register.
- **Render via Graphviz/Mermaid.** Rejected: adds a runtime dependency to a module that must
  stay pure and shippable inside the packaged agent ([[0006-local-agent-trust-model]]), and
  hands away control of the trust boundary and badge rendering.

## Related

[[0007-deterministic-records]] · [[0010-eight-domain-lens]] · [[0004-unknown-is-a-gap]]
