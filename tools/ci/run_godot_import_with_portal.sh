#!/usr/bin/env bash
# Run the real Godot editor import inside an isolated X11 + D-Bus + XDG portal session.
# Debian trixie ships xdg-desktop-portal-gnome 48.0, whose Settings backend
# implements both org.freedesktop.appearance color-scheme and accent-color.
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-$PWD}"
GODOT_BIN="${GODOT_BIN:?GODOT_BIN must point to the pinned Godot 4.5.1 binary}"
LOG_DIR="${RUNNER_TEMP:?RUNNER_TEMP must be set}"

test -s "$WORKSPACE/project.godot"
test -x "$GODOT_BIN"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  dbus dbus-x11 \
  xdg-desktop-portal xdg-desktop-portal-gnome xdg-desktop-portal-gtk \
  gsettings-desktop-schemas dconf-gsettings-backend \
  xvfb xauth x11-utils python3 \
  libgl1 libgl1-mesa-dri libglx-mesa0 libvulkan1 mesa-vulkan-drivers \
  libx11-6 libxcursor1 libxinerama1 libxrandr2 libxi6 libxrender1 \
  libxfixes3 libxkbcommon0 libfontconfig1 libasound2t64

PORTAL_VERSION="$(dpkg-query -W -f='${Version}' xdg-desktop-portal-gnome)"
PORTAL_FRONTEND_VERSION="$(dpkg-query -W -f='${Version}' xdg-desktop-portal)"
echo "GNOME portal backend version: $PORTAL_VERSION"
echo "XDG portal frontend version: $PORTAL_FRONTEND_VERSION"
dpkg --compare-versions "$PORTAL_VERSION" ge "48.0-2"
dpkg --compare-versions "$PORTAL_FRONTEND_VERSION" ge "1.20.3"

export HOME="$LOG_DIR/portal-home"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_RUNTIME_DIR="/tmp/jedl-xdg-runtime"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME" "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

export DISPLAY=:99
Xvfb "$DISPLAY" -screen 0 1280x800x24 -nolisten tcp >"$LOG_DIR/xvfb-portal.log" 2>&1 &
XVFB_PID=$!
cleanup() {
  kill "$XVFB_PID" 2>/dev/null || true
  wait "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT
for attempt in $(seq 1 30); do
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then break; fi
  sleep 1
done
xdpyinfo -display "$DISPLAY" >/dev/null

export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_DESKTOP=gnome
export XDG_SESSION_TYPE=x11
export XDG_DATA_DIRS="/usr/local/share:/usr/share"
export GSETTINGS_BACKEND=memory
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe

dbus-run-session -- bash -euo pipefail -c '
  set -x
  dbus-update-activation-environment DISPLAY XDG_RUNTIME_DIR XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XDG_DATA_DIRS HOME

  # Introspection activates the frontend; its GNOME backend is selected by
  # gnome-portals.conf for XDG_CURRENT_DESKTOP=GNOME.
  gdbus introspect --session \
    --dest org.freedesktop.portal.Desktop \
    --object-path /org/freedesktop/portal/desktop \
    > "$RUNNER_TEMP/portal-introspection.log"
  grep -Fq "org.freedesktop.portal.Settings" "$RUNNER_TEMP/portal-introspection.log"

  color_scheme="$(gdbus call --session \
    --dest org.freedesktop.portal.Desktop \
    --object-path /org/freedesktop/portal/desktop \
    --method org.freedesktop.portal.Settings.Read \
    org.freedesktop.appearance color-scheme)"
  printf "Portal color-scheme response: %s\n" "$color_scheme"
  printf "%s\n" "$color_scheme" | grep -Eq "uint32 [012]"

  accent_color="$(gdbus call --session \
    --dest org.freedesktop.portal.Desktop \
    --object-path /org/freedesktop/portal/desktop \
    --method org.freedesktop.portal.Settings.Read \
    org.freedesktop.appearance accent-color)"
  printf "Portal accent-color response: %s\n" "$accent_color"
  python3 -c '\''import re,sys
s=sys.stdin.read()
m=re.search(r"<\(([^)]*)\)>", s)
assert m, f"accent-color did not return a tuple: {s!r}"
values=re.findall(r"(?:\d+\.)?\d+(?:[eE][+-]?\d+)?", m.group(1))
assert len(values)==3, f"expected three RGB components, got {values!r}"
assert all(0.0 <= float(v) <= 1.0 for v in values), f"RGB component out of range: {values!r}"
print("Portal accent-color RGB validated:", ", ".join(values))'\'' <<< "$accent_color"

  # Godot is run in this exact D-Bus session and Xvfb display.
  set +e
  "$GODOT_BIN" --rendering-method gl_compatibility --rendering-driver opengl3 \
    --audio-driver Dummy --editor --import --path "$GITHUB_WORKSPACE" --verbose \
    2>&1 | tee "$RUNNER_TEMP/godot-import.log"
  godot_status=${PIPESTATUS[0]}
  set -e
  if [ "$godot_status" -ne 0 ] || grep -E "ERROR:|SCRIPT ERROR:|Parse Error:|Failed to load|Failed importing" "$RUNNER_TEMP/godot-import.log"; then
    echo "Godot import emitted an error; refusing to run tests or export an APK."
    exit 1
  fi
  echo "GODOT_IMPORT_EXIT_CODE=$godot_status"
  test "$godot_status" -eq 0
'

test -d "$WORKSPACE/.godot/imported"
