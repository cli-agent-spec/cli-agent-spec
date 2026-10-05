"""Pin ManifestResponse schema behaviour for individual CommandEntry fields."""

from typing import Any

import pytest

import validate_schemas as vs


@pytest.fixture(scope="module")
def manifest_validator():
    schemas = vs.load_schemas()
    return vs.build_validators(schemas, vs.build_registry(schemas))["manifest-response.json"]


def manifest(**command_fields: Any) -> dict[str, Any]:
    command = {"description": "Run", "danger_level": "safe", "required_scopes": [], "flags": {}, "exit_codes": {}}
    command.update(command_fields)
    return {"schema_version": "3.17", "framework_version": "1", "etag": "x", "commands": {"run": command}}


def errors(validator, instance: dict[str, Any]) -> list[str]:
    return [e.message for e in validator.iter_errors(instance)]


def test_mcp_absent_is_valid(manifest_validator) -> None:
    assert errors(manifest_validator, manifest()) == []


def test_mcp_false_is_valid(manifest_validator) -> None:
    assert errors(manifest_validator, manifest(mcp=False)) == []


@pytest.mark.parametrize("value", [True, "false", 0, None])
def test_mcp_other_values_are_rejected(manifest_validator, value: object) -> None:
    assert errors(manifest_validator, manifest(mcp=value)) != []
