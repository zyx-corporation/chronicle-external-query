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


class MissingRequiredFileError(ImportValidationError):
    """Raised when a required bundle file is absent."""


class InvalidJsonError(ImportValidationError):
    """Raised when a bundle file contains malformed JSON."""


class InvalidBundleObjectError(ImportValidationError):
    """Raised when a bundle file decodes to an unsupported top-level shape."""


class MissingRequiredKeyError(ImportValidationError):
    """Raised when a bundle payload is missing required keys."""


class UnsupportedContractVersionError(ImportValidationError):
    """Raised when a bundle contract version is not supported."""


class ContractConsistencyError(ImportValidationError):
    """Raised when bundle payloads disagree about core contract details."""


class VectorFixtureValidationError(ImportValidationError):
    """Raised when a local vector fixture cannot be loaded safely."""


class EvaluationArtifactValidationError(ImportValidationError):
    """Raised when a local evaluation artifact cannot be loaded safely."""
