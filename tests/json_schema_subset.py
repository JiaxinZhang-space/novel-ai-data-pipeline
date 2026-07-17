"""Tiny standard-library validator for the JSON Schema subset used in contracts/.

This is intentionally a test helper, not a general JSON Schema implementation.
Supported keywords: type, required, properties, const, enum, pattern, items,
minItems, minLength, minimum, and the date format.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any


def _is_json_type(value: Any, expected: str) -> bool:
    checks = {
        "null": lambda item: item is None,
        "boolean": lambda item: isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float))
        and not isinstance(item, bool),
    }
    if expected not in checks:
        raise ValueError(f"unsupported JSON Schema type: {expected}")
    return checks[expected](value)


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without treating Python bool as integer."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if left is None or right is None:
        return left is right
    return left == right


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None:
        candidates = [expected_type] if isinstance(expected_type, str) else expected_type
        if not any(_is_json_type(instance, candidate) for candidate in candidates):
            return [
                f"{path}: expected type {candidates}, got {type(instance).__name__}"
            ]

    if "const" in schema and not _json_equal(instance, schema["const"]):
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and not any(
        _json_equal(instance, candidate) for candidate in schema["enum"]
    ):
        errors.append(f"{path}: value {instance!r} is not in enum {schema['enum']!r}")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        for key, child_schema in schema.get("properties", {}).items():
            if key in instance:
                errors.extend(validate(instance[key], child_schema, f"{path}.{key}"))

    if isinstance(instance, list):
        minimum_items = schema.get("minItems")
        if minimum_items is not None and len(instance) < minimum_items:
            errors.append(
                f"{path}: expected at least {minimum_items} items, got {len(instance)}"
            )
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(instance):
                errors.extend(validate(item, item_schema, f"{path}[{index}]"))

    if isinstance(instance, str):
        minimum_length = schema.get("minLength")
        if minimum_length is not None and len(instance) < minimum_length:
            errors.append(
                f"{path}: expected minimum length {minimum_length}, got {len(instance)}"
            )
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            errors.append(f"{path}: value {instance!r} does not match {pattern!r}")
        if schema.get("format") == "date":
            try:
                date.fromisoformat(instance)
            except ValueError:
                errors.append(f"{path}: value {instance!r} is not an ISO date")

    minimum = schema.get("minimum")
    if minimum is not None and isinstance(instance, (int, float)):
        if not isinstance(instance, bool) and instance < minimum:
            errors.append(f"{path}: value {instance} is below minimum {minimum}")

    return errors


def assert_valid(instance: Any, schema: dict[str, Any], label: str) -> None:
    errors = validate(instance, schema)
    if errors:
        preview = "\n".join(f"- {error}" for error in errors[:20])
        suffix = "" if len(errors) <= 20 else f"\n... {len(errors) - 20} more"
        raise AssertionError(f"{label} failed contract validation:\n{preview}{suffix}")

