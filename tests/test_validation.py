"""Tests for validate_config and substitute_env."""
import pytest

from lakeflow_ingestion_framework.cli import substitute_env, validate_config
from tests.helpers import base_config

# ---------------------------------------------------------------------------
# substitute_env
# ---------------------------------------------------------------------------

def test_substitute_env_replaces_env_placeholder():
    # ${env} in a path string must be swapped for the given env name
    raw = "s3://my-bucket-${env}/data"
    assert substitute_env(raw, "dev") == "s3://my-bucket-dev/data"


def test_substitute_env_multiple_occurrences():
    # every occurrence of ${env} must be replaced, not just the first
    raw = "/Volumes/enterprise_${env}/staging/${env}/files"
    assert substitute_env(raw, "prod") == "/Volumes/enterprise_prod/staging/prod/files"


def test_substitute_env_no_placeholder_is_noop():
    # strings without ${env} must pass through unchanged
    raw = "s3://my-bucket/data"
    assert substitute_env(raw, "dev") == "s3://my-bucket/data"


# ---------------------------------------------------------------------------
# validate_config — happy paths
# ---------------------------------------------------------------------------

def test_valid_scd1_config_passes():
    # a minimal but fully-specified SCD1 config must not raise
    validate_config(base_config(), "dev")


def test_valid_scd2_config_passes():
    # SCD2 requires the same fields as SCD1; must not raise
    pipe = {**base_config()["pipelines"][0], "table_type": "scd2"}
    validate_config(base_config(pipelines=[pipe]), "dev")


def test_valid_streaming_config_passes():
    # streaming does not require cdc_conf; must not raise
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != "cdc_conf"}
    pipe["table_type"] = "streaming"
    validate_config(base_config(pipelines=[pipe]), "dev")


def test_valid_materialized_config_passes():
    # materialized does not require cdc_conf; must not raise
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != "cdc_conf"}
    pipe["table_type"] = "materialized"
    validate_config(base_config(pipelines=[pipe]), "dev")


def test_any_nonempty_env_accepted():
    # env is no longer restricted to a fixed set; any non-empty string is valid
    validate_config(base_config(), "staging")
    validate_config(base_config(), "uat")
    validate_config(base_config(), "prod-eu")


# ---------------------------------------------------------------------------
# validate_config — pipelines list
# ---------------------------------------------------------------------------

def test_missing_pipelines_key_raises():
    # a config without the top-level 'pipelines' key is invalid
    cfg = base_config()
    del cfg["pipelines"]
    with pytest.raises(ValueError, match="pipelines"):
        validate_config(cfg, "dev")


def test_empty_pipelines_raises():
    # an empty pipelines list is not allowed — at least one entry is required
    with pytest.raises(ValueError, match="pipelines"):
        validate_config(base_config(pipelines=[]), "dev")


def test_empty_env_raises():
    # an empty env string must be rejected
    with pytest.raises(ValueError, match="env"):
        validate_config(base_config(), "")


# ---------------------------------------------------------------------------
# validate_config — required per-pipeline fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", ["bronze_table_name", "silver_table_name", "table_type", "description"])
def test_missing_required_pipe_field_raises(field):
    # each of these four fields is mandatory on every pipeline entry
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != field}
    with pytest.raises(ValueError, match=field):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_missing_columns_raises():
    # an empty columns list must be rejected
    pipe = {**base_config()["pipelines"][0], "columns": []}
    with pytest.raises(ValueError, match="columns"):
        validate_config(base_config(pipelines=[pipe]), "dev")


# ---------------------------------------------------------------------------
# validate_config — table_type
# ---------------------------------------------------------------------------

def test_invalid_table_type_raises():
    # table_type must be one of the four supported strategies
    pipe = {**base_config()["pipelines"][0], "table_type": "incremental"}
    with pytest.raises(ValueError, match="table_type"):
        validate_config(base_config(pipelines=[pipe]), "dev")


# ---------------------------------------------------------------------------
# validate_config — cdc_conf
# ---------------------------------------------------------------------------

def test_scd1_missing_cdc_conf_raises():
    # scd1 requires a cdc_conf block
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != "cdc_conf"}
    with pytest.raises(ValueError, match="cdc_conf"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_scd2_missing_cdc_conf_raises():
    # scd2 also requires a cdc_conf block
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != "cdc_conf"}
    pipe["table_type"] = "scd2"
    with pytest.raises(ValueError, match="cdc_conf"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_scd1_missing_cdc_keys_raises():
    # cdc_conf must include a non-empty 'keys' list
    pipe = {**base_config()["pipelines"][0], "cdc_conf": {"sequence_by": "updated_at"}}
    with pytest.raises(ValueError, match="cdc_conf"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_scd1_missing_cdc_sequence_by_raises():
    # cdc_conf must include a 'sequence_by' column
    pipe = {**base_config()["pipelines"][0], "cdc_conf": {"keys": ["member_id"]}}
    with pytest.raises(ValueError, match="cdc_conf"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_streaming_does_not_require_cdc_conf():
    # streaming tables use append-only logic — cdc_conf is not required
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != "cdc_conf"}
    pipe["table_type"] = "streaming"
    validate_config(base_config(pipelines=[pipe]), "dev")  # must not raise


# ---------------------------------------------------------------------------
# validate_config — qualify_clause
# ---------------------------------------------------------------------------

def test_qualify_clause_on_non_materialized_raises():
    # QUALIFY is a Databricks SQL clause only valid on materialized views
    pipe = {**base_config()["pipelines"][0], "qualify_clause": "ROW_NUMBER() = 1"}
    with pytest.raises(ValueError, match="qualify_clause"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_qualify_clause_on_materialized_passes():
    # qualify_clause is valid and expected on materialized table_type
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != "cdc_conf"}
    pipe["table_type"] = "materialized"
    pipe["qualify_clause"] = "ROW_NUMBER() OVER(PARTITION BY member_id ORDER BY ts DESC) = 1"
    validate_config(base_config(pipelines=[pipe]), "dev")  # must not raise


# ---------------------------------------------------------------------------
# validate_config — schedule / file_trigger
# ---------------------------------------------------------------------------

def test_schedule_and_file_trigger_mutually_exclusive():
    # only one trigger type may be configured at a time
    cfg = base_config(
        schedule={"quartz_cron_expression": "0 0 6 * * ?", "timezone_id": "UTC", "pause_status": "UNPAUSED"},
        file_trigger={
            "url": "s3://bucket/",
            "wait_after_last_change_seconds": 300,
            "min_time_between_triggers_seconds": 3600,
        },
    )
    with pytest.raises(ValueError, match="mutually exclusive"):
        validate_config(cfg, "dev")


def test_schedule_alone_passes():
    # a cron schedule without a file trigger is valid
    cfg = base_config(
        schedule={"quartz_cron_expression": "0 0 6 * * ?", "timezone_id": "America/Chicago", "pause_status": "UNPAUSED"}
    )
    validate_config(cfg, "dev")  # must not raise


# ---------------------------------------------------------------------------
# validate_config — downstream job
# ---------------------------------------------------------------------------

def test_trigger_downstream_job_without_id_raises():
    # enabling downstream job chaining requires a downstream_job_id
    with pytest.raises(ValueError, match="downstream_job_id"):
        validate_config(base_config(trigger_downstream_job=True), "dev")


def test_trigger_downstream_job_with_id_passes():
    # downstream job is valid when an ID is provided
    validate_config(base_config(trigger_downstream_job=True, downstream_job_id=12345), "dev")


# ---------------------------------------------------------------------------
# validate_config — column_masks
# ---------------------------------------------------------------------------

def test_column_mask_missing_column_raises():
    # each column_masks entry must name the column being masked
    pipe = {**base_config()["pipelines"][0], "column_masks": [{"function": "cat.schema.fn"}]}
    with pytest.raises(ValueError, match="column"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_column_mask_missing_function_raises():
    # each column_masks entry must specify the masking UDF
    pipe = {**base_config()["pipelines"][0], "column_masks": [{"column": "ssn"}]}
    with pytest.raises(ValueError, match="function"):
        validate_config(base_config(pipelines=[pipe]), "dev")


# ---------------------------------------------------------------------------
# validate_config — row_filter
# ---------------------------------------------------------------------------

def test_row_filter_missing_function_raises():
    # row_filter must specify the filter UDF
    pipe = {**base_config()["pipelines"][0], "row_filter": {"on_columns": ["region"]}}
    with pytest.raises(ValueError, match="function"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_row_filter_missing_on_columns_raises():
    # row_filter must specify which columns the UDF accepts as arguments
    pipe = {**base_config()["pipelines"][0], "row_filter": {"function": "cat.schema.fn"}}
    with pytest.raises(ValueError, match="on_columns"):
        validate_config(base_config(pipelines=[pipe]), "dev")


# ---------------------------------------------------------------------------
# validate_config — source_file_type
# ---------------------------------------------------------------------------

def test_invalid_source_file_type_raises():
    # only parquet, csv, and excel are supported source formats
    pipe = {**base_config()["pipelines"][0], "source_file_type": "json"}
    with pytest.raises(ValueError, match="source_file_type"):
        validate_config(base_config(pipelines=[pipe]), "dev")


def test_reuse_bronze_skips_source_file_type_check():
    # when reuse_bronze is true, source_file_type is not needed
    pipe = {k: v for k, v in base_config()["pipelines"][0].items() if k != "source_file_type"}
    pipe["reuse_bronze"] = True
    validate_config(base_config(pipelines=[pipe]), "dev")  # must not raise
