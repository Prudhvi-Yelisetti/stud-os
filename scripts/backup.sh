#!/usr/bin/env bash
# Nightly backup: tars the repo (minus node_modules/.venv/caches) + the
# SQLite DB to a second location. This is the single control that would
# have prevented the 2026-05-18 total-loss incident -- see REBUILD_PLAN.md
# section 7. Wire this to cron, e.g.:
#   0 2 * * * /home/prudhvi/Projects/stud-os/scripts/backup.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${STUD_OS_BACKUP_DIR:-$HOME/backups/stud-os}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_DIR/stud-os-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

tar -czf "$DEST" \
  --exclude="node_modules" \
  --exclude=".venv" \
  --exclude="__pycache__" \
  --exclude=".vite" \
  --exclude="dist" \
  -C "$(dirname "$PROJECT_DIR")" "$(basename "$PROJECT_DIR")"

echo "Backed up to $DEST"

# Keep the last 14 backups only
ls -1t "$BACKUP_DIR"/stud-os-*.tar.gz | tail -n +15 | xargs -r rm --
