"""Tests for resolve_bundle_var — DABs variable resolution from databricks.yml."""
import pytest
import yaml

from lakeflow_ingestion_framework.cli import resolve_bundle_var


@pytest.fixture
def bundle_file(tmp_path):
    """A minimal databricks.yml with target-level overrides and bundle-level defaults."""
    content = {
        "variables": {
            # bundle-level defaults (used when a target doesn't override)
            "domain": {"default": "lakeflow-pipeline-ingestion-framework-examples"},
            "audit_schema": {"default": "audit"},
        },
        "targets": {
            "dev": {
                "variables": {
                    # dev overrides catalog but inherits domain from bundle default
                    "catalog": "enterprise_dev",
                    "warehouse_id": "abc123def456",
                }
            },
            "prod": {
                "variables": {
                    # prod overrides both catalog and domain
                    "catalog": "enterprise_prod",
                    "domain": "clinical-ops-prod",
                    "warehouse_id": "xyz789uvw012",
                }
            },
        },
    }
    f = tmp_path / "databricks.yml"
    f.write_text(yaml.dump(content), encoding="utf-8")
    return f


def test_target_specific_value_returned(bundle_file):
    # a variable set under targets.<env>.variables is returned directly
    assert resolve_bundle_var(bundle_file, "dev", "catalog") == "enterprise_dev"


def test_bundle_level_default_used_when_target_lacks_override(bundle_file):
    # dev does not set 'domain', so the bundle-level default is used as fallback
    assert resolve_bundle_var(bundle_file, "dev", "domain") == "lakeflow-pipeline-ingestion-framework-examples"


def test_target_override_takes_precedence_over_bundle_default(bundle_file):
    # prod defines its own 'domain', which should win over the bundle-level default
    assert resolve_bundle_var(bundle_file, "prod", "domain") == "clinical-ops-prod"


def test_audit_schema_bundle_default_returned(bundle_file):
    # audit_schema has a bundle-level default and neither target overrides it
    assert resolve_bundle_var(bundle_file, "dev", "audit_schema") == "audit"


def test_missing_var_with_no_default_raises(bundle_file):
    # a variable that is absent from both target and bundle-level must raise
    with pytest.raises(ValueError, match="nonexistent_var"):
        resolve_bundle_var(bundle_file, "prod", "nonexistent_var")


def test_missing_var_with_default_argument_returns_default(bundle_file):
    # when the var is absent but a Python-level default is provided, return it
    result = resolve_bundle_var(bundle_file, "dev", "performance_target", default="STANDARD")
    assert result == "STANDARD"


def test_missing_bundle_file_raises(tmp_path):
    # a non-existent databricks.yml must produce a clear error referencing the path
    missing = tmp_path / "databricks.yml"
    with pytest.raises(ValueError, match="not found"):
        resolve_bundle_var(missing, "dev", "catalog")


def test_unknown_target_falls_back_to_bundle_default(bundle_file):
    # an unknown target has no variables, so the bundle-level default applies
    assert resolve_bundle_var(bundle_file, "staging", "domain") == "lakeflow-pipeline-ingestion-framework-examples"


def test_unknown_target_missing_var_raises(bundle_file):
    # an unknown target with no bundle-level default must raise
    with pytest.raises(ValueError, match="catalog"):
        resolve_bundle_var(bundle_file, "staging", "catalog")
