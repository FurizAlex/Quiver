#!/usr/bin/env bash
# Build Quiver with PyInstaller and install it so rofi (drun) can launch it.
# Put this file in the project root, next to Quiver.spec, then run:  ./build-and-install.sh
set -euo pipefail
cd "$(dirname "$0")"

APP_DIR="$HOME/.local/opt/Quiver"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"

# use the project's venv (named venv or .venv) if there is one
PY="python3"
for d in venv .venv; do
  if [ -x "$d/bin/python" ]; then PY="$d/bin/python"; break; fi
done
echo "==> Using $PY"
"$PY" -c "import PyQt6, numpy" 2>/dev/null || {
  echo "PyQt6/numpy aren't installed for $PY, so the build would be broken."
  echo "Run:  $PY -m pip install PyQt6 numpy"; exit 1; }
"$PY" -c "import PyInstaller" 2>/dev/null || {
  echo "PyInstaller isn't installed for $PY."
  echo "Run:  $PY -m pip install pyinstaller"; exit 1; }
[ -f Quiver.spec ] || { echo "Run this from the project root (Quiver.spec not found)"; exit 1; }

echo "==> Building"
"$PY" -m PyInstaller Quiver.spec --noconfirm --clean

[ -x dist/Quiver/Quiver ] || { echo "Build failed: dist/Quiver/Quiver missing"; exit 1; }

echo "==> Installing to $APP_DIR"
# keep the user's settings (config/) across reinstalls
KEEP="$(mktemp -d)"
for c in "$APP_DIR/_internal/config" "$APP_DIR/config"; do
  [ -d "$c" ] && cp -r "$c/." "$KEEP/" && break
done
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR" "$BIN_DIR" "$APPS_DIR" "$ICON_DIR"
cp -r dist/Quiver/. "$APP_DIR/"
for c in "$APP_DIR/_internal/config" "$APP_DIR/config"; do
  [ -d "$c" ] && cp -r "$KEEP/." "$c/" && break
done
rm -rf "$KEEP"

# launcher: rofi hides errors, so everything Quiver prints goes to ~/.cache/quiver.log
LAUNCHER="$APP_DIR/quiver-launch"
cat > "$LAUNCHER" <<LAUNCH
#!/usr/bin/env bash
mkdir -p "\$HOME/.cache"
exec "$APP_DIR/Quiver" "\$@" > "\$HOME/.cache/quiver.log" 2>&1
LAUNCH
chmod +x "$LAUNCHER"
ln -sf "$LAUNCHER" "$BIN_DIR/quiver"
cp assets/icons/quiver.png "$ICON_DIR/quiver.png"

cat > "$APPS_DIR/quiver.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Quiver
Comment=Code editor
Exec=$LAUNCHER
Icon=$ICON_DIR/quiver.png
Terminal=false
Categories=Development;TextEditor;
StartupWMClass=Quiver
DESKTOP

update-desktop-database "$APPS_DIR" 2>/dev/null || true
echo "==> Done. Open rofi (rofi -show drun) and type: Quiver"
echo "    If it does not open, read: ~/.cache/quiver.log"
