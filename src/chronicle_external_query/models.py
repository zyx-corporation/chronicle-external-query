from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BundlePaths:
    bundle_dir: Path
    graph_json: Path
    handoff_json: Path
    manifest_json: Path
    adapter_skeleton_json: Path
    acceptance_checklist_md: Path
    trial_report_template_md: Path
    primary_record_jsonl: Path | None


@dataclass(frozen=True)
class HandoffBundle:
    paths: BundlePaths
    chronicle_records: list[dict[str, Any]] | None
    graph_payload: dict[str, Any]
    handoff_payload: dict[str, Any]
    manifest_payload: dict[str, Any]
    adapter_skeleton_payload: dict[str, Any]


class ImportValidationError(ValueError):
    """Raised when a Chronicle bundle is missing required files or structure."""

    error_code = "validation.unspecified"

    @property
    def error_category(self) -> str:
        return self.error_code.rsplit(".", 1)[0]


class MissingRequiredFileError(ImportValidationError):
    """Raised when a required bundle file is absent."""

    error_code = "bundle_validation.missing_required_file"


class InvalidJsonError(ImportValidationError):
    """Raised when a bundle file contains malformed JSON."""

    error_code = "bundle_validation.invalid_json"


class InvalidBundleObjectError(ImportValidationError):
    """Raised when a bundle file decodes to an unsupported top-level shape."""

    error_code = "bundle_validation.invalid_bundle_object"


class MissingRequiredKeyError(ImportValidationError):
    """Raised when a bundle payload is missing required keys."""

    error_code = "bundle_validation.missing_required_key"


class UnsupportedContractVersionError(ImportValidationError):
    """Raised when a bundle contract version is not supported."""

    error_code = "bundle_validation.unsupported_contract_version"


class ContractConsistencyError(ImportValidationError):
    """Raised when bundle payloads disagree about core contract details."""

    error_code = "bundle_validation.contract_consistency"


class VectorFixtureValidationError(ImportValidationError):
    """Raised when a local vector fixture cannot be loaded safely."""

    error_code = "vector_fixture_validation.invalid_fixture"


class EvaluationArtifactValidationError(ImportValidationError):
    """Raised when a local evaluation artifact cannot be loaded safely."""

    error_code = "evaluation_artifact_validation.invalid_artifact"
