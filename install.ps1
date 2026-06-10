# One-command install for Minakami Plugins on Windows.
# Detects which runtimes are installed, registers the marketplace, installs every plugin.
# Safe under both `.\install.ps1` and `iwr ... | iex` (no `exit` — uses `return`).
$ErrorActionPreference = 'Continue'

$Marketplace = 'war3water/Minakami_plugins'
$MarketplaceName = 'minakami-plugins'
$Plugins = @('agent-coord-bootstrap')

Write-Host 'Minakami Plugins installer'
Write-Host "  marketplace: $Marketplace"

$FoundAny = $false
$Failures = @()

if (Get-Command claude -ErrorAction SilentlyContinue) {
    $FoundAny = $true
    Write-Host ''
    Write-Host '[claude] registering marketplace'
    & claude plugin marketplace add $Marketplace
    if ($LASTEXITCODE -ne 0) {
        # tolerate an already-registered marketplace; refresh it instead
        & claude plugin marketplace update $MarketplaceName
        if ($LASTEXITCODE -ne 0) { $Failures += 'claude: marketplace add/update failed' }
    }
    foreach ($p in $Plugins) {
        Write-Host "[claude] installing $p"
        & claude plugin install "$p@$MarketplaceName"
        if ($LASTEXITCODE -ne 0) { $Failures += "claude: install $p failed" }
    }
} else {
    Write-Host '[claude] not found on PATH - skipping'
}

if (Get-Command codex -ErrorAction SilentlyContinue) {
    $FoundAny = $true
    Write-Host ''
    Write-Host '[codex] registering marketplace'
    & codex plugin marketplace add $Marketplace
    if ($LASTEXITCODE -ne 0) {
        & codex plugin marketplace upgrade $MarketplaceName
        if ($LASTEXITCODE -ne 0) { $Failures += 'codex: marketplace add/upgrade failed' }
    }
    foreach ($p in $Plugins) {
        Write-Host "[codex] installing $p"
        & codex plugin add "$p@$MarketplaceName"
        if ($LASTEXITCODE -ne 0) { $Failures += "codex: add $p failed" }
    }
} else {
    Write-Host '[codex] not found on PATH - skipping'
}

if (-not $FoundAny) {
    Write-Host ''
    Write-Host 'Neither claude nor codex was found on PATH.'
    Write-Host 'Install at least one runtime and re-run this script.'
    $global:LASTEXITCODE = 1
    return
}

if ($Failures.Count -gt 0) {
    Write-Host ''
    Write-Host 'FAILED steps:'
    foreach ($f in $Failures) { Write-Host "  - $f" }
    $global:LASTEXITCODE = 1
    return
}

Write-Host ''
Write-Host "Done. Try '/init-agent-coord' in any project root - fresh or existing."
