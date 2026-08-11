"""Data-flow diagram built from the ROPA register."""

from compliance.dataflow import DataSource, infer_data_flows
from compliance.dfd import build_dfd, dfd_to_svg
from compliance.ropa import ProcessingActivity, build_ropa

FLOW = infer_data_flows([
    DataSource(name="users_db", field_names=["email", "phone"], provider="aws", region="ap-south-1"),
    DataSource(name="analytics", field_names=["email", "latitude"], provider="gcp", region="us-central1"),
])
ANSWERS = {"entity_type": "startup", "sector": "saas", "offers_in_india": True,
           "consent_mechanism": "explicit_optin", "retention_defined": True}


def _declared_ropa():
    return build_ropa(ANSWERS, flow_report=FLOW, activities=[ProcessingActivity(
        activity_id="signup", purpose="Account creation", categories=["email"],
        data_principals=["customers"], stores=["users_db"], retention="24 months",
        processors=["AWS"])])


# --- graph ----------------------------------------------------------------------------

def test_every_ropa_store_becomes_a_store_node():
    graph = build_dfd(build_ropa(ANSWERS, flow_report=FLOW))
    stores = {n["label"] for n in graph["nodes"] if n["kind"] == "store"}
    assert stores == {"users_db", "analytics"}


def test_declared_data_principals_become_external_entity_nodes():
    graph = build_dfd(_declared_ropa())
    principals = {n["label"] for n in graph["nodes"] if n["kind"] == "principal"}
    assert principals == {"customers"}


def test_undeclared_principals_collapse_to_one_honest_placeholder_node():
    graph = build_dfd(build_ropa(ANSWERS, flow_report=FLOW))
    principals = [n for n in graph["nodes"] if n["kind"] == "principal"]
    assert len(principals) == 1
    assert "not declared" in principals[0]["label"].lower()


def test_named_processors_become_processor_nodes_fed_by_the_store():
    graph = build_dfd(_declared_ropa())
    proc = next(n for n in graph["nodes"] if n["kind"] == "processor")
    assert proc["label"] == "AWS"
    assert any(e["target"] == proc["id"] for e in graph["edges"])


def test_declared_but_unnamed_processors_do_not_invent_a_node():
    graph = build_dfd(build_ropa({**ANSWERS, "processors_listed": True}, flow_report=FLOW))
    assert [n for n in graph["nodes"] if n["kind"] == "processor"] == []


def test_edge_from_activity_to_store_is_labelled_with_the_categories():
    graph = build_dfd(_declared_ropa())
    store = next(n for n in graph["nodes"] if n["kind"] == "store")
    edge = next(e for e in graph["edges"] if e["target"] == store["id"])
    assert "email" in edge["label"]


def test_store_outside_india_is_marked_and_raises_the_graph_flag():
    graph = build_dfd(build_ropa(ANSWERS, flow_report=FLOW))
    analytics = next(n for n in graph["nodes"] if n["label"] == "analytics")
    users = next(n for n in graph["nodes"] if n["label"] == "users_db")
    assert analytics["outside_india"] is True and users["outside_india"] is False
    assert graph["has_cross_border"] is True


def test_edge_into_a_cross_border_store_is_flagged_cross_border():
    graph = build_dfd(build_ropa(ANSWERS, flow_report=FLOW))
    analytics = next(n for n in graph["nodes"] if n["label"] == "analytics")
    edge = next(e for e in graph["edges"] if e["target"] == analytics["id"])
    assert edge["cross_border"] is True


# --- svg ------------------------------------------------------------------------------

def test_svg_is_a_single_self_contained_element():
    svg = dfd_to_svg(build_dfd(_declared_ropa()))
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "<script" not in svg and "xlink:href" not in svg


def test_svg_renders_every_node_label():
    svg = dfd_to_svg(build_dfd(build_ropa(ANSWERS, flow_report=FLOW)))
    assert "users_db" in svg and "analytics" in svg


def test_svg_escapes_markup_in_labels():
    ropa = build_ropa(ANSWERS, activities=[ProcessingActivity(
        activity_id="a1", purpose="R&D <script>", stores=["A & B"],
        categories=["email"], data_principals=["customers"], retention="1y",
        processors=["x"])])
    svg = dfd_to_svg(build_dfd(ropa))
    assert "&amp;" in svg and "<script>" not in svg


def test_svg_marks_the_india_trust_boundary_when_data_leaves():
    svg = dfd_to_svg(build_dfd(build_ropa(ANSWERS, flow_report=FLOW)))
    assert "Outside India" in svg


def test_svg_omits_the_boundary_when_nothing_leaves_india():
    flow = infer_data_flows([DataSource(name="only_db", field_names=["email"],
                                        provider="aws", region="ap-south-1")])
    svg = dfd_to_svg(build_dfd(build_ropa(ANSWERS, flow_report=flow)))
    assert "Outside India" not in svg


# --- DPDPA domain overlay ---------------------------------------------------------------

def test_nodes_carry_the_domain_numbers_that_apply_at_that_stage():
    graph = build_dfd(build_ropa(ANSWERS, flow_report=FLOW))
    analytics = next(n for n in graph["nodes"] if n["label"] == "analytics")
    users = next(n for n in graph["nodes"] if n["label"] == "users_db")
    assert 8 in analytics["domains"] and 8 not in users["domains"]
    assert 4 in users["domains"]


def test_collection_point_node_is_badged_with_notice_and_consent():
    graph = build_dfd(build_ropa(ANSWERS, flow_report=FLOW))
    principal = next(n for n in graph["nodes"] if n["kind"] == "principal")
    assert {1, 2, 3} <= set(principal["domains"])


def test_sdf_badge_rides_along_on_every_node_once_notified():
    graph = build_dfd(build_ropa({**ANSWERS, "notified_as_sdf": True}, flow_report=FLOW))
    assert all(6 in n["domains"] for n in graph["nodes"])


def test_stores_holding_personal_data_are_marked_as_pii_stages():
    graph = build_dfd(build_ropa(ANSWERS, flow_report=FLOW))
    assert next(n for n in graph["nodes"] if n["label"] == "users_db")["has_pii"] is True


def test_svg_draws_a_numbered_badge_and_the_domain_legend():
    svg = dfd_to_svg(build_dfd(build_ropa(ANSWERS, flow_report=FLOW)))
    assert "badge" in svg
    assert "DPDPA domains" in svg
    assert "Cross-border data transfer" in svg


def test_svg_stars_the_stages_where_personal_data_is_used():
    svg = dfd_to_svg(build_dfd(build_ropa(ANSWERS, flow_report=FLOW)))
    assert "Stages where personal data is used" in svg
