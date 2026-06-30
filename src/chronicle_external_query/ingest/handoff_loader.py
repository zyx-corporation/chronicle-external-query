from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chronicle_external_query.ingest.chronicle_loader import load_jsonl_records
from chronicle_external_query.ingest.graph_loader import load_graph_payload
from chronicle_external_query.models import (
    BundlePaths,
    ContractConsistencyError,
    HandoffBundle,
    ImportValidationError,
    InvalidBundleObjectError,
    InvalidJsonError,
    MissingRequiredFileError,
    MissingRequiredKeyError,
    UnsupportedContractVersionError,
)


class HandoffLoader:
    """Load a Chronicle handoff bundle from a local directory."""

    SUPPORTED_BUNDLE_CONTRACT_VERSION = "1.0"
    SUPPORTED_HANDOFF_CONTRACT_VERSION = "1.0"
    SUPPORTED_GRAPH_EXPORT_CONTRACT_VERSION = "1.0"
    SUPPORTED_ADAPTER_SKELETON_CONTRACT_VERSION = "1.0"
    SUPPORTED_GRAPH_EXPORT_FORMAT = "graph-json"
    EXPECTED_BUNDLE_KIND = "query_engine_handoff_bundle"

    REQUIRED_FILES = {
        "graph_json": "graph.json",
        "handoff_json": "query_engine_handoff.json",
        "manifest_json": "bundle_manifest.json",
        "adapter_skeleton_json": "query_engine_adapter_skeleton.json",
        "acceptance_checklist_md": "ACCEPTANCE_CHECKLIST.md",
        "trial_report_template_md": "TRIAL_REPORT_TEMPLATE.md",
    }

    def load_bundle(self, bundle_dir: Path) -> HandoffBundle:
        resolved_dir = bundle_dir.resolve()
        paths = self._resolve_paths(resolved_dir)
        manifest_payload = self._load_json_object(paths.manifest_json, "bundle_manifest.json")
        self._validate_manifest_payload(manifest_payload)
        self._validate_manifest_files(paths.bundle_dir, manifest_payload)
        handoff_payload = self._load_json_object(paths.handoff_json, "query_engine_handoff.json")
        adapter_skeleton_payload = self._load_json_object(
            paths.adapter_skeleton_json,
            "query_engine_adapter_skeleton.json",
        )
        graph_payload = load_graph_payload(paths.graph_json)
        self._validate_handoff_payload(handoff_payload)
        self._validate_adapter_skeleton_payload(adapter_skeleton_payload)
        self._validate_graph_payload(graph_payload)
        self._validate_contract_consistency(
            manifest_payload=manifest_payload,
            handoff_payload=handoff_payload,
            graph_payload=graph_payload,
            adapter_skeleton_payload=adapter_skeleton_payload,
        )
        chronicle_records = (
            load_jsonl_records(paths.primary_record_jsonl)
            if paths.primary_record_jsonl is not None and paths.primary_record_jsonl.exists()
            else None
        )
        return HandoffBundle(
            paths=paths,
            chronicle_records=chronicle_records,
            graph_payload=graph_payload,
            handoff_payload=handoff_payload,
            manifest_payload=manifest_payload,
            adapter_skeleton_payload=adapter_skeleton_payload,
        )

    def _resolve_paths(self, bundle_dir: Path) -> BundlePaths:
        resolved: dict[str, Path] = {"bundle_dir": bundle_dir}
        missing: list[str] = []
        for key, relative_path in self.REQUIRED_FILES.items():
            path = bundle_dir / relative_path
            if not path.exists():
                missing.append(relative_path)
            resolved[key] = path
        if missing:
            joined = ", ".join(sorted(missing))
            raise MissingRequiredFileError(f"bundle is missing required files: {joined}")
        primary_record_jsonl = bundle_dir / ".chronicle" / "chronicle.jsonl"
        resolved["primary_record_jsonl"] = primary_record_jsonl if primary_record_jsonl.exists() else None
        return BundlePaths(**resolved)

    def _load_json_object(self, path: Path, label: str) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise InvalidJsonError(f"{label} contains invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise InvalidBundleObjectError(f"{label} must decode to an object")
        return payload

    def _validate_manifest_payload(self, payload: dict[str, Any]) -> None:
        self._require_keys(
            payload,
            "bundle_manifest.json",
            {
                "contract_version",
                "bundle_kind",
                "handoff_contract_version",
                "graph_export_contract_version",
                "adapter_skeleton_contract_version",
                "primary_record_path",
                "files",
                "import_validation_status",
                "import_ready",
            },
        )
        self._require_contract_version(
            label="bundle_manifest.json contract_version",
            actual=str(payload["contract_version"]),
            supported=self.SUPPORTED_BUNDLE_CONTRACT_VERSION,
        )
        if str(payload["bundle_kind"]) != self.EXPECTED_BUNDLE_KIND:
            raise ContractConsistencyError(
                "bundle_manifest.json bundle_kind must be "
                f"{self.EXPECTED_BUNDLE_KIND!r}, got {payload['bundle_kind']!r}"
            )
        if not isinstance(payload["files"], list):
            raise InvalidBundleObjectError("bundle_manifest.json files must decode to a list")

    def _validate_manifest_files(self, bundle_dir: Path, manifest_payload: dict[str, Any]) -> None:
        missing: list[str] = []
        for relative_path in manifest_payload.get("files", []):
            if not isinstance(relative_path, str):
                raise InvalidBundleObjectError("bundle_manifest.json files entries must be strings")
            if not (bundle_dir / relative_path).exists():
                missing.append(relative_path)
        if missing:
            joined = ", ".join(sorted(missing))
            raise MissingRequiredFileError(f"bundle is missing files listed in bundle_manifest.json: {joined}")

    def _validate_handoff_payload(self, payload: dict[str, Any]) -> None:
        self._require_keys(
            payload,
            "query_engine_handoff.json",
            {
                "contract_version",
                "graph_export_format",
                "graph_export_contract_version",
                "primary_record_path",
                "import_validation",
                "status",
            },
        )
        self._require_contract_version(
            label="query_engine_handoff.json contract_version",
            actual=str(payload["contract_version"]),
            supported=self.SUPPORTED_HANDOFF_CONTRACT_VERSION,
        )
        if str(payload["graph_export_format"]) != self.SUPPORTED_GRAPH_EXPORT_FORMAT:
            raise UnsupportedContractVersionError(
                "query_engine_handoff.json graph_export_format must be "
                f"{self.SUPPORTED_GRAPH_EXPORT_FORMAT!r}, got {payload['graph_export_format']!r}"
            )
        import_validation = payload["import_validation"]
        if not isinstance(import_validation, dict):
            raise InvalidBundleObjectError("query_engine_handoff.json import_validation must decode to an object")
        self._require_keys(
            import_validation,
            "query_engine_handoff.json import_validation",
            {"contract_version", "status", "import_ready", "checks"},
        )
        self._require_contract_version(
            label="query_engine_handoff.json import_validation contract_version",
            actual=str(import_validation["contract_version"]),
            supported=self.SUPPORTED_HANDOFF_CONTRACT_VERSION,
        )

    def _validate_adapter_skeleton_payload(self, payload: dict[str, Any]) -> None:
        self._require_keys(
            payload,
            "query_engine_adapter_skeleton.json",
            {
                "contract_version",
                "skeleton_kind",
                "handoff_contract_version",
                "import_validation_contract_version",
                "primary_record_path",
                "graph_export_format",
                "graph_export_contract_version",
                "required_inputs",
            },
        )
        self._require_contract_version(
            label="query_engine_adapter_skeleton.json contract_version",
            actual=str(payload["contract_version"]),
            supported=self.SUPPORTED_ADAPTER_SKELETON_CONTRACT_VERSION,
        )
        if str(payload["graph_export_format"]) != self.SUPPORTED_GRAPH_EXPORT_FORMAT:
            raise UnsupportedContractVersionError(
                "query_engine_adapter_skeleton.json graph_export_format must be "
                f"{self.SUPPORTED_GRAPH_EXPORT_FORMAT!r}, got {payload['graph_export_format']!r}"
            )

    def _validate_graph_payload(self, payload: dict[str, Any]) -> None:
        self._require_keys(
            payload,
            "graph.json",
            {"export_contract", "export_manifest", "nodes", "edges"},
        )
        export_contract = payload["export_contract"]
        if not isinstance(export_contract, dict):
            raise InvalidBundleObjectError("graph.json export_contract must decode to an object")
        self._require_keys(
            export_contract,
            "graph.json export_contract",
            {"contract_version", "export_family", "primary_record", "incremental_mode"},
        )
        self._require_contract_version(
            label="graph.json export_contract contract_version",
            actual=str(export_contract["contract_version"]),
            supported=self.SUPPORTED_GRAPH_EXPORT_CONTRACT_VERSION,
        )
        if str(export_contract["export_family"]) != self.SUPPORTED_GRAPH_EXPORT_FORMAT:
            raise UnsupportedContractVersionError(
                "graph.json export_contract export_family must be "
                f"{self.SUPPORTED_GRAPH_EXPORT_FORMAT!r}, got {export_contract['export_family']!r}"
            )

    def _validate_contract_consistency(
        self,
        *,
        manifest_payload: dict[str, Any],
        handoff_payload: dict[str, Any],
        graph_payload: dict[str, Any],
        adapter_skeleton_payload: dict[str, Any],
    ) -> None:
        graph_contract = graph_payload["export_contract"]
        import_validation = handoff_payload["import_validation"]
        checks = [
            (
                "bundle_manifest.json handoff_contract_version",
                str(manifest_payload["handoff_contract_version"]),
                str(handoff_payload["contract_version"]),
            ),
            (
                "bundle_manifest.json graph_export_contract_version",
                str(manifest_payload["graph_export_contract_version"]),
                str(graph_contract["contract_version"]),
            ),
            (
                "bundle_manifest.json adapter_skeleton_contract_version",
                str(manifest_payload["adapter_skeleton_contract_version"]),
                str(adapter_skeleton_payload["contract_version"]),
            ),
            (
                "query_engine_handoff.json graph_export_contract_version",
                str(handoff_payload["graph_export_contract_version"]),
                str(graph_contract["contract_version"]),
            ),
            (
                "query_engine_handoff.json import_validation contract_version",
                str(import_validation["contract_version"]),
                str(handoff_payload["contract_version"]),
            ),
            (
                "query_engine_adapter_skeleton.json handoff_contract_version",
                str(adapter_skeleton_payload["handoff_contract_version"]),
                str(handoff_payload["contract_version"]),
            ),
            (
                "query_engine_adapter_skeleton.json import_validation_contract_version",
                str(adapter_skeleton_payload["import_validation_contract_version"]),
                str(import_validation["contract_version"]),
            ),
            (
                "query_engine_adapter_skeleton.json graph_export_contract_version",
                str(adapter_skeleton_payload["graph_export_contract_version"]),
                str(graph_contract["contract_version"]),
            ),
            (
                "primary_record_path",
                str(manifest_payload["primary_record_path"]),
                str(handoff_payload["primary_record_path"]),
            ),
            (
                "graph primary_record",
                str(handoff_payload["primary_record_path"]),
                str(graph_contract["primary_record"]),
            ),
            (
                "graph export format",
                str(handoff_payload["graph_export_format"]),
                str(graph_contract["export_family"]),
            ),
        ]
        for label, left, right in checks:
            if left != right:
                raise ContractConsistencyError(f"contract mismatch for {label}: {left!r} != {right!r}")

    def _require_keys(self, payload: dict[str, Any], label: str, required_keys: set[str]) -> None:
        missing = sorted(key for key in required_keys if key not in payload)
        if missing:
            joined = ", ".join(missing)
            raise MissingRequiredKeyError(f"{label} is missing required keys: {joined}")

    def _require_contract_version(self, *, label: str, actual: str, supported: str) -> None:
        if actual != supported:
            raise UnsupportedContractVersionError(
                f"{label} is unsupported: got {actual!r}, expected {supported!r}"
            )
