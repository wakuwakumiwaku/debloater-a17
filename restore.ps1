# Galaxy A17 Package Restorer (PowerShell)

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   Samsung Galaxy A17 (SM-A175F) Package Restorer" -ForegroundColor Cyan
Write-Host "=========================================================`n" -ForegroundColor Cyan

$packagesFile = Join-Path $PSScriptRoot "packages.txt"
$packages = Get-Content $packagesFile | Where-Object { $_ -and -not $_.StartsWith("#") }

foreach ($pkg in $packages) {
    Write-Host "[*] Restoring $pkg..." -NoNewline
    adb shell cmd package install-existing $pkg 2>&1 | Out-Null
    Write-Host " [OK]" -ForegroundColor Green
}

Write-Host "[*] Enabling Game Optimizing Service (GOS)..." -NoNewline
adb shell pm enable com.samsung.android.game.gos 2>&1 | Out-Null
Write-Host " [OK]" -ForegroundColor Green

Write-Host "`n[DONE] All packages successfully restored!" -ForegroundColor Green
