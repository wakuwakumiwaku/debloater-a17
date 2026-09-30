@echo off
setlocal enabledelayedexpansion
title Galaxy A17 Debloater (Knox 0x0 Safe)

echo =========================================================
echo    Samsung Galaxy A17 (SM-A175F) Debloater Toolkit
echo    Knox 0x0 Compliant ^| Banking App Safe
echo =========================================================
echo.

adb get-state >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No ADB device detected!
    echo Ensure USB Debugging is enabled and your device is connected.
    pause
    exit /b 1
)

echo [*] Device connected. Beginning debloat process...
echo.

set SCRIPT_DIR=%~dp0
set SUCCESS_COUNT=0
set FAIL_COUNT=0

for /f "usebackq eol=# tokens=*" %%P in ("%SCRIPT_DIR%packages.txt") do (
    if not "%%P"=="" (
        echo [*] Uninstalling %%P...
        adb shell pm uninstall -k --user 0 %%P >nul 2>&1
        if !errorlevel! equ 0 (
            set /a SUCCESS_COUNT+=1
        ) else (
            set /a FAIL_COUNT+=1
        )
    )
)

echo [*] Disabling Game Optimizing Service (GOS)...
adb shell pm disable-user --user 0 com.samsung.android.game.gos >nul 2>&1

echo.
echo =========================================================
echo [DONE] Debloat complete!
echo Packages processed: !SUCCESS_COUNT! uninstalled/verified.
echo =========================================================
echo.
pause
