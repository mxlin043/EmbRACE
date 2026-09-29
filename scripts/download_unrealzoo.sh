#!/bin/bash
# Download and unpack the UnrealZoo UE5.6 Linux package (v3.0.2, ~73.5 GB
# download, ~75 GB unpacked; make sure ~150 GB are free during unpacking).
#
#   bash scripts/download_unrealzoo.sh             # from Hugging Face (default)
#   bash scripts/download_unrealzoo.sh modelscope  # from ModelScope (mirror in China)
#
# Target directory: $UNREALZOO_ROOT (default: ./UnrealEnv).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
SOURCE="${1:-huggingface}"
mkdir -p "$UNREALZOO_ROOT"
cd "$UNREALZOO_ROOT"

if [ -x "$UE_BIN" ]; then
    echo "[>>>] Already installed: $UE_BIN"; exit 0
fi

case "$SOURCE" in
  huggingface|hf)
    # https://huggingface.co/datasets/UnrealZoo/UnrealZoo_UE5
    command -v hf >/dev/null || pip install -q "huggingface_hub>=1.0"
    hf download UnrealZoo/UnrealZoo_UE5 \
        "$UE_PACKAGE.zip" --repo-type dataset --local-dir .
    echo "0c6c8438b9f1ba7191b6088ef792400f9f278deed941da1a05381efdbe9c76c5  $UE_PACKAGE.zip" \
        | sha256sum -c -
    unzip -q "$UE_PACKAGE.zip"
    rm -f "$UE_PACKAGE.zip"
    ;;
  modelscope|ms)
    # https://modelscope.cn/datasets/UnrealZoo/UnrealZoo-UE5 (3 split parts)
    pip install -q modelscope
    modelscope download --dataset UnrealZoo/UnrealZoo-UE5 \
        --include "UnrealZoo_UE5_6_v3.0.2/Linux/*" --local_dir .
    PARTS="UnrealZoo_UE5_6_v3.0.2/Linux/$UE_PACKAGE.tar.gz"
    sha256sum -c - <<SUMS
09e6b69567f97c120f8e715c0dc41d59c599f78da7e351719bb55d95ecb7a140  ${PARTS}aa
1c7ac1f0d791937125609e852f0d930836ae035484450d49cd2a521f4252f230  ${PARTS}ab
b04856e0737364b794cfda62bedfc6d059a3f4d77418d505ccadda2b3921ea39  ${PARTS}ac
SUMS
    cat "${PARTS}"a? | tar -xzf -
    rm -rf UnrealZoo_UE5_6_v3.0.2
    ;;
  *) echo "unknown source: $SOURCE (huggingface | modelscope)"; exit 1 ;;
esac

# Some archives unpack into an extra level; normalise to $UE_PACKAGE/Linux/...
if [ ! -d "$UE_PACKAGE/Linux" ] && [ -d Linux ]; then
    mkdir -p "$UE_PACKAGE" && mv Linux "$UE_PACKAGE/"
fi
[ -f "$UE_BIN" ] || { echo "[!!!] $UE_BIN not found after unpacking"; exit 1; }
chmod u+x "$UE_BIN"
echo "[>>>] UnrealZoo installed at $UNREALZOO_ROOT/$UE_PACKAGE"
echo "[>>>] Next: bash scripts/download_data.sh benchmark"
