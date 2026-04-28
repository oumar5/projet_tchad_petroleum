#!/usr/bin/env bash
# Entraîne 3 modèles de base (un par model_type) à partir des données ingérées,
# puis affiche les métriques. Pré-requis : seed-users + seed-data.
set -euo pipefail

API="${API_BASE_URL:-http://api.localhost}"
EMAIL="${SEED_USER:-engineer@smartbarrel.td}"
PASSWORD="${SEED_PASSWORD:-123456}"
ALGO="${ML_ALGORITHM:-gradient_boosting}"

echo "→ Login en tant que $EMAIL"
TOKEN=$(curl -fsS -X POST "$API/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

train_one() {
  local model_type="$1"
  echo
  echo "→ Training: model_type=$model_type, algorithm=$ALGO"
  local job_response
  job_response=$(curl -fsS -X POST "$API/v1/ml/train" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"model_type\":\"$model_type\",\"algorithm\":\"$ALGO\",\"params\":{}}")
  local job_id
  job_id=$(echo "$job_response" | python3 -c 'import sys,json;print(json.load(sys.stdin)["job_id"])')
  echo "  job_id=$job_id"

  # Poll jusqu'à success/failed (max 5 min)
  local deadline=$(( $(date +%s) + 300 ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local job
    job=$(curl -fsS "$API/v1/ml/jobs/$job_id" -H "Authorization: Bearer $TOKEN")
    local status
    status=$(echo "$job" | python3 -c 'import sys,json;print(json.load(sys.stdin)["status"])')
    if [ "$status" = "success" ]; then
      echo "  ✓ status=success"
      echo "$job" | python3 -m json.tool | sed 's/^/    /'
      return 0
    fi
    if [ "$status" = "failed" ]; then
      echo "  ✗ status=failed"
      echo "$job" | python3 -m json.tool | sed 's/^/    /'
      return 1
    fi
    sleep 3
  done
  echo "  ✗ timeout"
  return 1
}

train_one maintenance
train_one forecast
train_one water

echo
echo "→ Modèles actifs en base :"
docker compose -f smartbarrel.compose.yml exec -T postgres \
  psql -U smartbarrel -d smartbarrel_db -c \
  "SELECT name, version, algorithm, model_type, is_active, metrics FROM ml.models WHERE is_active = true ORDER BY model_type;"
