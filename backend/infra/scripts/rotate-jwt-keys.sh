#!/usr/bin/env bash
# Rotation des clés JWT RS256 — procédure sans downtime.
# Pré-requis : kubectl configuré sur le cluster cible.
set -euo pipefail

NS="${1:-smartbarrel}"
DIR=$(mktemp -d)
trap 'rm -rf "$DIR"' EXIT

echo "1) Génération de la nouvelle paire dans $DIR"
openssl genrsa -out "$DIR/private.pem" 4096
openssl rsa -in "$DIR/private.pem" -pubout -out "$DIR/public.pem"

echo "2) Déploiement de la nouvelle clé publique aux validateurs (en parallèle de l'ancienne)"
kubectl create configmap jwt-public-keys -n "$NS" \
  --from-file=current=infra/jwt/public.pem \
  --from-file=next="$DIR/public.pem" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "3) Rolling restart des services qui valident le JWT"
kubectl rollout restart deployment -n "$NS" -l role=jwt-validator
kubectl rollout status deployment -n "$NS" -l role=jwt-validator --timeout=5m

echo "4) Bascule de la clé privée sur auth-service"
kubectl create secret generic smartbarrel-jwt-keys -n "$NS" \
  --from-file=public.pem="$DIR/public.pem" \
  --from-file=private.pem="$DIR/private.pem" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment auth-service -n "$NS"
kubectl rollout status deployment auth-service -n "$NS" --timeout=5m

echo "5) Patientez 24h (durée max d'un access_token + refresh) avant de retirer l'ancienne clé."
echo "   Ensuite, ré-exécutez l'étape 2 avec uniquement current=public.pem (nouvelle)."

cp "$DIR/public.pem" infra/jwt/public.pem
cp "$DIR/private.pem" infra/jwt/private.pem
chmod 600 infra/jwt/private.pem

echo "Done."
