#!/bin/bash
# Download the EmbRACE data from Hugging Face (mxlin043/EmbRACE) and unpack it into ./datas.
#
#   bash scripts/download_data.sh                          # dataset and benchmark, ~7.4 GB
#   bash scripts/download_data.sh benchmark                # the benchmark only, ~1.6 GB
#   bash scripts/download_data.sh benchmark IndustrialArea # one environment of one part
#
# Each environment is one archive under packed/ in the dataset repo. The archives are unpacked
# into datas/ and the unpacked files are checked against the release's SHA256SUMS:
#
#   datas/dataset/task/<Env>/<Task>.json                 dataset task files
#   datas/dataset/trajectory/<Env>/<Task>/               frames and record of each demonstration
#   datas/benchmark/task/<Env>/<Task>.json               benchmark tasks, read by the evaluator
#   datas/benchmark/trajectory/<Env>/<Task>/             reference human demonstrations
#   datas/benchmark/success_region/<Env>/<Task>/         success regions, read by the scorer
#
# The archives stay in datas/.hf so that a rerun skips them; KEEP_ARCHIVES=0 deletes them once
# they are unpacked. HF_TOKEN, if set, raises the Hub's download rate limit.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
REPO="${EMBRACE_REPO:-mxlin043/EmbRACE}"
DATA_DIR="$PROJECT_ROOT/datas"
CACHE="$DATA_DIR/.hf"

PART="${1:-all}"
[ $# -gt 0 ] && shift
case "$PART" in
  all) PARTS=(dataset benchmark) ;;
  dataset|benchmark) PARTS=("$PART") ;;
  *) echo "usage: download_data.sh [all|dataset|benchmark] [ENV ...]" >&2; exit 1 ;;
esac

command -v hf >/dev/null || pip install -q "huggingface_hub>=1.0"
INCLUDES=(--include SHA256SUMS --include environments.json --include pd_objects.json)
for part in "${PARTS[@]}"; do
  if [ $# -gt 0 ]; then
    for env in "$@"; do INCLUDES+=(--include "packed/$part/$env.tar"); done
  else
    INCLUDES+=(--include "packed/$part/*.tar")
  fi
done
mkdir -p "$CACHE"
hf download "$REPO" --repo-type dataset --local-dir "$CACHE" "${INCLUDES[@]}" > /dev/null

ARCHIVES=()
for part in "${PARTS[@]}"; do
  if [ $# -gt 0 ]; then
    for env in "$@"; do
      if [ -f "$CACHE/packed/$part/$env.tar" ]; then
        ARCHIVES+=("$CACHE/packed/$part/$env.tar")
      elif [ "$PART" != all ]; then
        echo "no environment '$env' in the $part part (see datas/environments.json)" >&2; exit 1
      fi
    done
  else
    ARCHIVES+=("$CACHE"/packed/"$part"/*.tar)
  fi
done
[ ${#ARCHIVES[@]} -gt 0 ] || { echo "nothing to unpack" >&2; exit 1; }

cp "$CACHE/environments.json" "$CACHE/pd_objects.json" "$DATA_DIR/"
for archive in "${ARCHIVES[@]}"; do
  tar -xf "$archive" -C "$DATA_DIR"
  [ "${KEEP_ARCHIVES:-1}" = 0 ] && rm -f "$archive"
done
(cd "$DATA_DIR" && sha256sum --quiet --ignore-missing -c "$CACHE/SHA256SUMS")
echo "[>>>] ${#ARCHIVES[@]} environment archive(s) unpacked into $DATA_DIR and verified"
