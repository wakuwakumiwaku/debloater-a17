# Shared package-list validation. No ADB calls are allowed until this returns.
function Get-ValidatedPackages {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "packages.txt not found!"
    }
    $raw = [System.IO.File]::ReadAllText($Path)
    if ($raw.Contains([char]0)) {
        throw "Invalid NUL byte in packages.txt!"
    }
    $packages = [System.Collections.Generic.List[string]]::new()
    $lineNumber = 0
    foreach ($line in ($raw -split "`n")) {
        $lineNumber++
        # Accept LF/CRLF, but never normalize embedded control characters.
        $pkg = $line
        if ($pkg.EndsWith("`r")) { $pkg = $pkg.Substring(0, $pkg.Length - 1) }
        $pkg = $pkg.Trim([char[]]" `t")
        if ($pkg.Length -eq 0 -or $pkg.StartsWith('#')) { continue }
        if ($pkg -cnotmatch '\A[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ][abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_]*(\.[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ][abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_]*)*\z') {
            throw "Invalid package name on line $lineNumber."
        }
        $packages.Add($pkg)
    }
    # Emit only after every record passes; preserve case, duplicates and order.
    return $packages.ToArray()
}
