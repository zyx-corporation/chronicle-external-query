from __future__ import annotations

import json
from pathlib import Path

import pytest

from chronicle_external_query.ingest.handoff_loader import HandoffLoader
from chronicle_external_query.models import (
    ImportValidationError,
    MissingRequiredKeyError,
    UnsupportedContractVersionError,
)


FIXTURE_BUNDLE_DIR = (
    Path(__file__).resolve().parent / "fixtures" / "query_engine_bundle" / "minimal_cli_bundle"
)


def test_load_bundle_reads_real_cli_generated_bundle_fixture():
    bundle = HandoffLoader().load_bundle(FIXTURE_BUNDLE_DIR)

    assert bundle.chronicle_records is None
    assert bundle.manifest_payload["bundle_kind"] == "query_engine_handoff_bundle"
    assert bundle.handoff_payload["graph_export_format"] == "graph-json"
    assert bundle.handoff_payload["import_validation"]["status"] == "contract_validated"
    assert bundle.graph_payload["export_contract"]["contract_version"] == "1.0"
    assert bundle.adapter_skeleton_payload["skeleton_kind"] == "query_engine_import_adapter"


def test_load_bundle_reads_optional_primary_record_when_present(tmp_path):
    bundle_dir = tmp_path / "bundle"
    chronicle_dir = bundle_dir / ".chronicle"
    chronicle_dir.mkdir(parents=True)

    (chronicle_dir / "chronicle.jsonl").write_text(
        json.dumps({"event_id": "evt_1"}) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "graph.json").write_text(
        json.dumps(
            {
                "export_contract": {
                    "contract_version": "1.0",
                    "export_family": "graph-json",
                    "primary_record": ".chronicle/chronicle.jsonl",
                    "incremental_mode": "event-driven_rebuildable",
                },
                "export_manifest": {"schema_version": "0.4"},
                "nodes": [{"id": "evt_1", "label": "First event"}],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "query_engine_handoff.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "graph_export_format": "graph-json",
                "graph_export_contract_version": "1.0",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "status": "contract_available",
                "import_validation": {
                    "contract_version": "1.0",
                    "status": "contract_validated",
                    "import_ready": True,
                    "checks": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "bundle_kind": "query_engine_handoff_bundle",
                "handoff_contract_version": "1.0",
                "graph_export_contract_version": "1.0",
                "adapter_skeleton_contract_version": "1.0",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "files": [
                    "bundle_manifest.json",
                    "query_engine_handoff.json",
                    "query_engine_adapter_skeleton.json",
                    "graph.json",
                    "ACCEPTANCE_CHECKLIST.md",
                    "TRIAL_REPORT_TEMPLATE.md",
                ],
                "import_validation_status": "contract_validated",
                "import_ready": True,
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "query_engine_adapter_skeleton.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "skeleton_kind": "query_engine_import_adapter",
                "handoff_contract_version": "1.0",
                "import_validation_contract_version": "1.0",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "graph_export_format": "graph-json",
                "graph_export_contract_version": "1.0",
                "required_inputs": [],
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "ACCEPTANCE_CHECKLIST.md").write_text(
        "acceptance checklist",
        encoding="utf-8",
    )
    (bundle_dir / "TRIAL_REPORT_TEMPLATE.md").write_text(
        "trial report template",
        encoding="utf-8",
    )

    bundle = HandoffLoader().load_bundle(bundle_dir)

    assert bundle.chronicle_records == [{"event_id": "evt_1"}]
    assert bundle.graph_payload["nodes"][0]["id"] == "evt_1"
    assert bundle.handoff_payload["contract_version"] == "1.0"
    assert bundle.manifest_payload["contract_version"] == "1.0"


def test_load_bundle_rejects_missing_required_files(tmp_path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()

    with pytest.raises(ImportValidationError) as excinfo:
        HandoffLoader().load_bundle(bundle_dir)

    assert "graph.json" in str(excinfo.value)


def test_load_bundle_rejects_unsupported_contract_versions(tmp_path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "graph.json").write_text(
        json.dumps(
            {
                "export_contract": {
                    "contract_version": "1.0",
                    "export_family": "graph-json",
                    "primary_record": ".chronicle/chronicle.jsonl",
                    "incremental_mode": "event-driven_rebuildable",
                },
                "export_manifest": {"schema_version": "0.4"},
                "nodes": [],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "query_engine_handoff.json").write_text(
        json.dumps(
            {
                "contract_version": "9.9",
                "graph_export_format": "graph-json",
                "graph_export_contract_version": "1.0",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "status": "contract_available",
                "import_validation": {
                    "contract_version": "9.9",
                    "status": "contract_validated",
                    "import_ready": True,
                    "checks": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "bundle_kind": "query_engine_handoff_bundle",
                "handoff_contract_version": "9.9",
                "graph_export_contract_version": "1.0",
                "adapter_skeleton_contract_version": "1.0",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "files": [
                    "bundle_manifest.json",
                    "query_engine_handoff.json",
                    "query_engine_adapter_skeleton.json",
                    "graph.json",
                    "ACCEPTANCE_CHECKLIST.md",
                    "TRIAL_REPORT_TEMPLATE.md",
                ],
                "import_validation_status": "contract_validated",
                "import_ready": True,
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "query_engine_adapter_skeleton.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "skeleton_kind": "query_engine_import_adapter",
                "handoff_contract_version": "9.9",
                "import_validation_contract_version": "9.9",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "graph_export_format": "graph-json",
                "graph_export_contract_version": "1.0",
                "required_inputs": [],
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "ACCEPTANCE_CHECKLIST.md").write_text("acceptance checklist", encoding="utf-8")
    (bundle_dir / "TRIAL_REPORT_TEMPLATE.md").write_text("trial report template", encoding="utf-8")

    with pytest.raises(UnsupportedContractVersionError) as excinfo:
        HandoffLoader().load_bundle(bundle_dir)

    assert "query_engine_handoff.json contract_version" in str(excinfo.value)


def test_load_bundle_rejects_missing_required_keys(tmp_path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "graph.json").write_text(
        json.dumps(
            {
                "export_contract": {
                    "contract_version": "1.0",
                    "export_family": "graph-json",
                    "primary_record": ".chronicle/chronicle.jsonl",
                    "incremental_mode": "event-driven_rebuildable",
                },
                "export_manifest": {"schema_version": "0.4"},
                "nodes": [],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "query_engine_handoff.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "graph_export_format": "graph-json",
                "graph_export_contract_version": "1.0",
                "status": "contract_available",
                "import_validation": {
                    "contract_version": "1.0",
                    "status": "contract_validated",
                    "import_ready": True,
                    "checks": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "bundle_kind": "query_engine_handoff_bundle",
                "handoff_contract_version": "1.0",
                "graph_export_contract_version": "1.0",
                "adapter_skeleton_contract_version": "1.0",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "files": [
                    "bundle_manifest.json",
                    "query_engine_handoff.json",
                    "query_engine_adapter_skeleton.json",
                    "graph.json",
                    "ACCEPTANCE_CHECKLIST.md",
                    "TRIAL_REPORT_TEMPLATE.md",
                ],
                "import_validation_status": "contract_validated",
                "import_ready": True,
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "query_engine_adapter_skeleton.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0",
                "skeleton_kind": "query_engine_import_adapter",
                "handoff_contract_version": "1.0",
                "import_validation_contract_version": "1.0",
                "primary_record_path": ".chronicle/chronicle.jsonl",
                "graph_export_format": "graph-json",
                "graph_export_contract_version": "1.0",
                "required_inputs": [],
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "ACCEPTANCE_CHECKLIST.md").write_text("acceptance checklist", encoding="utf-8")
    (bundle_dir / "TRIAL_REPORT_TEMPLATE.md").write_text("trial report template", encoding="utf-8")

    with pytest.raises(MissingRequiredKeyError) as excinfo:
        HandoffLoader().load_bundle(bundle_dir)

    assert "primary_record_path" in str(excinfo.value)
