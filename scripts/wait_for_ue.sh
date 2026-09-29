#!/bin/bash
# Block until the UnrealCV server listens on PORT (default 9000, timeout 300 s).
# Only the listening socket is checked: the packaged UnrealCV server serves
# about one client per lifetime, so a probe connection here would use it up.
PORT="${1:-9000}"; TIMEOUT="${2:-300}"
for ((i = 0; i < TIMEOUT; i += 2)); do
    if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
        sleep 5   # let the default map finish loading
        echo "[>>>] UnrealCV is listening on port $PORT"; exit 0
    fi
    sleep 2
done
echo "[!!!] UnrealCV did not listen on port $PORT within ${TIMEOUT}s"; exit 1
