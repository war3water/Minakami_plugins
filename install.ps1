# One-command install for Minakami Plugins on Windows.
# Detects which runtimes are installed, registers the marketplace, installs every plugin.
$ErrorActionPreference = 'Continue'

$Marketplace = 'github:war3water/Minakami_plugins'
$Plugins = @('agent-coord-bootstrap')

Write-Host 'Minakami Plugins installer'
Write-Host "  marketplace: $Marketplace"

$InstalledAny = $false

if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Host ''
    Write-Host '[claude] registering marketplace'
    & claude plugin marketplace add $Marketplace
    foreach ($p in $Plugins) {
        Write-Host "[claude] installing $p"
        & claude plugin install "$p@minakami-plugins"
    }
    $InstalledAny = $true
} else {
    Write-Host '[claude] not found on PATH - skipping'
}

if (Get-Command codex -ErrorAction SilentlyContinue) {
    Write-Host ''
    Write-Host '[codex] registering marketplace'
    & codex plugin marketplace add $Marketplace
    foreach ($p in $Plugins) {
        Write-Host "[codex] installing $p"
        & codex plugin install $p
    }
    $InstalledAny = $true
} else {
    Write-Host '[codex] not found on PATH - skipping'
}

if (-not $InstalledAny) {
    Write-Host ''
    Write-Host 'Neither claude nor codex was found on PATH.'
    Write-Host 'Install at least one runtime and re-run this script.'
    exit 1
}

Write-Host ''
Write-Host "Done. Try '/init-agent-coord' in a fresh project."
