"""Pin ManifestResponse schema behaviour for individual CommandEntry, FlagEntry, and PositionalEntry fields."""

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


def flag(**fields: Any) -> dict[str, Any]:
    return manifest(flags={"sig-type": {"required": False, "description": "Signature type", **fields}})


def positional(**fields: Any) -> dict[str, Any]:
    return manifest(positionals=[{"name": "level", "required": True, "description": "Level", **fields}])


ENTRY_BUILDERS = [pytest.param(flag, id="flag"), pytest.param(positional, id="positional")]


@pytest.mark.parametrize("build", ENTRY_BUILDERS)
def test_integer_entry_accepts_integer_enum_values(manifest_validator, build) -> None:
    assert errors(manifest_validator, build(type="integer", enum_values=[0, 1, 2])) == []


@pytest.mark.parametrize("build", ENTRY_BUILDERS)
def test_integer_entry_without_enum_values_stays_valid(manifest_validator, build) -> None:
    assert errors(manifest_validator, build(type="integer")) == []


@pytest.mark.parametrize("build", ENTRY_BUILDERS)
def test_integer_entry_rejects_string_enum_values(manifest_validator, build) -> None:
    assert errors(manifest_validator, build(type="integer", enum_values=["0", "1", "2"])) != []


@pytest.mark.parametrize("build", ENTRY_BUILDERS)
def test_integer_entry_rejects_non_integer_numbers(manifest_validator, build) -> None:
    assert errors(manifest_validator, build(type="integer", enum_values=[0, 1.5])) != []


@pytest.mark.parametrize("build", ENTRY_BUILDERS)
def test_enum_entry_keeps_string_enum_values(manifest_validator, build) -> None:
    assert errors(manifest_validator, build(type="enum", enum_values=["fast", "safe"])) == []


@pytest.mark.parametrize("build", ENTRY_BUILDERS)
def test_enum_entry_rejects_integer_enum_values(manifest_validator, build) -> None:
    assert errors(manifest_validator, build(type="enum", enum_values=[0, 1, 2])) != []


@pytest.mark.parametrize("build", ENTRY_BUILDERS)
def test_string_entry_rejects_integer_enum_values(manifest_validator, build) -> None:
    assert errors(manifest_validator, build(type="string", enum_values=[0, 1])) != []


def test_positional_enum_still_requires_enum_values(manifest_validator) -> None:
    assert errors(manifest_validator, positional(type="enum")) != []


def test_media_types_still_require_an_enum_flag(manifest_validator) -> None:
    root_format = {"type": "integer", "required": False, "description": "Format", "enum_values": [0, 1], "media_types": {"0": "text/html"}}
    instance = manifest()
    instance["flags"] = {"format": root_format}
    assert errors(manifest_validator, instance) != []
