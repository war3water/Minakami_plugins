#!/usr/bin/env bash
# One-command install for Minakami Plugins.
# Detects which runtimes are installed, registers the marketplace, installs every plugin.
set -uo pipefail

MARKETPLACE="war3water/Minakami_plugins"
MARKETPLACE_NAME="minakami-plugins"
PLUGINS=("agent-coord-bootstrap")

echo "Minakami Plugins installer"
echo "  marketplace: ${MARKETPLACE}"

FOUND_ANY=0
FAILURES=()

if command -v claude >/dev/null 2>&1; then
  FOUND_ANY=1
  echo
  echo "[claude] registering marketplace"
  if ! claude plugin marketplace add "${MARKETPLACE}"; then
    # tolerate an already-registered marketplace; refresh it instead
    if ! claude plugin marketplace update "${MARKETPLACE_NAME}"; then
      FAILURES+=("claude: marketplace add/update failed")
    fi
  fi
  for p in "${PLUGINS[@]}"; do
    echo "[claude] installing ${p}"
    if ! claude plugin install "${p}@${MARKETPLACE_NAME}"; then
      FAILURES+=("claude: install ${p} failed")
    fi
  done
else
  echo "[claude] not found on PATH — skipping"
fi

if command -v codex >/dev/null 2>&1; then
  FOUND_ANY=1
  echo
  echo "[codex] registering marketplace"
  if ! codex plugin marketplace add "${MARKETPLACE}"; then
    if ! codex plugin marketplace upgrade "${MARKETPLACE_NAME}"; then
      FAILURES+=("codex: marketplace add/upgrade failed")
    fi
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
echo "Done. Try '/init-agent-coord' in any project root — fresh or existing."
