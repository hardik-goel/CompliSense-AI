"""Collection-source config validator (pure)."""

import pytest

from compliance.collection_config import CollectionConfigError, validate_source, validate_sources


def test_valid_s3_source_normalised():
    s = validate_source({"type": "s3", "label": "Docs bucket",
                         "config": {"bucket": "b", "prefix": "docs/", "region": "us-east-1"}})
    assert s["type"] == "s3" and s["label"] == "Docs bucket"
    assert s["config"] == {"bucket": "b", "prefix": "docs/", "region": "us-east-1"}


def test_unknown_type_rejected():
    with pytest.raises(CollectionConfigError):
        validate_source({"type": "ftp", "config": {}})


def test_secret_field_rejected():
    with pytest.raises(CollectionConfigError) as e:
        validate_source({"type": "github", "config": {"repo": "o/r", "token": "ghp_x"}})
    assert "secret" in str(e.value).lower()


def test_unknown_field_rejected():
    with pytest.raises(CollectionConfigError):
        validate_source({"type": "s3", "config": {"bucket": "b", "weird": "x"}})


def test_required_field_enforced():
    with pytest.raises(CollectionConfigError):
        validate_source({"type": "s3", "config": {"prefix": "docs/"}})  # no bucket


def test_label_defaults_to_type():
    assert validate_source({"type": "notion", "config": {}})["label"] == "notion"


def test_azure_requires_account_url_and_container():
    with pytest.raises(CollectionConfigError):
        validate_source({"type": "azure_blob", "config": {"container": "c"}})  # no account_url
    ok = validate_source({"type": "azure_blob", "config": {"account_url": "https://a", "container": "c"}})
    assert ok["config"]["container"] == "c"


def test_validate_sources_list():
    out = validate_sources([{"type": "gcs", "config": {"bucket": "b"}},
                            {"type": "local", "config": {"path": "/x"}}])
    assert [s["type"] for s in out] == ["gcs", "local"]
