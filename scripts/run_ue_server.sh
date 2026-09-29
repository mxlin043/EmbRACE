#!/bin/bash
# Start one UnrealZoo UE5.6 instance with the UnrealCV server on PORT.
#
#   bash scripts/run_ue_server.sh [PORT] [--headless]
#
# Windowed mode (default) opens a UE window on $DISPLAY: use it for local play.
# --headless renders off-screen: use it for evaluation on servers.
# Env: GPU_ID (default 0), RES_X/RES_Y (default 640x480).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

PORT=9000
HEADLESS=0
for arg in "$@"; do
    case "$arg" in
        --headless) HEADLESS=1 ;;
        *) PORT="$arg" ;;
    esac
done
GPU_ID="${GPU_ID:-0}"
RES_X="${RES_X:-640}"
RES_Y="${RES_Y:-480}"
EXEC_CMDS="r.DynamicGlobalIlluminationMethod 0,r.Lumen.DiffuseIndirect.Allow 0,r.ReflectionMethod 0,r.Lumen.Reflections.Allow 0,r.SSR.Quality 0"

[ -f "$UE_BIN" ] || { echo "[!!!] UnrealZoo not found at $UE_BIN. Put $UE_PACKAGE/ in ./UnrealEnv, or set UNREALZOO_ROOT to its folder (README section 3)."; exit 1; }
[ -x "$UE_BIN" ] || chmod u+x "$UE_BIN"

if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    echo "[!!!] Port $PORT is already in use; pick another port."; exit 1
fi

# Start from the pinned configuration in ue_config/ every time.
rm -rf "$UE_CONFIG_DIR/Linux"
mkdir -p "$UE_CONFIG_DIR/Linux"
cp "$PROJECT_ROOT"/ue_config/Engine.ini "$PROJECT_ROOT"/ue_config/GameUserSettings.ini \
   "$PROJECT_ROOT"/ue_config/Input.ini "$UE_CONFIG_DIR/Linux/"
sed "s/^Port=.*/Port=$PORT/" "$PROJECT_ROOT/ue_config/unrealcv.ini" > "$UNREALCV_INI"

EXTRA=()
if [ "$HEADLESS" = 1 ]; then
    EXTRA+=(-RenderOffScreen)
    echo "[>>>] Starting UnrealZoo (headless) on GPU $GPU_ID, UnrealCV port $PORT"
else
    echo "[>>>] Starting UnrealZoo (windowed) on GPU $GPU_ID, UnrealCV port $PORT"
fi

exec "$UE_BIN" -vulkan -unattended -NoSound -NoVSync -NoHMD -NoXR \
    -ResX="$RES_X" -ResY="$RES_Y" -forcepassthrough -log \
    -ExecCmds="$EXEC_CMDS" -graphicsadapter="$GPU_ID" "${EXTRA[@]}"
