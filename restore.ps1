# Galaxy A17 Package Restorer (PowerShell)

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   Samsung Galaxy A17 (SM-A175F) Package Restorer" -ForegroundColor Cyan
Write-Host "=========================================================`n" -ForegroundColor Cyan

. (Join-Path $PSScriptRoot "package-list.ps1")
$packagesFile = Join-Path $PSScriptRoot "packages.txt"
try {
    $packages = @(Get-ValidatedPackages -Path $packagesFile)
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$failed = 0
foreach ($pkg in $packages) {
    Write-Host "[*] Restoring $pkg..." -NoNewline
    adb shell cmd package install-existing $pkg 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK]" -ForegroundColor Green
    } else {
        Write-Host " [FAILED]" -ForegroundColor Red
        $failed++
    }
}

Write-Host "[*] Enabling Game Optimizing Service (GOS)..." -NoNewline
adb shell pm enable com.samsung.android.game.gos 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host " [OK]" -ForegroundColor Green
} else {
    Write-Host " [FAILED]" -ForegroundColor Red
    $failed++
}

if ($failed -gt 0) {
    Write-Host "`n[ERROR] Restore incomplete: $failed operation(s) failed." -ForegroundColor Red
    exit 1
}
Write-Host "`n[DONE] All packages successfully restored!" -ForegroundColor Green
