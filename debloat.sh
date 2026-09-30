#!/usr/bin/env bash
# Samsung Galaxy A17 (SM-A175F) Debloater Toolkit
# Knox 0x0 Compliant | Banking App Safe

set -euo pipefail

echo "========================================================="
echo "   Samsung Galaxy A17 (SM-A175F) Debloater Toolkit"
echo "   Knox 0x0 Compliant | Banking App Safe"
echo "========================================================="
echo

if ! adb get-state >/dev/null 2>&1; then
    echo "[ERROR] No ADB device detected! Check USB debugging."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES_FILE="${SCRIPT_DIR}/packages.txt"

if [[ ! -f "${PACKAGES_FILE}" ]]; then
    echo "[ERROR] packages.txt not found!"
    exit 1
fi

echo "[*] Processing debloat list..."
while IFS= read -r pkg || [[ -n "$pkg" ]]; do
    [[ "$pkg" =~ ^#.*$ || -z "$pkg" ]] && continue
    echo -n "[*] Uninstalling ${pkg}... "
    adb shell pm uninstall -k --user 0 "$pkg" >/dev/null 2>&1 && echo "[OK]" || echo "[SKIPPED]"
done < "${PACKAGES_FILE}"

echo -n "[*] Restricting Game Optimizing Service (GOS)... "
adb shell pm disable-user --user 0 com.samsung.android.game.gos >/dev/null 2>&1 && echo "[OK]" || echo "[SKIPPED]"

echo
echo "========================================================="
echo "[DONE] Debloat completed successfully!"
echo "========================================================="
