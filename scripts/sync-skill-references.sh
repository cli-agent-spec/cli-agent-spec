#!/usr/bin/env bash
# sync-skill-references.sh
#
# Copies spec content from the repo root into the bundled references/ directories
# inside each distributable skill. Installed skills cannot follow symlinks out of
# their own directory, so the bundles are real copies and must be re-synced after
# editing challenges, requirements, schemas, guides, IMPLEMENTING.md, or AGENTS.md.
#
# Usage: scripts/sync-skill-references.sh [--dry-run | --check]
#   --dry-run  print what would be copied
#   --check    exit 1 if any bundle differs from the repo root (used by CI)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE=sync

for arg in "$@"; do
  case "$arg" in
    --dry-run) MODE=dry-run ;;
    --check) MODE=check ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

DRIFT=0

copy() {
  local src="$1" dst="$2"
  case "$MODE" in
    dry-run)
      echo "[dry-run] rsync $src -> $dst"
      ;;
    check)
      local changes
      # diff, not rsync --dry-run: macOS openrsync itemizes identical files as transfers
      changes=$(diff -rq "$src" "$dst" 2>&1 || true)
      if [[ -n "$changes" ]]; then
        echo "DRIFT: ${dst#"$REPO_ROOT"/} differs from ${src#"$REPO_ROOT"/}"
        echo "$changes" | sed 's/^/  /' | head -20
        DRIFT=1
      fi
      ;;
    sync)
      mkdir -p "$(dirname "$dst")"
      rsync -a --delete "$src" "$dst"
      echo "synced: ${src#"$REPO_ROOT"/} -> ${dst#"$REPO_ROOT"/}"
      ;;
  esac
}

# cli-agent-evaluate: bundles challenges/ (audit, evaluate-batch, readiness, report symlink to it)
copy "$REPO_ROOT/challenges/" \
     "$REPO_ROOT/skills/cli-agent-evaluate/references/challenges/"

# cli-agent-implement: bundles challenges/, requirements/, schemas/, guides it reads, IMPLEMENTING.md, AGENTS.md
copy "$REPO_ROOT/challenges/" \
     "$REPO_ROOT/skills/cli-agent-implement/references/challenges/"

copy "$REPO_ROOT/requirements/" \
     "$REPO_ROOT/skills/cli-agent-implement/references/requirements/"

copy "$REPO_ROOT/schemas/" \
     "$REPO_ROOT/skills/cli-agent-implement/references/schemas/"

copy "$REPO_ROOT/guides/unix-naming-conventions.md" \
     "$REPO_ROOT/skills/cli-agent-implement/references/guides/unix-naming-conventions.md"

copy "$REPO_ROOT/IMPLEMENTING.md" \
     "$REPO_ROOT/skills/cli-agent-implement/references/IMPLEMENTING.md"

copy "$REPO_ROOT/AGENTS.md" \
     "$REPO_ROOT/skills/cli-agent-implement/references/AGENTS.md"

if [[ "$MODE" == check ]]; then
  if [[ "$DRIFT" -ne 0 ]]; then
    echo "skill bundles are stale: run scripts/sync-skill-references.sh" >&2
    exit 1
  fi
  echo "skill bundles match the repo root"
fi
[[ "$MODE" == sync ]] && echo "done"
exit 0
