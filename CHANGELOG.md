# Changelog

All notable changes to this project will be documented here. This project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [1.1.2] — 2026-05-22

### Changed
- **Pydantic v2 schema validation** — replaces hand-rolled `validate_config` and `preprocess_pipeline` with a full Pydantic model hierarchy (`PipelineConfig`, `PipelineEntry`, `CdcConf`, `CsvOptions`, `ExcelOptions`, `ColumnMask`, `RowFilter`, `Column`, `Expectation`, `Schedule`, `FileTrigger`); structured error messages with field paths; defaults handled by the model
- `pydantic>=2.0` added as a runtime dependency

---

## [1.1.1] — 2026-05-22

### Fixed
- Release workflow now fails early with a clear message when triggered with no new commits since the last tag, preventing accidental duplicate version bumps

---

## [1.1.0] — 2026-05-22

### Added
- **CI workflow** — GitHub Actions runs ruff lint and pytest with coverage on PRs to `main`, pushes to `main`, and manual dispatch
- **Release workflow** — `workflow_dispatch` with `patch`/`minor`/`major` input; bumps version files, commits, tags, and creates a GitHub Release automatically
- **`bump-my-version`** — automated version management configured in `pyproject.toml`
- **`--version` flag** — `lakeflow-generate --version` prints the installed package version
- **ruff linting** — E, F, I rules enforced in CI and available locally via `pip install -e ".[dev]"`
- **pytest-cov coverage** — coverage reported on every test run
- **119-test suite** — covers config validation (`test_validation.py`), DABs variable resolution (`test_resolve_bundle_var.py`), and all five Jinja2 templates (`test_templates.py`)
- **Claude Code integration** — GitHub workflows for Claude Code review and assistance

---

## [1.0.0] — 2026-05-22

Initial release.

### Features

- **`lakeflow-generate` CLI** — generates all DABs bundle artifacts from a declarative `pipeline_config.yaml`
- **Four Silver strategies** — SCD Type 1 (upsert), SCD Type 2 (history), Streaming (append-only), Materialized View (with `WHERE`/`QUALIFY` support)
- **Source formats** — Parquet, CSV (custom delimiters, permissive error handling), and Excel (single sheet or multi-sheet `UNION ALL`)
- **Bronze → Cleaned View → Quarantine → Silver architecture** — one generated `.sql` file per pipeline entry
- **DABs variable resolution** — `domain`, `catalog`, and `audit_schema` read from `databricks.yml` at generation time via `resolve_bundle_var`; no duplication between `pipeline_config.yaml` and `databricks.yml`
- **`${env}` substitution** — path strings in `pipeline_config.yaml` support environment-specific values
- **Governance tagging** — dual-layer: `TBLPROPERTIES` embedded in SQL at creation time, plus `ALTER TABLE SET TAGS` applied by a post-pipeline job task
- **Column tags** — optional per-column Unity Catalog tags declared inline in `columns`
- **Column masks and row filters** — declarative Unity Catalog masking applied via `ALTER TABLE` after each pipeline run
- **Data quality expectations** — pipeline constraint rules with automatic quarantine table generation and optional expectations report task
- **Orchestration job** — four-task Databricks Workflow Job: pipeline trigger → UC tags → expectations report (optional) → downstream job chaining (optional)
- **`--dry-run` flag** — preview generated file paths without writing anything to disk
- **`--version` flag** — print the installed framework version
- **119-test suite** — covers config validation, DABs variable resolution, and all five Jinja2 templates
- **CI** — GitHub Actions runs tests on PRs and pushes to `main`
