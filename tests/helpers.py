"""Shared test helpers for building minimal valid config and context dicts.

Table naming mirrors the companion example repo:
  bronze: enterprise_dev.bronze.<table>
  silver: enterprise_dev.silver.<table>
"""
from pathlib import Path

from lakeflow_ingestion_framework.cli import preprocess_pipeline

TEMPLATES_DIR = Path(__file__).parent.parent / "lakeflow_ingestion_framework" / "templates"


def make_pipe(**overrides) -> dict:
    """Return a preprocessed SCD1/CSV pipeline dict (patients) with sensible defaults."""
    pipe = {
        "bronze_table_name": "enterprise_dev.bronze.patients",
        "silver_table_name": "enterprise_dev.silver.patients",
        "table_type": "scd1",
        "description": "Current member records — upserted daily from Synthea patient snapshots.",
        "source_path": "/Volumes/enterprise_dev/staging/example_raw_files_volume/patients",
        "source_file_type": "csv",
        "columns": [
            {"source": "Id", "target": "member_id", "target_datatype": "STRING", "comment": "Synthea patient UUID"},
            {"source": "FIRST", "target": "first_name", "target_datatype": "STRING", "comment": "First name"},
            {"source": "SSN", "target": "ssn", "target_datatype": "STRING", "comment": "SSN (masked)"},
        ],
        "cdc_conf": {"keys": ["member_id"], "sequence_by": "source_file_modification_time"},
    }
    pipe.update(overrides)
    return preprocess_pipeline(pipe)


def make_context(pipes=None, **overrides) -> dict:
    """Return a minimal valid Jinja2 context dict for template rendering tests."""
    if pipes is None:
        pipes = [make_pipe()]
    ctx = {
        "pipelines": pipes,
        "pipelines_with_expectations": [p for p in pipes if p.get("expectations")],
        "pipeline_name": "synthea_pipeline",
        "catalog": "enterprise_dev",
        "audit_schema": "audit",
        "Domain": "clinical-ops",
        "domain": "clinical-ops",
        "GitHubRepo": "github.com/cpiazza01/lakeflow-pipeline-ingestion-framework-dabs-examples",
        "FrameworkUsed": "Lakeflow Pipeline Ingestion Framework",
        "JobName": "synthea_pipeline_job",
        "PipelineName": "synthea_pipeline",
        "custom_tags": {"DataSource": "Synthea"},
        "github_repo": "github.com/cpiazza01/lakeflow-pipeline-ingestion-framework-dabs-examples",
        "framework_tag": "Lakeflow Pipeline Ingestion Framework",
        "job_name": "synthea_pipeline_job",
        "env": "dev",
        "email_notifications": ["codypiazza@example.com"],
        "email_on_job_success": True,
        "email_on_pipeline_success": True,
        "expectations_report_emails": ["codypiazza@gmail.com"],
        "pipeline_alerts": ["on-update-success", "on-update-fatal-failure"],
        "excel_used": False,
        "pipeline_access_group": None,
        "service_principal_job_runners": [],
        "enable_expectations_report": False,
        "trigger_downstream_job": False,
        "downstream_job_id": None,
        "downstream_job_parameters": {},
        "schedule": None,
        "file_trigger": None,
    }
    ctx.update(overrides)
    return ctx


def base_config(**overrides) -> dict:
    """Return a minimal valid pipeline_config.yaml dict for validation tests."""
    cfg = {
        "pipeline_name": "synthea_pipeline",
        "github_repo": "github.com/cpiazza01/lakeflow-pipeline-ingestion-framework-dabs-examples",
        "email_notifications": ["codypiazza@example.com"],
        "pipelines": [
            {
                "bronze_table_name": "enterprise_dev.bronze.patients",
                "silver_table_name": "enterprise_dev.silver.patients",
                "table_type": "scd1",
                "description": "Current member records.",
                "source_path": "/Volumes/enterprise_dev/staging/example_raw_files_volume/patients",
                "source_file_type": "csv",
                "columns": [
                    {"source": "Id", "target": "member_id", "target_datatype": "STRING", "comment": "Patient UUID"}
                ],
                "cdc_conf": {"keys": ["member_id"], "sequence_by": "source_file_modification_time"},
            }
        ],
    }
    cfg.update(overrides)
    return cfg
