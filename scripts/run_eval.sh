#!/bin/bash
# Evaluate one model on the benchmark tasks in datas/benchmark/task with a headless
# UE instance, then score the results.
#
#   bash scripts/run_eval.sh MODEL [extra eval_vlm args ...]
#
# MODEL is a route in configs/vlm_models.yaml (endpoint, key variable, sampling).
# Env: UE_PORT (default 9000), GPU_ID (default 0), SAVE_DIR (default ./runs).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
MODEL="${1:?usage: run_eval.sh MODEL [extra eval_vlm args]}"
shift
UE_PORT="${UE_PORT:-9000}"
SAVE_DIR="${SAVE_DIR:-$PROJECT_ROOT/runs}"

bash "$PROJECT_ROOT/scripts/run_ue_server.sh" "$UE_PORT" --headless > "$PROJECT_ROOT/ue_$UE_PORT.log" 2>&1 &
UE_PID=$!
trap 'kill $UE_PID 2>/dev/null || true' EXIT
bash "$PROJECT_ROOT/scripts/wait_for_ue.sh" "$UE_PORT"

cd "$PROJECT_ROOT"
python -m embrace.eval.eval_vlm --port "$UE_PORT" --model "$MODEL" \
    --save_dir "$SAVE_DIR" "$@"
python -m embrace.eval.score_metrics --runs-root "$SAVE_DIR" \
    --report "$SAVE_DIR/report_${MODEL//\//_}.json"
