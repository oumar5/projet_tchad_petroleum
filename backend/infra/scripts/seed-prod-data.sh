#!/usr/bin/env bash
# Seed la base avec le fichier Excel "Données de production Rev.xlsx"
# en passant par l'endpoint REST /v1/etl/ingest/excel.
#
# Pré-requis :
#   1. Stack démarrée (make dev-up)
#   2. Comptes dev créés (make seed-users)
set -euo pipefail

API="${API_BASE_URL:-http://api.localhost}"
EMAIL="${SEED_USER:-engineer@smartbarrel.td}"
PASSWORD="${SEED_PASSWORD:-Engineer-Pa\$\$word-12345}"

# Localiser le fichier Excel : repo_root/data/...
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EXCEL_FILE="${EXCEL_FILE:-$REPO_ROOT/data/Données de production Rev.xlsx}"

if [ ! -f "$EXCEL_FILE" ]; then
  echo "✗ Fichier introuvable: $EXCEL_FILE" >&2
  exit 1
fi

echo "→ Login en tant que $EMAIL"
LOGIN_BODY=$(printf '{"email":"%s","password":"%s"}' "$EMAIL" "$PASSWORD")
TOKEN=$(curl -fsS -X POST "$API/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$LOGIN_BODY" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

if [ -z "$TOKEN" ]; then
  echo "✗ Login échoué" >&2
  exit 1
fi
echo "  ✓ token obtenu"

echo "→ Upload de $(basename "$EXCEL_FILE") vers $API/v1/etl/ingest/excel"
RESPONSE=$(curl -fsS -X POST "$API/v1/etl/ingest/excel?label=seed-baseline" \
  -H "Authorization: Bearer $TOKEN" \
  -F "upload=@${EXCEL_FILE};type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

echo "  ✓ ingestion terminée :"
echo "$RESPONSE" | python3 -m json.tool
