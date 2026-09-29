#!/bin/bash
# Check that this installation reproduces recorded demonstrations exactly: start a headless UE
# instance, replay the demonstrations in reproducibility/ through the evaluator's own task setup
# and action execution, and compare every recorded pose with the replayed one.
#
#   bash scripts/check_reproducibility.sh [extra check_reproducibility args ...]
#
# Env: UE_PORT (default 9000), GPU_ID (default 0). Exits nonzero if any demonstration differs.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
UE_PORT="${UE_PORT:-9000}"

bash "$PROJECT_ROOT/scripts/run_ue_server.sh" "$UE_PORT" --headless > "$PROJECT_ROOT/ue_$UE_PORT.log" 2>&1 &
UE_PID=$!
trap 'kill $UE_PID 2>/dev/null || true' EXIT
bash "$PROJECT_ROOT/scripts/wait_for_ue.sh" "$UE_PORT"

cd "$PROJECT_ROOT"
python -m embrace.eval.check_reproducibility --port "$UE_PORT" "$@"
