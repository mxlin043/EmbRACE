# Shared paths for the launch scripts. Source, do not execute.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UE_PACKAGE="${UE_PACKAGE:-UnrealZoo_UE5_6_Linux_v3.0.2}"
UE_PROJECT="UnrealZoo_UE5_6"
# UnrealZoo is in ./UnrealEnv unless UNREALZOO_ROOT names another folder: the one that
# holds $UE_PACKAGE/, or $UE_PACKAGE/ itself.
UNREALZOO_ROOT="${UNREALZOO_ROOT:-$PROJECT_ROOT/UnrealEnv}"
UE_BASE="$UNREALZOO_ROOT/$UE_PACKAGE/Linux/$UE_PROJECT"
if [ ! -d "$UE_BASE" ] && [ -d "$UNREALZOO_ROOT/Linux/$UE_PROJECT" ]; then
    UE_BASE="$UNREALZOO_ROOT/Linux/$UE_PROJECT"
fi
UE_BIN="$UE_BASE/Binaries/Linux/$UE_PROJECT"
UE_CONFIG_DIR="$UE_BASE/Saved/Config"
UNREALCV_INI="$UE_BASE/Binaries/Linux/unrealcv.ini"
