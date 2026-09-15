# Schema Code Generation Guide

> How to install and run the code generation tools that produce language-specific types from the CLI Agent Spec JSON Schema files.

---

## Overview

The schemas are JSON Schema draft-07 files. Two-step workflow for any language:

1. **Validate** — confirm the schema is well-formed with `ajv`
2. **Generate** — produce language-specific types with a codegen tool

All tools read from `schemas/` and write to a destination you specify. The `x-enum-varnames` and `x-enum-descriptions` vendor extensions are honoured by most tools to produce named enum constants with docstrings.

---

## Prerequisites (all languages)

**Node.js** (required for `ajv-cli` and TypeScript codegen):

```bash
# macOS
brew install node

# Ubuntu / Debian
sudo apt install nodejs npm

# Verify
node --version   # v18 or later recommended
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
**Output:** Pydantic v2 models (or dataclasses — configurable)

**Install:**

```bash
pip install datamodel-code-generator

# Verify
datamodel-codegen --version
```

**Generate:**

```bash
datamodel-codegen \
  --input schemas/ \
  --input-file-type jsonschema \
  --output src/models/ \
  --output-model-type pydantic_v2.BaseModel \
  --use-annotated \
  --enum-field-as-literal all
```

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
npm install -g json-schema-to-typescript

# Verify
json2ts --version
```

**Generate:**

```bash
json2ts \
  --input schemas/ \
  --output src/types/ \
  --bannerComment ""
```

**Options:**

| Flag | Effect |
|------|--------|
| `--bannerComment ""` | Suppresses the auto-generated file header |
| `--no-additionalProperties` | Adds `[k: string]: unknown` index signatures by default — disable if schemas use `additionalProperties: false` |
| `--unreachableDefinitions` | Include `$defs` not referenced by any `$ref` |

**Vendor extension support:** `x-enum-varnames` is used to name TypeScript enum members. `x-enum-descriptions` is emitted as JSDoc `/** */` comments on each member.

**Per-file alternative** (useful to control output filenames):

```bash
json2ts --input schemas/exit-code.json       --output src/types/exit-code.ts
json2ts --input schemas/exit-code-entry.json --output src/types/exit-code-entry.ts
json2ts --input schemas/response-envelope.json --output src/types/response-envelope.ts
json2ts --input schemas/manifest-response.json --output src/types/manifest-response.ts
```

---

### Rust

**Tool:** `typify` (via `cargo-typify` CLI)
**Output:** Rust structs with `serde` derive macros

**Prerequisites:**

```bash
# Install Rust toolchain if not present
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify
cargo --version
```

**Install:**

```bash
cargo install cargo-typify

# Verify
cargo typify --version
```

**Generate:**

```bash
cargo typify schemas/exit-code-entry.json         > src/types/exit_code_entry.rs
cargo typify schemas/exit-code.json               > src/types/exit_code.rs
cargo typify schemas/response-envelope.json        > src/types/response_envelope.rs
cargo typify schemas/manifest-response.json        > src/types/manifest_response.rs
```

**`Cargo.toml` dependencies** (add before compiling generated code):

```toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

**Note:** `typify` does not support directory input — process files individually. The `x-enum-varnames` extension is used to name enum variants.

---

### Go

**Tool:** `go-jsonschema`

**Prerequisites:**

```bash
# Install Go toolchain if not present: https://go.dev/dl/
go version  # 1.21 or later recommended
```

**Install:**

```bash
go install github.com/atombender/go-jsonschema@latest

# Verify (binary lands in $GOPATH/bin or $HOME/go/bin)
go-jsonschema --version
```

**Add `$GOPATH/bin` to `PATH` if not already:**

```bash
export PATH="$PATH:$(go env GOPATH)/bin"
# Add to ~/.zshrc or ~/.bashrc to persist
```

**Generate:**

```bash
go-jsonschema \
  --package framework \
  --output-name types.go \
  schemas/exit-code.json \
  schemas/exit-code-entry.json \
  schemas/response-envelope.json \
  schemas/manifest-response.json \
  > pkg/framework/types.go
```

**Options:**

| Flag | Effect |
|------|--------|
| `--package <name>` | Go package name for the output file |
| `--output-name <file>` | Output filename (default: based on schema `$id`) |
| `--tags json,yaml` | Struct tags to emit (default: `json`) |

**Note:** `go-jsonschema` does not honour `x-enum-varnames` — enum values are generated as `const` blocks using the schema `enum` values directly.

---

### Java

**Tool:** `jsonschema2pojo`
**Output:** Java POJOs with Jackson annotations

**Prerequisites:**

```bash
# Java 11 or later required
java --version

# Homebrew install (macOS)
brew install jsonschema2pojo

# Or download the CLI jar directly:
# https://github.com/joelittlejohn/jsonschema2pojo/releases/latest
# → jsonschema2pojo-<version>-release.tar.gz → bin/jsonschema2pojo
```

**Verify:**

```bash
jsonschema2pojo --version
# or: java -jar jsonschema2pojo-cli.jar --version
```

**Generate:**

```bash
jsonschema2pojo \
  --source schemas/ \
  --target src/main/java/ \
  --package com.example.framework \
  --annotation-style JACKSON2 \
  --generate-builders \
  --include-additional-properties false
```

**Options:**

| Flag | Effect |
|------|--------|
| `--annotation-style JACKSON2` | Jackson 2.x `@JsonProperty` annotations |
| `--generate-builders` | Produces builder pattern constructors |
| `--include-additional-properties false` | No `Map<String,Object> additionalProperties` field (matches `additionalProperties: false` schemas) |
| `--use-inner-class-builders` | Builder as inner `Builder` class |

**Maven plugin alternative** (add to `pom.xml`):

```xml
<plugin>
  <groupId>org.jsonschema2pojo</groupId>
  <artifactId>jsonschema2pojo-maven-plugin</artifactId>
  <version>1.2.1</version>
  <configuration>
    <sourceDirectory>${basedir}/schemas</sourceDirectory>
    <targetPackage>com.example.framework</targetPackage>
    <annotationStyle>jackson2</annotationStyle>
    <generateBuilders>true</generateBuilders>
    <includeAdditionalProperties>false</includeAdditionalProperties>
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
| Python | `datamodel-code-generator` | `pip install datamodel-code-generator` | `datamodel-codegen --input schemas/ --output src/models/` |
| TypeScript | `json-schema-to-typescript` | `npm install -g json-schema-to-typescript` | `json2ts --input schemas/ --output src/types/` |
| Rust | `cargo-typify` | `cargo install cargo-typify` | `cargo typify schemas/<name>.json > src/types/<name>.rs` |
| Go | `go-jsonschema` | `go install github.com/atombender/go-jsonschema@latest` | `go-jsonschema --package framework schemas/*.json > types.go` |
| Java | `jsonschema2pojo` | `brew install jsonschema2pojo` | `jsonschema2pojo --source schemas/ --target src/main/java/` |
