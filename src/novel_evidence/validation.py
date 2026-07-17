"""Rights and record-shape validation."""

from __future__ import annotations

from datetime import date
from typing import Any

from .constants import RIGHTS_AS_OF


RAW_REQUIRED_FIELDS = {
    "record_id",
    "source_id",
    "document_id",
    "rights_record_id",
    "ingest_sequence",
    "source_uri",
    "source_type",
    "author_id",
    "work_id",
    "title",
    "language",
    "text",
    "rights",
    "demo",
    "demo_marker",
}


def validate_raw_record(record: dict[str, Any]) -> list[str]:
    errors = [f"missing:{field}" for field in sorted(RAW_REQUIRED_FIELDS - record.keys())]
    if record.get("demo") is not True:
        errors.append("demo_must_be_true")
    if not isinstance(record.get("text"), str) or not record.get("text", "").strip():
        errors.append("text_must_be_nonempty_string")
    if not isinstance(record.get("rights"), dict):
        errors.append("rights_must_be_object")
    return errors


def validate_rights(
    record: dict[str, Any],
    *,
    as_of: date | None = None,
) -> list[str]:
    rights = record.get("rights") or {}
    effective_date = as_of or date.fromisoformat(RIGHTS_AS_OF)
    errors: list[str] = []

    if rights.get("status") != "active":
        errors.append("rights_status_not_active")
    if rights.get("consent_confirmed") is not True:
        errors.append("consent_not_confirmed")
    if not rights.get("contract_id"):
        errors.append("missing_contract_id")

    scopes = set(rights.get("license_scope") or [])
    if not {"training", "evaluation"}.issubset(scopes):
        errors.append("scope_missing_training_or_evaluation")

    try:
        valid_from = date.fromisoformat(str(rights.get("valid_from")))
        valid_until = date.fromisoformat(str(rights.get("valid_until")))
        if not valid_from <= effective_date <= valid_until:
            errors.append("license_outside_validity_window")
    except ValueError:
        errors.append("invalid_license_date")
    return errors


def partition_by_rights(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda row: row["ingest_sequence"]):
        shape_errors = validate_raw_record(record)
        rights_errors = validate_rights(record) if not shape_errors else []
        errors = shape_errors + rights_errors
        if errors:
            rejected.append(
                {
                    **record,
                    "rejection_stage": "rights_validation",
                    "rejection_reason": errors[0],
                    "validation_errors": errors,
                }
            )
        else:
            accepted.append(record)
    return accepted, rejected
