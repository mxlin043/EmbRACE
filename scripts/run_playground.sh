#!/bin/bash
# Start a windowed UE instance and the web playground on top of it.
#
#   bash scripts/run_playground.sh [MAP] [UE_PORT] [WEB_PORT]
#
# Then open http://localhost:WEB_PORT (default 8080).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
MAP="${1:-IndustrialArea}"
UE_PORT="${2:-9000}"
WEB_PORT="${3:-8080}"

bash "$PROJECT_ROOT/scripts/run_ue_server.sh" "$UE_PORT" > "$PROJECT_ROOT/ue_$UE_PORT.log" 2>&1 &
UE_PID=$!
trap 'kill $UE_PID 2>/dev/null || true' EXIT
echo "[>>>] UE log: ue_$UE_PORT.log"
bash "$PROJECT_ROOT/scripts/wait_for_ue.sh" "$UE_PORT"

cd "$PROJECT_ROOT"
python -m embrace.web_ui.playground --port "$UE_PORT" --map "$MAP" --web_port "$WEB_PORT"
