#!/usr/bin/env bash
# One-command install for Minakami Plugins.
# Detects which runtimes are installed, registers the marketplace, installs every plugin.
set -euo pipefail

MARKETPLACE="github:war3water/Minakami_plugins"
PLUGINS=("agent-coord-bootstrap")

echo "Minakami Plugins installer"
echo "  marketplace: ${MARKETPLACE}"

INSTALLED_ANY=0

if command -v claude >/dev/null 2>&1; then
  echo
  echo "[claude] registering marketplace"
  claude plugin marketplace add "${MARKETPLACE}" || true
  for p in "${PLUGINS[@]}"; do
    echo "[claude] installing ${p}"
    claude plugin install "${p}@minakami-plugins" || true
  done
  INSTALLED_ANY=1
else
  echo "[claude] not found on PATH — skipping"
fi

if command -v codex >/dev/null 2>&1; then
  echo
  echo "[codex] registering marketplace"
  codex plugin marketplace add "${MARKETPLACE}" || true
  for p in "${PLUGINS[@]}"; do
    echo "[codex] installing ${p}"
    codex plugin install "${p}" || true
  done
  INSTALLED_ANY=1
else
  echo "[codex] not found on PATH — skipping"
fi

if [ "${INSTALLED_ANY}" -eq 0 ]; then
  echo
  echo "Neither claude nor codex was found on PATH."
  echo "Install at least one runtime and re-run this script."
  exit 1
fi

echo
echo "Done. Try '/init-agent-coord' in a fresh project."
