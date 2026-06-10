#!/usr/bin/env bash
# Sync the duplicated manifest pairs (canonical → mirror) and verify parity.
# Run from the repo root before committing manifest changes.
set -euo pipefail

cd "$(dirname "$0")/.."

cp agent-coord-bootstrap/.codex-plugin/plugin.json agent-coord-bootstrap/.claude-plugin/plugin.json
cp .agents/plugins/marketplace.json .claude-plugin/marketplace.json

diff agent-coord-bootstrap/.codex-plugin/plugin.json agent-coord-bootstrap/.claude-plugin/plugin.json
diff .agents/plugins/marketplace.json .claude-plugin/marketplace.json

echo "Manifest pairs are in sync."
