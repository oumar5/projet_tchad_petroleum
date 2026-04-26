# 📡 API Reference — SmartBarrel v3

> Spécification consolidée des endpoints REST exposés par les microservices SmartBarrel via l'API Gateway Traefik.
>
> **Base URL** : `https://api.smartbarrel.td/v1`
> **Auth** : `Authorization: Bearer <access_token>` (JWT RS256)
> **Format** : JSON ; erreurs au format RFC 7807 (Problem Details)
> **Versioning** : préfixe `/v1/` (breaking changes → `/v2/`)

---

## Sommaire

1. [Conventions](#1-conventions)
2. [auth-service](#2-auth-service)
3. [production-service](#3-production-service)
4. [maintenance-service](#4-maintenance-service)
5. [ml-service](#5-ml-service)
6. [etl-service](#6-etl-service)
7. [notification-service](#7-notification-service)
8. [Codes d'erreur](#8-codes-derreur)
9. [Rate limiting](#9-rate-limiting)

---

## 1. Conventions

### 1.1 Headers communs

| Header | Obligatoire | Description |
|--------|-------------|-------------|
| `Authorization` | Oui (sauf `/auth/login`, `/auth/register`) | `Bearer <jwt>` |
| `Content-Type` | Oui sur POST/PATCH | `application/json` |
| `X-Request-Id` | Recommandé | UUID propagé dans les logs (`trace_id`) |
| `Accept-Language` | Non | `fr` (défaut) ou `en` |

### 1.2 Pagination

Tous les endpoints `GET` listant des ressources acceptent :

```
?page=1&page_size=50&sort=-created_at
```

Réponse :

```json
{
  "items": [...],
  "page": 1,
  "page_size": 50,
  "total": 1234,
  "total_pages": 25
}
```

### 1.3 Filtres temporels

Les endpoints chronologiques acceptent `from` et `to` au format ISO 8601 (UTC) :

```
?from=2025-01-01T00:00:00Z&to=2025-12-31T23:59:59Z
```

### 1.4 RBAC requis

Chaque endpoint indique la permission minimale requise. Les wildcards sont supportés (`production:*`, `*:*` pour admin).

---

## 2. auth-service

Base : `/v1/auth`

### 2.1 Inscription

```
POST /v1/auth/register
```

Body :
```json
{ "email": "user@smartbarrel.td", "password": "...", "full_name": "..." }
```

Réponse `201` :
```json
{ "id": "uuid", "email": "...", "roles": ["viewer"] }
```

### 2.2 Login

```
POST /v1/auth/login
```

Body :
```json
{ "email": "...", "password": "...", "mfa_code": "123456" }
```

Réponse `200` :
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

### 2.3 Refresh

```
POST /v1/auth/refresh
```

Body : `{ "refresh_token": "..." }` → renvoie un nouveau `access_token`.

### 2.4 Logout

```
POST /v1/auth/logout
```

Ajoute le refresh à la blocklist Redis (TTL = exp restante).

### 2.5 Profil

```
GET /v1/auth/me
```

Réponse :
```json
{
  "id": "uuid",
  "email": "...",
  "full_name": "...",
  "roles": ["engineer"],
  "permissions": ["production:read", "production:write", "ml:predict"]
}
```

### 2.6 Reset password

```
POST /v1/auth/password/reset       # demande email
POST /v1/auth/password/confirm     # body: { token, new_password }
```

### 2.7 Administration

| Méthode | Path | Permission |
|---------|------|------------|
| `POST` | `/v1/auth/users` | `users:write` |
| `GET` | `/v1/auth/users` | `users:read` |
| `PATCH` | `/v1/auth/users/{id}/roles` | `users:write` |
| `DELETE` | `/v1/auth/users/{id}` | `users:delete` |
| `GET` | `/v1/auth/roles` | `roles:read` |
| `POST` | `/v1/auth/roles` | `roles:write` |
| `GET` | `/v1/auth/permissions` | `roles:read` |
| `GET` | `/v1/auth/audit` | `audit:read` |

---

## 3. production-service

Base : `/v1/production`

### 3.1 Production journalière

```
GET /v1/production/daily?from=&to=&block=&well=
```
Permission : `production:read`

Réponse (extrait) :
```json
{
  "items": [
    {
      "date": "2025-04-26",
      "block": "X",
      "wells_total": 18,
      "wells_active": 16,
      "oil_bbl": 4250.5,
      "water_bbl": 7910.2,
      "watercut_pct": 65.05,
      "wor": 1.86
    }
  ]
}
```

```
POST /v1/production/daily
```
Permission : `production:write`

### 3.2 Référentiels

```
GET /v1/production/wells
GET /v1/production/blocks
```
Permission : `production:read`

### 3.3 KPIs

```
GET /v1/production/kpis?period=7d|30d|90d|1y
```

Réponse :
```json
{
  "period": "30d",
  "production_total_bbl": 127500,
  "production_avg_bbl_day": 4250,
  "watercut_avg_pct": 64.2,
  "active_wells_avg": 45,
  "delta_vs_previous_pct": 2.1
}
```

### 3.4 Export

```
GET /v1/production/export?format=csv|xlsx|json&from=&to=
```
Permission : `production:export`

---

## 4. maintenance-service

Base : `/v1/maintenance`

### 4.1 Pannes

```
GET /v1/maintenance/failures?from=&to=&block=&pump_type=
POST /v1/maintenance/failures
```

Body POST :
```json
{
  "notification_date": "2025-04-26",
  "block": "Y",
  "pump_id": "P-Y-04",
  "failure_type": "ESP_motor",
  "severity": "high"
}
```

### 4.2 Interventions

```
GET /v1/maintenance/interventions?from=&to=
POST /v1/maintenance/interventions
PATCH /v1/maintenance/interventions/{id}
```

### 4.3 Statut équipements

```
GET /v1/maintenance/equipment/{id}/status
```

---

## 5. ml-service

Base : `/v1/ml`

### 5.1 Prédictions synchrones

```
POST /v1/ml/predict/maintenance
```
Permission : `ml:predict`

Body :
```json
{
  "block": "Y",
  "horizon_days": 30,
  "model_id": "rf_v3"
}
```

Réponse :
```json
{
  "block": "Y",
  "predictions": [
    { "well": "Y-04", "failure_probability": 0.72, "expected_failure_date": "2025-05-08" }
  ],
  "model": { "id": "rf_v3", "algorithm": "random_forest", "trained_at": "2025-04-20" }
}
```

```
POST /v1/ml/predict/forecast
POST /v1/ml/predict/water
```

### 5.2 Entraînement asynchrone

```
POST /v1/ml/train
```
Permission : `ml:train`

Body :
```json
{ "model_type": "production_forecast", "algorithm": "xgboost", "params": {...} }
```

Réponse `202` :
```json
{ "job_id": "uuid", "status": "queued", "links": { "self": "/v1/ml/jobs/uuid" } }
```

```
GET /v1/ml/jobs/{job_id}
```

### 5.3 Registre des modèles

```
GET /v1/ml/models?type=&algorithm=&active=true
GET /v1/ml/models/{id}
PATCH /v1/ml/models/{id}/activate
```

### 5.4 Historique des prédictions

```
GET /v1/ml/predictions/history?from=&to=&type=
```

---

## 6. etl-service

Base : `/v1/etl`

```
POST /v1/etl/ingest/excel       # multipart/form-data, fichier .xlsx
GET  /v1/etl/runs?status=
GET  /v1/etl/runs/{id}
```

Permission : `production:write` + `maintenance:write`.

Publication événement RabbitMQ : `data.ingested.production` à la fin du run.

---

## 7. notification-service

Base : `/v1/notifications`

```
GET    /v1/notifications/preferences
PATCH  /v1/notifications/preferences
POST   /v1/notifications/test       # admin uniquement, déclenche un envoi
```

Le service consomme principalement RabbitMQ — cf. [`docs/future-architecture.md`](future-architecture.md) §7.

---

## 8. Codes d'erreur

Format RFC 7807 :

```json
{
  "type": "https://smartbarrel.td/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Missing permission: production:write",
  "instance": "/v1/production/daily",
  "trace_id": "abc-123"
}
```

| Code HTTP | Cas d'usage |
|-----------|-------------|
| `400` | Validation Pydantic échouée |
| `401` | JWT manquant, expiré ou invalide |
| `403` | Permission RBAC manquante |
| `404` | Ressource inexistante |
| `409` | Conflit (doublon, état incompatible) |
| `422` | Body bien formé mais sémantiquement invalide |
| `429` | Rate limit dépassé |
| `500` | Erreur serveur (incident) |
| `503` | Service indisponible (maintenance, dépendance KO) |

---

## 9. Rate limiting

Appliqué par Traefik au niveau du gateway :

| Scope | Limite |
|-------|--------|
| Anonyme (`/auth/login`, `/auth/register`) | 10 req/min/IP |
| Authentifié (lecture) | 600 req/min/user |
| Authentifié (écriture) | 120 req/min/user |
| `/ml/train` | 5 req/h/user |

Headers retournés : `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

---

*Document vivant — généré à partir des OpenAPI de chaque service. Source de vérité : `services/*/openapi.json` consolidé sur `https://api.smartbarrel.td/docs`.*
