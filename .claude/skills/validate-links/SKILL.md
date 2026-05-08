---
name: validate-links
description: Validate all cross-links in the CLI Agent Spec specification — broken file links, missing schema sections, and schema↔requirement symmetry. Use when files have been added or edited, or to check the project is internally consistent.
allowed-tools: Bash
license: MIT
compatibility: Requires git and a POSIX shell (bash/zsh). Designed for the cli-agent-spec repository.
---

# Validate Cross-Links

Run the scripts below in order. Report every failure found. If all checks pass, confirm with a summary of what was checked and how many links were verified.

Each script detects the project root via `git rev-parse --show-toplevel`, falling back to the current directory if not in a git repo.

---

## Script 1 — Broken file links in all markdown files

Extracts every relative link from every `.md` file and checks the target exists.

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd) && cd "$ROOT" && ERRORS=0
while IFS= read -r mdfile; do
  while IFS= read -r link; do
    target="$(dirname "$mdfile")/$link"
    resolved=$(python3 -c "import os,sys; print(os.path.normpath(sys.argv[1]))" "$target")
    if [ ! -e "$resolved" ]; then
      echo "BROKEN: $mdfile -> $link"
      ERRORS=$((ERRORS + 1))
    fi
  done < <(perl -ne 'if (/^```/) { $in_code = !$in_code; next } next if $in_code; while (/\[[^\]]*\]\(([^)#]+)\)/g) { print "$1\n" }' "$mdfile" \
           | grep -v '^http' | grep -v '^mailto')
done < <(find "$ROOT" -name "*.md" \
           -not -path "*/.git/*" \
           -not -path "*/node_modules/*" \
           -not -path "*/.claude/plugins/*")
echo "---"
echo "Broken links: $ERRORS"
```

---

## Script 2 — Schema ↔ requirement symmetry

**Direction 1:** For each schema `.md` "Used by" requirement → that requirement must have a `## Schema` link back to this schema's `.json`.

**Direction 2:** For each requirement's `## Schema` link → that schema's `.md` "Used by" must include this requirement.

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd) && cd "$ROOT" && ERRORS=0

echo "=== Direction 1: Schema 'Used by' -> Requirement '## Schema' ==="
for schema_md in "$ROOT"/schemas/*.md; do
  base=$(basename "$schema_md")
  [[ "$base" == "index.md" || "$base" == "codegen-guide.md" ]] && continue
  schema_json="${base%.md}.json"

  while IFS= read -r req_id; do
    [ -z "$req_id" ] && continue
    tier=$(echo "$req_id" | perl -ne '/REQ-([A-Z])-\d+/ && print lc($1)')
    num=$(echo "$req_id"  | perl -ne '/REQ-[A-Z]-(\d+)/ && print $1+0')
    req_file=$(find "$ROOT/requirements" -name "${tier}-$(printf '%03d' $num)-*.md" 2>/dev/null | head -1)

    if [ -z "$req_file" ]; then
      echo "MISSING FILE: $base says 'Used by $req_id' but no matching file in requirements/"
      ERRORS=$((ERRORS + 1))
      continue
    fi
    schema_base="${schema_json%.json}"
    grep -qE "${schema_base}\.(json|md)" "$req_file" || {
      echo "MISSING BACK-LINK: $req_id has no link to $schema_base.json or $schema_base.md  (schema: $base)"
      ERRORS=$((ERRORS + 1))
    }
  done < <(grep "Used by" "$schema_md" \
             | perl -ne 'while (/(REQ-[A-Z]-\d+)/g) { print "$1\n" }')
done

echo ""
echo "=== Direction 2: Requirement '## Schema' -> Schema 'Used by' ==="
for req_file in "$ROOT"/requirements/[fco]-*.md; do
  req_id=$(perl -ne '/(REQ-[A-Z]-\d+)/ && print "$1\n" && exit' "$req_file")
  [ -z "$req_id" ] && continue

  # Extract content of ## Schema section only
  schema_section=$(awk '/^## Schema/{found=1; next} /^## /{found=0} found{print}' "$req_file")
  [ -z "$schema_section" ] && continue

  while IFS= read -r schema_md_name; do
    [ -z "$schema_md_name" ] && continue
    schema_md="$ROOT/schemas/$schema_md_name"
    if [ ! -f "$schema_md" ]; then
      echo "MISSING SCHEMA FILE: $req_id links to $schema_md_name but schemas/$schema_md_name not found"
      ERRORS=$((ERRORS + 1))
      continue
    fi
    grep -q "$req_id" "$schema_md" || {
      echo "MISSING BACK-LINK: $schema_md_name 'Used by' does not include $req_id"
      ERRORS=$((ERRORS + 1))
    }
  done < <(echo "$schema_section" \
             | perl -ne 'while (/\b([\w-]+\.md)\b/g) { print "$1\n" }' \
             | grep -v "^index\." | grep -v "^codegen-" | sort -u)
done

echo "---"
echo "Symmetry errors: $ERRORS"
```

---

## Script 3 — Index completeness

Every file listed in `requirements/index.md` and `schemas/index.md` must exist, and every file in those directories must be listed.

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd) && cd "$ROOT" && ERRORS=0

echo "=== requirements/index.md ==="

# Every .md linked from index must exist
while IFS= read -r fname; do
  [ -f "$ROOT/requirements/$fname" ] || {
    echo "MISSING: index links to $fname but file not found"
    ERRORS=$((ERRORS + 1))
  }
done < <(perl -ne 'while (/\(([\w-]+\.md)\)/g) { print "$1\n" }' \
           "$ROOT/requirements/index.md")

# Every requirement file must appear in index
for req_file in "$ROOT"/requirements/[fco]-*.md; do
  fname=$(basename "$req_file")
  grep -q "$fname" "$ROOT/requirements/index.md" || {
    echo "UNLISTED: $fname not in requirements/index.md"
    ERRORS=$((ERRORS + 1))
  }
done

echo ""
echo "=== schemas/index.md ==="

# Every .json linked from index must exist
while IFS= read -r fname; do
  [ -f "$ROOT/schemas/$fname" ] || {
    echo "MISSING: index links to $fname but file not found"
    ERRORS=$((ERRORS + 1))
  }
done < <(perl -ne 'while (/\(([\w-]+\.json)\)/g) { print "$1\n" }' \
           "$ROOT/schemas/index.md")

# Every schema .json must appear in index
for schema_file in "$ROOT"/schemas/*.json; do
  fname=$(basename "$schema_file")
  grep -q "$fname" "$ROOT/schemas/index.md" || {
    echo "UNLISTED: $fname not in schemas/index.md"
    ERRORS=$((ERRORS + 1))
  }
done

echo "---"
echo "Index errors: $ERRORS"
```

---

## Script 4 — Content completeness

Reports how many challenge and requirement files have all required sections. This is a progress metric, not a hard error — incomplete files are expected during authoring. Files with missing sections are listed so authors know what remains.

**Challenge required sections** (in order): `### The Problem` · `### Impact` · `### Solutions` · `### Evaluation` · `### Agent Workaround`

**Requirement required sections** (in order): `## Description` · `## Acceptance Criteria` · `## Schema` · `## Wire Format` · `## Example` · `## Related`

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd) && cd "$ROOT"

check_sections() {
  local f="$1"; shift; local missing=""
  for section in "$@"; do
    grep -q "^$section" "$f" || missing="${missing}\"${section}\" "
  done
  echo "$missing"
}

CHALLENGE_TOTAL=0; CHALLENGE_COMPLETE=0
REQ_TOTAL=0; REQ_COMPLETE=0

echo "=== Challenge completeness ==="
for f in "$ROOT"/challenges/*/*.md; do
  fname=$(basename "$f")
  [[ "$fname" == "index.md" ]] && continue
  grep -q "MERGED" "$f" && continue
  CHALLENGE_TOTAL=$((CHALLENGE_TOTAL + 1))
  missing=$(check_sections "$f" \
    "### The Problem" "### Impact" "### Solutions" "### Evaluation" "### Agent Workaround")
  if [ -z "$missing" ]; then
    CHALLENGE_COMPLETE=$((CHALLENGE_COMPLETE + 1))
  else
    echo "INCOMPLETE: $fname — missing: $missing"
  fi
done
echo "Complete: $CHALLENGE_COMPLETE / $CHALLENGE_TOTAL challenges"

echo ""
echo "=== Requirement completeness ==="
for f in "$ROOT"/requirements/[fco]-*.md; do
  fname=$(basename "$f")
  REQ_TOTAL=$((REQ_TOTAL + 1))
  missing=$(check_sections "$f" \
    "## Description" "## Acceptance Criteria" "## Schema" "## Wire Format" "## Example" "## Related")
  if [ -z "$missing" ]; then
    REQ_COMPLETE=$((REQ_COMPLETE + 1))
  else
    echo "INCOMPLETE: $fname — missing: $missing"
  fi
done
echo "Complete: $REQ_COMPLETE / $REQ_TOTAL requirements"
```

---

## Script 5 — Counter consistency

Counts actual challenge and requirement files on disk and compares to the declared numbers in key prose files. Reports any mismatch as an error.

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd) && cd "$ROOT" && ERRORS=0

ACTUAL_CHALLENGES=$(find "$ROOT/challenges" -name "*.md" -not -name "index.md" -not -name "checklist.md" -not -name "sources.md" | xargs grep -L "MERGED" 2>/dev/null | wc -l | tr -d ' ')
ACTUAL_REQS=$(ls "$ROOT"/requirements/[fco]-*.md 2>/dev/null | wc -l | tr -d ' ')

echo "Actual on disk: $ACTUAL_CHALLENGES challenges, $ACTUAL_REQS requirements"
echo ""

check_count() {
  local file="$1" pattern="$2" expected="$3" label="$4"
  local found
  found=$(grep -oE "$pattern" "$file" | head -1)
  if [ -z "$found" ]; then
    echo "NOT FOUND: $label pattern '$pattern' not matched in $file"
    ERRORS=$((ERRORS + 1))
  elif [ "$found" != "$expected" ]; then
    echo "STALE: $file — '$label' says $found but actual is $expected"
    ERRORS=$((ERRORS + 1))
  fi
}

# challenges/index.md
check_count "$ROOT/challenges/index.md"    "All [0-9]+ failure modes"      "All $ACTUAL_CHALLENGES failure modes"      "header"
check_count "$ROOT/challenges/index.md"    "[0-9]+ active failure modes"   "$ACTUAL_CHALLENGES active failure modes"   "footer"

# challenges/checklist.md
check_count "$ROOT/challenges/checklist.md" "[0-9]+ documented failure modes" \
  "$ACTUAL_CHALLENGES documented failure modes" "header"

# requirements/index.md
check_count "$ROOT/requirements/index.md"  "[0-9]+ documented failure modes" \
  "$ACTUAL_CHALLENGES documented failure modes" "intro"
check_count "$ROOT/requirements/index.md"  "\*\*[0-9]+ total\*\*"      "**$ACTUAL_REQS total**"                 "total"

# README.md
check_count "$ROOT/README.md"  "\*\*[0-9]+ failure modes\*\*"   "**$ACTUAL_CHALLENGES failure modes**"  "failure modes bullet"
check_count "$ROOT/README.md"  "\*\*[0-9]+ requirements\*\*" "**$ACTUAL_REQS requirements**"      "requirements bullet"

# CLAUDE.md
check_count "$ROOT/CLAUDE.md"  "[0-9]+ failure modes, [0-9]+ requirements" \
  "$ACTUAL_CHALLENGES failure modes, $ACTUAL_REQS requirements" "what this repo is"

echo "---"
echo "Counter errors: $ERRORS"
```

---

## Output format

After all five scripts, report:

```
## Link validation results

### Broken file links      — N errors
### Schema ↔ req symmetry  — N errors
### Index completeness     — N errors
### Content completeness   — N/71 failure modes · N/154 requirements fully authored
### Counter consistency    — N errors

Total: N errors  (completeness is informational, not an error count)
```

List every error with the file it came from. For each error suggest the fix:
- `BROKEN` → update the link or create the missing file
- `MISSING BACK-LINK` → add `## Schema` to the requirement or add the requirement to schema "Used by"
- `MISSING FILE` → create the file or remove the stale reference
- `UNLISTED` → add a row to the index
- `INCOMPLETE` → add the missing section(s) to the file; see CLAUDE.md for required section order
- `STALE` → update the counter to match the actual file count on disk
- `NOT FOUND` → the expected counter pattern was not found; the file may have been restructured
