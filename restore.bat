@echo off
setlocal enabledelayedexpansion
title Galaxy A17 Package Restorer

echo =========================================================
echo    Samsung Galaxy A17 (SM-A175F) Package Restorer
echo =========================================================
echo.

adb get-state >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No ADB device detected!
    pause
    exit /b 1
)

set SCRIPT_DIR=%~dp0

for /f "usebackq eol=# tokens=*" %%P in ("%SCRIPT_DIR%packages.txt") do (
    if not "%%P"=="" (
        echo [*] Restoring %%P...
        adb shell cmd package install-existing %%P >nul 2>&1
    )
)

echo [*] Enabling Game Optimizing Service (GOS)...
adb shell pm enable com.samsung.android.game.gos >nul 2>&1

echo.
echo =========================================================
echo [DONE] Restoration complete!
echo =========================================================
echo.
pause
