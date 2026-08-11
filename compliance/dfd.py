"""Data-flow diagram (DFD) rendered from the ROPA register — pure, no dependencies.

The ROPA answers *what* is processed; the DFD shows *where it moves*. Both are built from
the same facts (``compliance/ropa.py``), so the diagram can never disagree with the table.

Shape: data principals -> processing activity -> data store -> processor, laid out in four
columns, with a dashed **India trust boundary** drawn around any store that sits outside
India (DPDP s.16 / Rule 15).

Output is a single self-contained ``<svg>`` string: no scripts, no external references, no
fonts to fetch — safe to inline in the HTML report, the evidence pack, or an email.
"""

from __future__ import annotations

from typing import Any, Dict, List

from compliance.domains import DOMAINS, domains_for_node
from compliance.ropa import UNKNOWN

NO_PRINCIPALS = "Data principals (not declared)"

# Layout constants (px). Columns sit 305px apart with 170px boxes, leaving 135px of clear
# space for an edge label — that gap, not the node width, is what drives the canvas width.
_COL_X = {"principal": 30, "activity": 335, "store": 640, "processor": 945}
_NODE_W, _NODE_H, _V_GAP = 170, 56, 82
_TOP, _BOTTOM_PAD, _CANVAS_W = 60, 40, 1145
# Footnote + the eight-domain legend rendered under the diagram (2 columns x 4 rows).
_LEGEND_H, _LEGEND_ROW_H, _LEGEND_COL_W = 148, 19, 560
_BADGE_R = 8


def _uniq_append(items: List[Dict[str, Any]], node: Dict[str, Any]) -> Dict[str, Any]:
    for existing in items:
        if existing["id"] == node["id"]:
            existing["outside_india"] = existing.get("outside_india") or node.get("outside_india")
            return existing
    items.append(node)
    return node


def _answers_from_controller(ropa: Dict[str, Any]) -> Dict[str, Any]:
    """Recover the applicability facts the domain overlay needs, from the register itself.

    Deliberately NOT a second parameter: the diagram must be derivable from the register
    alone, or the picture and the table could drift apart.
    """
    c = ropa.get("controller") or {}
    return {
        "notified_as_sdf": c.get("is_significant_data_fiduciary", False),
        "processes_children_data": c.get("processes_children_data", False),
    }


def build_dfd(ropa: Dict[str, Any]) -> Dict[str, Any]:
    """Turn a ROPA register into a node/edge graph. Pure."""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    answers = _answers_from_controller(ropa)

    def _edge(source: str, target: str, label: str, cross_border: bool = False) -> None:
        for e in edges:
            if e["source"] == source and e["target"] == target:
                e["cross_border"] = e["cross_border"] or cross_border
                return
        edges.append({"source": source, "target": target, "label": label,
                      "cross_border": cross_border})

    pii_nodes: set = set()

    for row in ropa.get("rows", []) or []:
        categories = row.get("categories") or []
        cat_label = ", ".join(categories) if categories else UNKNOWN
        touches_pii = bool(categories)

        purpose = row.get("purpose")
        act_label = purpose if purpose and purpose != UNKNOWN else \
            f"{row['activity_id']} (purpose not declared)"
        act = _uniq_append(nodes, {"id": f"a:{row['activity_id']}", "kind": "activity",
                                   "label": act_label, "outside_india": False})
        if touches_pii:
            pii_nodes.add(act["id"])

        principals = row.get("data_principals")
        labels = principals if isinstance(principals, list) and principals else [NO_PRINCIPALS]
        for name in labels:
            p = _uniq_append(nodes, {"id": f"p:{name}", "kind": "principal",
                                     "label": name, "outside_india": False})
            if touches_pii:
                pii_nodes.add(p["id"])
            _edge(p["id"], act["id"], cat_label)

        store_label = row.get("store")
        if store_label and store_label != UNKNOWN:
            store = _uniq_append(nodes, {"id": f"s:{store_label}", "kind": "store",
                                         "label": store_label,
                                         "outside_india": bool(row.get("cross_border")),
                                         "provider": row.get("provider"), "region": row.get("region")})
            if touches_pii:
                pii_nodes.add(store["id"])
            _edge(act["id"], store["id"], cat_label, bool(row.get("cross_border")))

            # Only *named* processors become nodes. "Declared but not named" is a string,
            # and inventing a node for it would fabricate a data flow.
            processors = row.get("processors")
            if isinstance(processors, list):
                for name in processors:
                    proc = _uniq_append(nodes, {"id": f"x:{name}", "kind": "processor",
                                                "label": name, "outside_india": False})
                    if touches_pii:
                        pii_nodes.add(proc["id"])
                    _edge(store["id"], proc["id"], cat_label)

    # Overlay: which of the eight DPDPA domains a reviewer would pin to each stage, and
    # which stages actually touch personal data.
    for node in nodes:
        node["domains"] = domains_for_node(node["kind"], node, answers)
        node["has_pii"] = node["id"] in pii_nodes

    return {
        "nodes": nodes,
        "edges": edges,
        "has_cross_border": bool(ropa.get("has_cross_border")),
        "has_pii_stages": bool(pii_nodes),
        "legend": {"principal": "Data principal (external entity)", "activity": "Processing activity",
                   "store": "Data store", "processor": "Processor / third party"},
        "domain_legend": [{"number": d["number"], "domain_id": d["domain_id"],
                           "title": d["title"], "act_citation": d["act_citation"]}
                          for d in DOMAINS],
        "applicable_domains": sorted({n for node in nodes for n in node["domains"]}),
    }


# --- SVG rendering -------------------------------------------------------------------

def _esc(text: Any) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def _clip(text: str, limit: int = 26) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


_STYLE = """
<style>
  .bg { fill: #ffffff; }
  .box { fill: #f4f6fa; stroke: #93a2b8; stroke-width: 1.2; }
  .box.principal { fill: #eef4ff; stroke: #6b8ec9; }
  .box.activity  { fill: #eefaf3; stroke: #58a980; }
  .box.store     { fill: #fff6e8; stroke: #cc9a4e; }
  .box.processor { fill: #f6eef8; stroke: #a173b5; }
  .box.outside   { stroke: #c0392b; stroke-width: 2.2; stroke-dasharray: 5 3; }
  .lbl  { fill: #1c2733; font: 600 12px system-ui, -apple-system, 'Segoe UI', sans-serif; }
  .sub  { fill: #566577; font: 400 10px system-ui, -apple-system, 'Segoe UI', sans-serif; }
  .edge { stroke: #7c8b9e; stroke-width: 1.3; fill: none; }
  .edge.cross { stroke: #c0392b; stroke-dasharray: 5 3; }
  .elbl { fill: #566577; font: 400 9.5px system-ui, -apple-system, 'Segoe UI', sans-serif; }
  .boundary { fill: none; stroke: #c0392b; stroke-width: 1.4; stroke-dasharray: 7 4; }
  .boundary-lbl { fill: #c0392b; font: 600 11px system-ui, -apple-system, 'Segoe UI', sans-serif; }
  .title { fill: #1c2733; font: 700 14px system-ui, -apple-system, 'Segoe UI', sans-serif; }
  .arrow { fill: #7c8b9e; }
  .arrow-cross { fill: #c0392b; }
  .badge { fill: #2c3e6b; }
  .badge.cross { fill: #c0392b; }
  .badge.muted { fill: #b3bdca; }
  .badge-num { fill: #ffffff; font: 700 10px system-ui, -apple-system, sans-serif; }
  .foot { fill: #566577; font: 400 11px system-ui, -apple-system, 'Segoe UI', sans-serif; }
  .legend-title { fill: #1c2733; font: 700 12px system-ui, -apple-system, 'Segoe UI', sans-serif; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #12161c; }
    .box { fill: #1c232c; stroke: #46586e; }
    .box.principal { fill: #182234; stroke: #5c7fb8; }
    .box.activity  { fill: #16261f; stroke: #4a9271; }
    .box.store     { fill: #2a2113; stroke: #b8873f; }
    .box.processor { fill: #251a2b; stroke: #8f63a1; }
    .lbl, .title { fill: #e6ecf3; }
    .sub, .elbl, .foot { fill: #97a5b6; }
    .legend-title { fill: #e6ecf3; }
    .edge { stroke: #6b7c90; }
    .badge { fill: #6f8fd6; }
    .badge.muted { fill: #46566b; }
    .badge-num { fill: #0f141a; }
  }
</style>
"""


def dfd_to_svg(graph: Dict[str, Any], title: str = "Personal-data flow") -> str:
    """Render the graph as one self-contained SVG string. No scripts, no external refs."""
    by_kind: Dict[str, List[Dict[str, Any]]] = {k: [] for k in _COL_X}
    for node in graph.get("nodes", []) or []:
        by_kind.setdefault(node["kind"], []).append(node)

    tallest = max((len(v) for v in by_kind.values()), default=0)
    diagram_h = _TOP + max(tallest, 1) * _V_GAP + _BOTTOM_PAD
    height = diagram_h + _LEGEND_H
    pos: Dict[str, tuple] = {}

    for kind, column in by_kind.items():
        if kind not in _COL_X:
            continue
        span = len(column) * _V_GAP
        start = _TOP + max(0, (max(tallest, 1) * _V_GAP - span)) / 2
        for i, node in enumerate(column):
            pos[node["id"]] = (_COL_X[kind], start + i * _V_GAP)

    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_CANVAS_W} {int(height)}" '
        f'width="{_CANVAS_W}" height="{int(height)}" role="img" '
        f'aria-label="{_esc(title)} diagram">',
        _STYLE,
        '<defs>'
        '<marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow"/></marker>'
        '<marker id="arx" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-cross"/></marker>'
        '</defs>',
        f'<rect class="bg" x="0" y="0" width="{_CANVAS_W}" height="{int(height)}"/>',
        f'<text class="title" x="{_COL_X["principal"]}" y="30">{_esc(title)}</text>',
    ]

    # India trust boundary around the stores that sit outside India.
    outside = [n for n in by_kind.get("store", []) if n.get("outside_india")]
    if graph.get("has_cross_border") and outside:
        ys = [pos[n["id"]][1] for n in outside]
        x = _COL_X["store"] - 14
        # Top edge clears the node above (rows are _V_GAP apart, boxes are _NODE_H tall).
        y = min(ys) - 21
        h = (max(ys) + _NODE_H) - min(ys) + 21 + 22
        parts.append(f'<rect class="boundary" x="{x}" y="{y:.0f}" width="{_NODE_W + 28}" '
                     f'height="{h:.0f}" rx="8"/>')
        parts.append(f'<text class="boundary-lbl" x="{x + 8}" y="{y + h - 7:.0f}">'
                     f'Outside India — DPDP s.16 / Rule 15</text>')

    for edge in graph.get("edges", []) or []:
        if edge["source"] not in pos or edge["target"] not in pos:
            continue
        x1, y1 = pos[edge["source"]]
        x2, y2 = pos[edge["target"]]
        sx, sy = x1 + _NODE_W, y1 + _NODE_H / 2
        tx, ty = x2 - 9, y2 + _NODE_H / 2
        mx = (sx + tx) / 2
        cross = " cross" if edge.get("cross_border") else ""
        marker = "arx" if edge.get("cross_border") else "ar"
        parts.append(f'<path class="edge{cross}" d="M{sx:.0f},{sy:.0f} C{mx:.0f},{sy:.0f} '
                     f'{mx:.0f},{ty:.0f} {tx:.0f},{ty:.0f}" marker-end="url(#{marker})"/>')
        if edge.get("label"):
            # Clipped to fit the column gap so a label can never run under a node box.
            parts.append(f'<text class="elbl" x="{mx:.0f}" y="{(sy + ty) / 2 - 5:.0f}" '
                         f'text-anchor="middle">{_esc(_clip(edge["label"], 20))}</text>')

    for kind, column in by_kind.items():
        if kind not in _COL_X:
            continue
        for node in column:
            x, y = pos[node["id"]]
            outside_cls = " outside" if node.get("outside_india") else ""
            sub = _subtitle(node)
            parts.append(f'<rect class="box {kind}{outside_cls}" x="{x}" y="{y:.0f}" '
                         f'width="{_NODE_W}" height="{_NODE_H}" rx="7"/>')
            star = " *" if node.get("has_pii") else ""
            parts.append(f'<text class="lbl" x="{x + 12}" y="{y + 24:.0f}">'
                         f'{_esc(_clip(node["label"], 24))}{star}</text>')
            parts.append(f'<text class="sub" x="{x + 12}" y="{y + 41:.0f}">'
                         f'{_esc(_clip(sub, 30))}</text>')
            # Numbered DPDPA-domain badges, sitting in the gutter above the box.
            for i, number in enumerate(reversed(node.get("domains") or [])):
                cx = x + _NODE_W - 10 - i * (_BADGE_R * 2 + 3)
                cy = y - 11
                cls = "badge cross" if number == 8 else "badge"
                parts.append(f'<circle class="{cls}" cx="{cx:.0f}" cy="{cy:.0f}" r="{_BADGE_R}"/>')
                parts.append(f'<text class="badge-num" x="{cx:.0f}" y="{cy + 3.5:.0f}" '
                             f'text-anchor="middle">{number}</text>')

    ly = diagram_h - 12
    if graph.get("has_pii_stages"):
        parts.append(f'<text class="foot" x="{_COL_X["principal"]}" y="{ly:.0f}">'
                     f'* Stages where personal data is used</text>')
    ly += 26
    parts.append(f'<text class="legend-title" x="{_COL_X["principal"]}" y="{ly:.0f}">'
                 f'DPDPA domains</text>')
    applicable = set(graph.get("applicable_domains") or [])
    ly += 8
    for i, d in enumerate(graph.get("domain_legend") or []):
        col, row_i = divmod(i, 4)
        lx = _COL_X["principal"] + col * _LEGEND_COL_W
        ry = ly + (row_i + 1) * _LEGEND_ROW_H
        applies = d["number"] in applicable
        cls = "badge" if applies else "badge muted"
        parts.append(f'<circle class="{cls}" cx="{lx + _BADGE_R:.0f}" cy="{ry - 4:.0f}" '
                     f'r="{_BADGE_R}"/>')
        parts.append(f'<text class="badge-num" x="{lx + _BADGE_R:.0f}" y="{ry - 0.5:.0f}" '
                     f'text-anchor="middle">{d["number"]}</text>')
        suffix = "" if applies else "  — not applicable to your declared profile"
        parts.append(f'<text class="foot" x="{lx + _BADGE_R * 2 + 8:.0f}" y="{ry:.0f}">'
                     f'{_esc(d["title"])}{_esc(suffix)}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def _subtitle(node: Dict[str, Any]) -> str:
    if node["kind"] == "store":
        where = " / ".join(x for x in [node.get("provider"), node.get("region")] if x)
        if node.get("outside_india"):
            return f"{where or 'region unknown'} — outside India"
        return where or "region not declared"
    return {"principal": "external entity", "activity": "processing activity",
            "processor": "processor / third party"}.get(node["kind"], "")
