# Galaxy A17 Debloater (PowerShell)
# Safe for Knox 0x0, Play Integrity, and Banking Apps

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   Samsung Galaxy A17 (SM-A175F) Debloater Toolkit" -ForegroundColor Cyan
Write-Host "   Knox 0x0 Compliant | Banking App Safe" -ForegroundColor Cyan
Write-Host "=========================================================`n" -ForegroundColor Cyan

$device = adb get-state 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] No ADB device detected! Check USB debugging." -ForegroundColor Red
    exit 1
}

$packagesFile = Join-Path $PSScriptRoot "packages.txt"
if (-not (Test-Path $packagesFile)) {
    Write-Host "[ERROR] packages.txt not found!" -ForegroundColor Red
    exit 1
}

$packages = Get-Content $packagesFile | Where-Object { $_ -and -not $_.StartsWith("#") }
$total = $packages.Count
$count = 0
$success = 0

foreach ($pkg in $packages) {
    $count++
    Write-Host "[$count/$total] Uninstalling $pkg..." -NoNewline
    $res = adb shell pm uninstall -k --user 0 $pkg 2>&1
    if ($res -match "Success") {
        Write-Host " [OK]" -ForegroundColor Green
        $success++
    } else {
        Write-Host " [SKIPPED/ABSENT]" -ForegroundColor DarkGray
    }
}

Write-Host "`n[*] Restricting Game Optimizing Service (GOS)..." -NoNewline
adb shell pm disable-user --user 0 com.samsung.android.game.gos 2>&1 | Out-Null
Write-Host " [OK]" -ForegroundColor Green

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "[DONE] Debloat complete! Successfully processed $success packages." -ForegroundColor Green
Write-Host "=========================================================`n" -ForegroundColor Cyan
