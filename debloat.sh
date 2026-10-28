#!/usr/bin/env bash
# Samsung Galaxy A17 (SM-A175F) Debloater Toolkit
# Knox 0x0 Compliant | Banking App Safe

set -euo pipefail

echo "========================================================="
echo "   Samsung Galaxy A17 (SM-A175F) Debloater Toolkit"
echo "   Knox 0x0 Compliant | Banking App Safe"
echo "========================================================="
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES_FILE="${SCRIPT_DIR}/packages.txt"

if [[ ! -f "${PACKAGES_FILE}" ]]; then
    echo "[ERROR] packages.txt not found!"
    exit 1
fi

# Bash read otherwise silently drops NUL bytes.
if IFS= read -r -d '' _ < "${PACKAGES_FILE}"; then
    echo "[ERROR] Invalid NUL byte in packages.txt!" >&2
    exit 1
fi

packages=()
line_number=0
while IFS= read -r pkg || [[ -n "$pkg" ]]; do
    line_number=$((line_number + 1))
    pkg="${pkg%$'\r'}"
    pkg="${pkg#"${pkg%%[!$' \t']*}"}"
    pkg="${pkg%"${pkg##*[!$' \t']}"}"
    [[ "$pkg" == \#* || -z "$pkg" ]] && continue
    # Enumerate ASCII characters: regex ranges depend on the caller's locale.
    if [[ ! "$pkg" =~ ^[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ][abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_]*(\.[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ][abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_]*)*$ ]]; then
        echo "[ERROR] Invalid package name on line ${line_number}." >&2
        exit 1
    fi
    packages+=("$pkg")
done < "${PACKAGES_FILE}"

if ! adb get-state >/dev/null 2>&1; then
    echo "[ERROR] No ADB device detected! Check USB debugging."
    exit 1
fi

echo "[*] Processing debloat list..."
for pkg in "${packages[@]}"; do
    echo -n "[*] Uninstalling ${pkg}... "
    adb shell pm uninstall -k --user 0 "$pkg" >/dev/null 2>&1 && echo "[OK]" || echo "[SKIPPED]"
done

echo -n "[*] Restricting Game Optimizing Service (GOS)... "
adb shell pm disable-user --user 0 com.samsung.android.game.gos >/dev/null 2>&1 && echo "[OK]" || echo "[SKIPPED]"

echo
echo "========================================================="
echo "[DONE] Debloat completed successfully!"
echo "========================================================="
