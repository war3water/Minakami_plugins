# One-command install for Minakami Plugins on Windows.
# Detects which runtimes are installed, registers the marketplace, installs every plugin.
# Safe under both `.\install.ps1` and `iwr ... | iex` (no `exit` — uses `return`).
$ErrorActionPreference = 'Continue'

$Marketplace = 'war3water/Minakami_plugins'
$MarketplaceName = 'minakami-plugins'
$Plugins = @('agent-coord-bootstrap', 'prompt-audit', 'code-map')

Write-Host 'Minakami Plugins installer'
Write-Host "  marketplace: $Marketplace"

$FoundAny = $false
$Failures = @()

if (Get-Command claude -ErrorAction SilentlyContinue) {
    $FoundAny = $true
    Write-Host ''
    Write-Host '[claude] registering marketplace'
    # add succeeds on an already-registered marketplace without refreshing it, so always refresh;
    # the refresh also fails when add did not register it, which is the failure that matters
    & claude plugin marketplace add $Marketplace
    & claude plugin marketplace update $MarketplaceName
    if ($LASTEXITCODE -ne 0) { $Failures += 'claude: marketplace add/update failed' }
    foreach ($p in $Plugins) {
        Write-Host "[claude] installing $p"
        & claude plugin install "$p@$MarketplaceName"
        if ($LASTEXITCODE -ne 0) { $Failures += "claude: install $p failed"; continue }
        # install leaves an already-installed plugin at its installed version; update brings it current
        & claude plugin update "$p@$MarketplaceName"
        if ($LASTEXITCODE -ne 0) { $Failures += "claude: update $p failed" }
    }
} else {
    Write-Host '[claude] not found on PATH - skipping'
}

if (Get-Command codex -ErrorAction SilentlyContinue) {
    $FoundAny = $true
    Write-Host ''
    Write-Host '[codex] registering marketplace'
    # same as above: add leaves an existing snapshot stale, so always upgrade it
    & codex plugin marketplace add $Marketplace
    & codex plugin marketplace upgrade $MarketplaceName
    if ($LASTEXITCODE -ne 0) { $Failures += 'codex: marketplace add/upgrade failed' }
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
Write-Host 'Done. Restart any running Claude Code or Codex session to load the new versions.'
Write-Host "To scaffold or upgrade a project's coordination docs (any project root):"
Write-Host '  Claude Code: /agent-coord-bootstrap:init-agent-coord'
Write-Host '  Codex CLI:   $agent-coord-bootstrap'
Write-Host "To audit a prompt's effectiveness for a target coding model:"
Write-Host '  Claude Code: /prompt-audit:audit-prompt'
Write-Host '  Codex CLI:   $prompt-audit'
Write-Host 'To build an interactive code map of the current repository:'
Write-Host '  Claude Code: /code-map:code-map'
Write-Host '  Codex CLI:   $code-map'
