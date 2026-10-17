#!/usr/bin/env bash
# One-command install for Minakami Plugins.
# Detects which runtimes are installed, registers the marketplace, installs every plugin.
set -uo pipefail

MARKETPLACE="war3water/Minakami_plugins"
MARKETPLACE_NAME="minakami-plugins"
PLUGINS=("agent-coord-bootstrap" "prompt-audit" "code-map")

echo "Minakami Plugins installer"
echo "  marketplace: ${MARKETPLACE}"

FOUND_ANY=0
FAILURES=()

if command -v claude >/dev/null 2>&1; then
  FOUND_ANY=1
  echo
  echo "[claude] registering marketplace"
  # add succeeds on an already-registered marketplace without refreshing it, so always refresh;
  # the refresh also fails when add did not register it, which is the failure that matters
  claude plugin marketplace add "${MARKETPLACE}"
  if ! claude plugin marketplace update "${MARKETPLACE_NAME}"; then
    FAILURES+=("claude: marketplace add/update failed")
  fi
  for p in "${PLUGINS[@]}"; do
    echo "[claude] installing ${p}"
    if ! claude plugin install "${p}@${MARKETPLACE_NAME}"; then
      FAILURES+=("claude: install ${p} failed")
      continue
    fi
    # install leaves an already-installed plugin at its installed version; update brings it current
    if ! claude plugin update "${p}@${MARKETPLACE_NAME}"; then
      FAILURES+=("claude: update ${p} failed")
    fi
  done
else
  echo "[claude] not found on PATH — skipping"
fi

if command -v codex >/dev/null 2>&1; then
  FOUND_ANY=1
  echo
  echo "[codex] registering marketplace"
  # same as above: add leaves an existing snapshot stale, so always upgrade it
  codex plugin marketplace add "${MARKETPLACE}"
  if ! codex plugin marketplace upgrade "${MARKETPLACE_NAME}"; then
    FAILURES+=("codex: marketplace add/upgrade failed")
  fi
  for p in "${PLUGINS[@]}"; do
    echo "[codex] installing ${p}"
    if ! codex plugin add "${p}@${MARKETPLACE_NAME}"; then
      FAILURES+=("codex: add ${p} failed")
    fi
  done
else
  echo "[codex] not found on PATH — skipping"
fi

if [ "${FOUND_ANY}" -eq 0 ]; then
  echo
  echo "Neither claude nor codex was found on PATH."
  echo "Install at least one runtime and re-run this script."
  exit 1
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo
  echo "FAILED steps:"
  for f in "${FAILURES[@]}"; do
    echo "  - ${f}"
  done
  exit 1
fi

echo
echo "Done. Restart any running Claude Code or Codex session to load the new versions."
echo "To scaffold or upgrade a project's coordination docs (any project root):"
echo "  Claude Code: /agent-coord-bootstrap:init-agent-coord"
echo "  Codex CLI:   \$init-agent-coord"
echo "To review a project's README against best practices for its type:"
echo "  Claude Code: /agent-coord-bootstrap:review-readme"
echo "  Codex CLI:   \$review-readme"
echo "To audit a prompt's effectiveness for a target coding model:"
echo "  Claude Code: /prompt-audit:audit-prompt"
echo "  Codex CLI:   \$prompt-audit"
echo "To build an interactive code map of the current repository:"
echo "  Claude Code: /code-map:code-map"
echo "  Codex CLI:   \$code-map"
