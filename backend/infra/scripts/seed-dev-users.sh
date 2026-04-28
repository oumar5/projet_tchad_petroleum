#!/usr/bin/env bash
# Seed des 4 comptes de dev (un par rôle RBAC).
# Pré-requis : stack docker compose démarrée et migrations appliquées.
set -euo pipefail

API="${API_BASE_URL:-http://api.localhost}"

reg_or_skip() {
  local email="$1" pwd="$2" full="$3"
  local body
  body=$(printf '{"email":"%s","password":"%s","full_name":"%s"}' "$email" "$pwd" "$full")
  curl -fsS -o /dev/null -X POST "$API/v1/auth/register" \
       -H 'Content-Type: application/json' -d "$body" \
    && echo "  created  $email" \
    || echo "  exists   $email"
}

DEV_PWD="${DEV_PASSWORD:-123456}"

echo "→ Registering 4 dev users (password: $DEV_PWD)..."
reg_or_skip "admin@smartbarrel.td"    "$DEV_PWD" "Admin Dev"
reg_or_skip "engineer@smartbarrel.td" "$DEV_PWD" "Engineer Dev"
reg_or_skip "analyst@smartbarrel.td"  "$DEV_PWD" "Analyst Dev"
reg_or_skip "viewer@smartbarrel.td"   "$DEV_PWD" "Viewer Dev"

echo "→ Promoting roles via psql..."
docker compose -f smartbarrel.compose.yml exec -T postgres \
  psql -U smartbarrel -d smartbarrel_db <<'SQL'
INSERT INTO auth.user_roles (user_id, role_id)
SELECT u.id, r.id FROM auth.users u, auth.roles r
WHERE (u.email = 'admin@smartbarrel.td'    AND r.name = 'admin')
   OR (u.email = 'engineer@smartbarrel.td' AND r.name = 'engineer')
   OR (u.email = 'analyst@smartbarrel.td'  AND r.name = 'analyst')
ON CONFLICT DO NOTHING;
\echo
SELECT u.email, ARRAY_AGG(r.name ORDER BY r.name) AS roles
FROM auth.users u
JOIN auth.user_roles ur ON ur.user_id = u.id
JOIN auth.roles r ON r.id = ur.role_id
WHERE u.email IN ('admin@smartbarrel.td','engineer@smartbarrel.td',
                  'analyst@smartbarrel.td','viewer@smartbarrel.td')
GROUP BY u.email ORDER BY u.email;
SQL
