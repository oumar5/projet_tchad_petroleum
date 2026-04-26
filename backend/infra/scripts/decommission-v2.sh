#!/usr/bin/env bash
# Décommissionnement de la v2 Streamlit après 90j de bascule réussie.
# Cf. docs/migration-v2-to-v3.md §8 pour le contexte.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
ts=$(date -u +%F)
out="$ROOT/backups/decommission/v2-final-$ts.tar.gz"

echo "→ Archivage de la v2 Streamlit dans $out"
mkdir -p "$ROOT/backups/decommission"
tar -czf "$out" -C "$ROOT" streamlit/

echo "→ Tag git v2-final"
git -C "$ROOT" tag -a "v2-final-$ts" -m "Streamlit v2 archived for decommission"

echo "→ Le code source reste dans le repo (read-only)."
echo "→ Pour l'arrêt des conteneurs Streamlit, exécuter sur l'hôte cible :"
echo "    docker compose -f /chemin/streamlit/docker-compose.yml down"
echo "→ Mettre à jour README racine pour rediriger vers le frontend Flutter."

echo "Done."
