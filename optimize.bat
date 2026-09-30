@echo off
title Galaxy A17 Performance & Privacy Optimizer

echo =========================================================
echo   Samsung Galaxy A17 (SM-A175F) System Optimizer
echo =========================================================
echo.

adb get-state >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No ADB device detected!
    pause
    exit /b 1
)

echo [*] Disabling RAM Plus (prevents flash storage wear & micro-stutter)...
adb shell settings put global ram_expand_size 0

echo [*] Setting UI animation speeds to 0.5x (snappier navigation)...
adb shell settings put global window_animation_scale 0.5
adb shell settings put global transition_animation_scale 0.5
adb shell settings put global animator_duration_scale 0.5

echo [*] Enforcing system-wide AdGuard Encrypted DNS (blocks ads & trackers)...
adb shell settings put global private_dns_mode hostname
adb shell settings put global private_dns_specifier dns.adguard-dns.com

echo [*] Enabling clipboard access read alert notifications...
adb shell settings put secure show_clip_access_notification 1

echo [*] Disabling automatic crash report telemetry...
adb shell settings put global send_action_app_error 0

echo [*] Enabling Maximum Battery Protection (80%% charge limit for longevity)...
adb shell settings put global protect_battery 3

echo [*] Reducing logcat ring buffers to 64 KiB...
adb shell logcat -G 64K

echo.
echo =========================================================
echo [DONE] Optimizations successfully applied!
echo Note: A restart is recommended for RAM Plus 0 to take effect.
echo =========================================================
echo.
pause
