"""Canonical legal-clause short forms (Prompt 3, Task 6).

Single source of truth for the on-product legal language so the site, generated reports, the
score email, and the app footer all show identical wording. Full versions live in the site
`/terms` page. These are short forms to embed in-product — do NOT weaken them, and never
convert readiness language into a compliance claim.
"""

# "Not legal advice / no attorney-client relationship".
NOT_LEGAL_ADVICE = (
    "CompliSense-AI provides a regulatory-readiness assessment, not legal advice, and does "
    "not create any attorney-client relationship."
)

# Limitation of liability (short form; full terms govern).
LIMITATION_OF_LIABILITY = (
    "To the maximum extent permitted by law, CompliSense's liability is limited as set out in "
    "our Terms; we are not liable for any regulatory fine or penalty imposed on you."
)

# The pre-existing readiness disclaimer stays; these lines are ADDED alongside it.
READINESS_DISCLAIMER = (
    "This is a readiness self-assessment, not a determination of compliance."
)


def legal_footer_lines() -> list[str]:
    """The three lines to render together in report/email/app footers (order matters)."""
    return [READINESS_DISCLAIMER, NOT_LEGAL_ADVICE, LIMITATION_OF_LIABILITY]


def legal_footer_text(sep: str = " ") -> str:
    return sep.join(legal_footer_lines())


def legal_footer_html() -> str:
    """Small HTML block for email/report footers."""
    items = "".join(f"<div>{line}</div>" for line in legal_footer_lines())
    return f'<div style="font-size:11px;color:#6b7280;line-height:1.5;margin-top:16px">{items}</div>'
