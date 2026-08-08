#!/bin/bash
# Builds Stud-OS-x86_64.AppImage from the current source tree.
#
# What this does NOT do: bundle Ollama/LM Studio (real, separate local
# services -- see AppRun's comments) or bake in any AI provider API key
# (none are required; every AI feature reports "not configured" until
# the person running the app sets one up themselves in Settings).
#
# Usage: ./packaging/appimage/build.sh
# Output: ./Stud-OS-x86_64.AppImage in the repo root.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$(mktemp -d)"
APPDIR="$BUILD_DIR/Stud-OS.AppDir"

echo "==> Building in $BUILD_DIR"
trap 'rm -rf "$BUILD_DIR"' EXIT

# ---- 1. frontend production build ----
echo "==> Building frontend (npm run build)..."
(cd "$REPO_ROOT/frontend" && npm run build --silent)

# ---- 2. AppDir skeleton ----
# usr/app/backend (not usr/backend) on purpose: Stud-OS imports itself
# as the "backend" package (`from backend.database import ...`), same
# as dev where the repo root sits on sys.path -- so the dir uvicorn's
# --app-dir points at has to be one level above backend/ itself.
mkdir -p "$APPDIR/usr/app/backend" "$APPDIR/usr/frontend-build" "$APPDIR/usr/venv"

# ---- 3. copy backend source, excluding dev-only artifacts ----
echo "==> Copying backend source..."
rsync -a \
    --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='stud_os.db' --exclude='.pytest_cache' --exclude='uploads/*' \
    "$REPO_ROOT/backend/" "$APPDIR/usr/app/backend/"
find "$APPDIR/usr/app/backend" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

# ---- 4. copy frontend build ----
echo "==> Copying frontend build..."
rsync -a "$REPO_ROOT/frontend/dist/" "$APPDIR/usr/frontend-build/"

# ---- 5. fresh, self-contained venv ----
# --copies (not symlinks): the AppImage's squashfs is mounted read-only
# at a different path every run, so anything symlinked back to a build-
# time path would break at launch.
echo "==> Building venv..."
python3 -m venv --copies "$APPDIR/usr/venv"
"$APPDIR/usr/venv/bin/pip" install --quiet --upgrade pip
# CPU-only torch FIRST (see README/HANDOFF): sentence-transformers pulls
# torch in transitively, and a plain install grabs ~2.5GB of CUDA
# packages this environment doesn't need and an AppImage shouldn't ship.
"$APPDIR/usr/venv/bin/pip" install --quiet torch --index-url https://download.pytorch.org/whl/cpu
"$APPDIR/usr/venv/bin/pip" install --quiet -r "$REPO_ROOT/backend/requirements.txt"

# ---- 6. schema-only seed DB ----
# Migrated once at build time so a fresh install never needs alembic
# (or even network access) on first launch -- AppRun just copies this
# into place. Run from REPO_ROOT, exactly like the documented dev
# workflow (README's "Run alembic commands from the repo root") --
# alembic.ini's prepend_sys_path=. depends on that CWD for `backend.*`
# imports in env.py to resolve. DATABASE_URL points at a throwaway path
# so this never touches the real dev DB.
echo "==> Generating seed database..."
SEED_DB="$BUILD_DIR/seed.db"
(cd "$REPO_ROOT" && DATABASE_URL="sqlite:///$SEED_DB" \
    "$APPDIR/usr/venv/bin/python3" -m alembic -c backend/alembic.ini upgrade head)
mv "$SEED_DB" "$APPDIR/usr/seed.db"

# ---- 7. AppRun / desktop file / icon ----
cp "$REPO_ROOT/packaging/appimage/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
cp "$REPO_ROOT/packaging/appimage/Stud-OS.desktop" "$APPDIR/Stud-OS.desktop"
if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w 256 -h 256 "$REPO_ROOT/packaging/appimage/stud-os-icon.svg" -o "$APPDIR/stud-os.png"
else
    echo "WARNING: rsvg-convert not found -- AppImage will build without an icon."
fi

# ---- 8. appimagetool (cached under packaging/appimage/.cache, gitignored) ----
CACHE_DIR="$REPO_ROOT/packaging/appimage/.cache"
mkdir -p "$CACHE_DIR"
if [ ! -x "$CACHE_DIR/appimagetool.AppImage" ]; then
    echo "==> Downloading appimagetool..."
    curl -sL -o "$CACHE_DIR/appimagetool.AppImage" \
        https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$CACHE_DIR/appimagetool.AppImage"
fi

echo "==> Packaging..."
rm -f "$REPO_ROOT/Stud-OS-x86_64.AppImage"
ARCH=x86_64 "$CACHE_DIR/appimagetool.AppImage" \
    "$APPDIR" "$REPO_ROOT/Stud-OS-x86_64.AppImage"

echo "==> Done: $REPO_ROOT/Stud-OS-x86_64.AppImage"
