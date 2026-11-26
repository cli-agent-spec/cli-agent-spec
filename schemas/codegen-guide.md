# Schema Code Generation Guide

> How to install and run the code generation tools that produce language-specific types from the CLI Agent Spec JSON Schema files.

---

## Overview

The schemas are JSON Schema draft-07 files. Two-step workflow for any language:

1. **Validate** — confirm the schema is well-formed with `ajv`
2. **Generate** — produce language-specific types with a codegen tool

The generators run on the six canonical schemas, the wire contracts listed under Canonical types in [`index.md`](index.md): `exit-code`, `exit-code-entry`, `response-envelope`, `manifest-response`, `dispatch-request`, `audit-log-entry`. Each command names the schema files rather than the `schemas/` directory, because the directory also holds the `.md` companions and the tooling schemas, which directory-input generators try to parse. Commands run from the repository root and write to a destination you choose. The `x-enum-varnames` and `x-enum-descriptions` vendor extensions are honoured by most tools to produce named enum constants with docstrings.

**Tested in CI.** Every install and generate command in Step 2 is the command CI runs: `scripts/codegen.py` holds them, the `codegen` job in `.github/workflows/validate.yml` runs them for each language and then compiles the output (`import` under Pydantic, `tsc --noEmit --strict`, `cargo check`, `go build`, `javac`), and `tests/test_codegen.py` fails when this guide's commands differ from the script's. From a checkout you can run the same steps:

```bash
uv run scripts/codegen.py install python
uv run scripts/codegen.py generate python --out tmp/codegen/python
uv run scripts/codegen.py compile python --out tmp/codegen/python
```

The tool versions below are the ones CI pins; newer versions usually work but are not tested here.

---

## Prerequisites (all languages)

**Node.js** (required for `ajv-cli` and TypeScript codegen):

```bash
# macOS
brew install node

# Ubuntu / Debian
sudo apt install nodejs npm

# Verify
node --version   # v22 or later recommended
npm --version
```

---

## Step 1 — Install and use `ajv-cli` (all languages)

`ajv-cli` validates JSON Schema files and your generated output against the schemas. Install it once regardless of which language you target.

```bash
npm install -g ajv-cli@5

# Verify
ajv help
```

`--strict=false` is required: the schemas carry `x-enum-varnames` and related `x-` annotations for code generators, which ajv strict mode rejects as unknown keywords.

**Validate a schema file:**

```bash
ajv validate -s schemas/response-envelope.json -d output.json --spec=draft7 --strict=false

# Manifest output references ExitCodeEntry; load it with -r
ajv validate -s schemas/manifest-response.json -r schemas/exit-code-entry.json -d manifest.json --spec=draft7 --strict=false
```

**Validate all schemas are well-formed:**

```bash
ajv compile -s "schemas/*.json" --spec=draft7 --strict=false
```

---

## Step 2 — Generate bindings

Pick the section for your language.

---

### Python

**Tool:** `datamodel-code-generator`
**Output:** Pydantic v2 models (or dataclasses — configurable), one module per schema

**Install** (`pip install datamodel-code-generator==0.102.0` works too):

```bash
uv tool install datamodel-code-generator==0.102.0

# Verify
datamodel-codegen --version
```

**Generate:**

```bash
mkdir -p src/models
datamodel-codegen --input schemas/exit-code.json --input-file-type jsonschema --output src/models/exit_code.py \
  --output-model-type pydantic_v2.BaseModel --use-annotated --enum-field-as-literal all
datamodel-codegen --input schemas/exit-code-entry.json --input-file-type jsonschema --output src/models/exit_code_entry.py \
  --output-model-type pydantic_v2.BaseModel --use-annotated --enum-field-as-literal all
datamodel-codegen --input schemas/response-envelope.json --input-file-type jsonschema --output src/models/response_envelope.py \
  --output-model-type pydantic_v2.BaseModel --use-annotated --enum-field-as-literal all
datamodel-codegen --input schemas/manifest-response.json --input-file-type jsonschema --output src/models/manifest_response.py \
  --output-model-type pydantic_v2.BaseModel --use-annotated --enum-field-as-literal all
datamodel-codegen --input schemas/dispatch-request.json --input-file-type jsonschema --output src/models/dispatch_request.py \
  --output-model-type pydantic_v2.BaseModel --use-annotated --enum-field-as-literal all
datamodel-codegen --input schemas/audit-log-entry.json --input-file-type jsonschema --output src/models/audit_log_entry.py \
  --output-model-type pydantic_v2.BaseModel --use-annotated --enum-field-as-literal all
```

`manifest_response.py` inlines the `ExitCodeEntry` model it references, so each module imports on its own.

**Options:**

| Flag | Effect |
|------|--------|
| `--output-model-type pydantic_v2.BaseModel` | Pydantic v2 (default: v1) |
| `--output-model-type dataclasses.dataclass` | stdlib dataclasses, no Pydantic dependency |
| `--use-annotated` | Uses `Annotated[str, Field(...)]` style |
| `--enum-field-as-literal all` | `Literal["none","partial","complete"]` for small enums |
| `--use-standard-collections` | `list[str]` instead of `List[str]` (Python 3.9+) |

**Vendor extension support:** `x-enum-varnames` is used to name enum members when `--enum-field-as-literal` is not set.

---

### TypeScript

**Tool:** `json-schema-to-typescript`

**Install:**

```bash
npm install -g json-schema-to-typescript@16.0.0

# Verify
json2ts --help
```

**Generate** (one `.ts` file per schema; `$ref` resolves against the schema file's directory):

```bash
mkdir -p src/types
json2ts --input schemas/exit-code.json --output src/types/exit-code.ts --bannerComment ""
json2ts --input schemas/exit-code-entry.json --output src/types/exit-code-entry.ts --bannerComment ""
json2ts --input schemas/response-envelope.json --output src/types/response-envelope.ts --bannerComment ""
json2ts --input schemas/manifest-response.json --output src/types/manifest-response.ts --bannerComment ""
json2ts --input schemas/dispatch-request.json --output src/types/dispatch-request.ts --bannerComment ""
json2ts --input schemas/audit-log-entry.json --output src/types/audit-log-entry.ts --bannerComment ""
```

**Options:**

| Flag | Effect |
|------|--------|
| `--bannerComment ""` | Suppresses the auto-generated file header |
| `--no-additionalProperties` | Adds `[k: string]: unknown` index signatures by default — disable if schemas use `additionalProperties: false` |
| `--unreachableDefinitions` | Include `$defs` not referenced by any `$ref` |

**Vendor extension support:** `x-enum-varnames` is used to name TypeScript enum members. `x-enum-descriptions` is emitted as JSDoc `/** */` comments on each member.

---

### Rust

**Tool:** `typify` (via `cargo-typify` CLI)
**Output:** Rust structs with `serde` derive macros

**Prerequisites:**

```bash
# Install Rust toolchain if not present (cargo-typify needs rustfmt, which rustup installs)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify
cargo --version
```

**Install:**

```bash
cargo install cargo-typify@0.10.2 --locked

# Verify
cargo typify --version
```

**Generate:**

```bash
mkdir -p src/types
cargo typify schemas/exit-code.json --output src/types/exit_code.rs
cargo typify schemas/exit-code-entry.json --output src/types/exit_code_entry.rs
cargo typify schemas/response-envelope.json --output src/types/response_envelope.rs
cargo typify schemas/manifest-response.json --output src/types/manifest_response.rs
cargo typify schemas/dispatch-request.json --output src/types/dispatch_request.rs
cargo typify schemas/audit-log-entry.json --output src/types/audit_log_entry.rs
```

**`Cargo.toml` dependencies** (add before compiling generated code):

```toml
[dependencies]
chrono = { version = "0.4", features = ["serde"] }
regress = "0.12"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

`regress` backs the `pattern` keywords and `chrono` the `date-time` formats.

**Note:** `typify` does not support directory input — process files individually. The `x-enum-varnames` extension is used to name enum variants.

---

### Go

**Tool:** `go-jsonschema`

**Prerequisites:**

```bash
# Install Go toolchain if not present: https://go.dev/dl/
go version  # 1.25 or later (go-jsonschema v0.24 requires it)
```

**Install:**

```bash
go install github.com/atombender/go-jsonschema@v0.24.1

# Verify (binary lands in $GOPATH/bin or $HOME/go/bin)
go-jsonschema --help
```

**Add `$GOPATH/bin` to `PATH` if not already:**

```bash
export PATH="$PATH:$(go env GOPATH)/bin"
# Add to ~/.zshrc or ~/.bashrc to persist
```

**Generate** (all schemas in one invocation, so types shared through `$ref` are declared once):

```bash
mkdir -p pkg/framework
go-jsonschema --package framework --output pkg/framework/types.go \
  schemas/exit-code.json schemas/exit-code-entry.json schemas/response-envelope.json \
  schemas/manifest-response.json schemas/dispatch-request.json schemas/audit-log-entry.json
```

The output imports `github.com/go-viper/mapstructure/v2`; run `go mod tidy` in your module before `go build`.

**Options:**

| Flag | Effect |
|------|--------|
| `--package <name>` | Go package name for the output file |
| `--output <file>` | Output file (default: `-`, standard output) |
| `--tags json` | Struct tags to emit (default: `json,yaml,mapstructure`) |

**Note:** `go-jsonschema` does not honour `x-enum-varnames` — enum values are generated as `const` blocks using the schema `enum` values directly.

---

### Java

**Tool:** `jsonschema2pojo`
**Output:** Java POJOs with Jackson annotations

**Prerequisites:**

```bash
# Java 11 or later required
java --version
```

**Install** (`brew install jsonschema2pojo` on macOS, or the release archive, which is what CI runs; `--exclude '._*'` drops the archive's macOS metadata files, which are not jars):

```bash
mkdir -p "$HOME/.local/share/jsonschema2pojo" "$HOME/.local/bin"
curl -fsSL https://github.com/joelittlejohn/jsonschema2pojo/releases/download/jsonschema2pojo-1.3.3/jsonschema2pojo-1.3.3.tar.gz | tar -xz --strip-components=1 --exclude '._*' -C "$HOME/.local/share/jsonschema2pojo"
ln -sf "$HOME/.local/share/jsonschema2pojo/bin/jsonschema2pojo" "$HOME/.local/bin/jsonschema2pojo"

# Verify
jsonschema2pojo --version
```

**Generate:**

```bash
mkdir -p src/main/java
jsonschema2pojo --source schemas/exit-code.json schemas/exit-code-entry.json schemas/response-envelope.json \
  schemas/manifest-response.json schemas/dispatch-request.json schemas/audit-log-entry.json \
  --target src/main/java --package com.example.framework --annotation-style JACKSON2 \
  --generate-builders --target-version 11
```

The generated classes need `jackson-annotations` 2.x on the classpath to compile.

**Options:**

| Flag | Effect |
|------|--------|
| `--annotation-style JACKSON2` | Jackson 2.x `@JsonProperty` annotations |
| `--generate-builders` | Produces builder pattern constructors |
| `--target-version 11` | Emits `javax.annotation.processing.Generated`, which the JDK ships (the default 1.6 target needs the separate `javax.annotation-api` jar) |
| `--enable-additional-properties` | Adds a `Map<String,Object> additionalProperties` field to every type, whatever the schema says (off by default) |
| `--use-inner-class-builders` | Builder as inner `Builder` class |

**Maven plugin alternative** (add to `pom.xml`):

```xml
<plugin>
  <groupId>org.jsonschema2pojo</groupId>
  <artifactId>jsonschema2pojo-maven-plugin</artifactId>
  <version>1.3.3</version>
  <configuration>
    <sourcePaths>
      <sourcePath>${basedir}/schemas/exit-code.json</sourcePath>
      <sourcePath>${basedir}/schemas/exit-code-entry.json</sourcePath>
      <sourcePath>${basedir}/schemas/response-envelope.json</sourcePath>
      <sourcePath>${basedir}/schemas/manifest-response.json</sourcePath>
      <sourcePath>${basedir}/schemas/dispatch-request.json</sourcePath>
      <sourcePath>${basedir}/schemas/audit-log-entry.json</sourcePath>
    </sourcePaths>
    <targetPackage>com.example.framework</targetPackage>
    <annotationStyle>jackson2</annotationStyle>
    <generateBuilders>true</generateBuilders>
    <targetVersion>11</targetVersion>
  </configuration>
</plugin>
```

---

## Validation after generation

After generating, validate the invariants manually or via test — code generators do not enforce the `if/then` constraint in `ExitCodeEntry`:

> `retryable: true` **implies** `side_effects: "none"`

**Python (Pydantic v2):**

```python
from pydantic import model_validator
# Add to ExitCodeEntry after generation:
@model_validator(mode="after")
def check_retryable_invariant(self) -> "ExitCodeEntry":
    if self.retryable and self.side_effects != SideEffects.none:
        raise ValueError("retryable=True requires side_effects='none'")
    return self
```

**TypeScript:**

```typescript
function validateExitCodeEntry(e: ExitCodeEntry): void {
  if (e.retryable && e.sideEffects !== "none") {
    throw new Error("retryable=true requires side_effects='none'");
  }
}
```

---

## Quick reference

| Language | Tool | Install | Generate |
|----------|------|---------|----------|
| Any | `ajv-cli` | `npm install -g ajv-cli@5` | `ajv validate -s schemas/... -d output.json --spec=draft7 --strict=false` |
| Python | `datamodel-code-generator` | `uv tool install datamodel-code-generator==0.102.0` | `datamodel-codegen --input schemas/<name>.json --input-file-type jsonschema --output src/models/<name>.py` |
| TypeScript | `json-schema-to-typescript` | `npm install -g json-schema-to-typescript@16.0.0` | `json2ts --input schemas/<name>.json --output src/types/<name>.ts` |
| Rust | `cargo-typify` | `cargo install cargo-typify@0.10.2 --locked` | `cargo typify schemas/<name>.json --output src/types/<name>.rs` |
| Go | `go-jsonschema` | `go install github.com/atombender/go-jsonschema@v0.24.1` | `go-jsonschema --package framework --output types.go schemas/<name>.json ...` |
| Java | `jsonschema2pojo` | `brew install jsonschema2pojo` | `jsonschema2pojo --source schemas/<name>.json ... --target src/main/java/` |
