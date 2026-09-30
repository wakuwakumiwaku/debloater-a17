# Galaxy A17 System Optimizer (PowerShell)

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   Samsung Galaxy A17 (SM-A175F) System Optimizer" -ForegroundColor Cyan
Write-Host "=========================================================`n" -ForegroundColor Cyan

$device = adb get-state 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] No ADB device detected!" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Disabling RAM Plus..." -NoNewline
adb shell settings put global ram_expand_size 0
Write-Host " [OK]" -ForegroundColor Green

Write-Host "[*] Setting UI animations to 0.5x..." -NoNewline
adb shell settings put global window_animation_scale 0.5
adb shell settings put global transition_animation_scale 0.5
adb shell settings put global animator_duration_scale 0.5
Write-Host " [OK]" -ForegroundColor Green

Write-Host "[*] Enforcing AdGuard Private DNS..." -NoNewline
adb shell settings put global private_dns_mode hostname
adb shell settings put global private_dns_specifier dns.adguard-dns.com
Write-Host " [OK]" -ForegroundColor Green

Write-Host "[*] Enabling clipboard access alerts..." -NoNewline
adb shell settings put secure show_clip_access_notification 1
Write-Host " [OK]" -ForegroundColor Green

Write-Host "[*] Disabling crash report telemetry..." -NoNewline
adb shell settings put global send_action_app_error 0
Write-Host " [OK]" -ForegroundColor Green

Write-Host "[*] Enabling Battery Protection (80% charge limit)..." -NoNewline
adb shell settings put global protect_battery 3
Write-Host " [OK]" -ForegroundColor Green

Write-Host "[*] Trimming logcat buffer to 64K..." -NoNewline
adb shell logcat -G 64K
Write-Host " [OK]" -ForegroundColor Green

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "[DONE] All optimizations applied successfully!" -ForegroundColor Green
Write-Host "=========================================================`n" -ForegroundColor Cyan
