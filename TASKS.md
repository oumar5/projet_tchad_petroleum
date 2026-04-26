# 📋 TASKS — Tchad Petroleum / SmartBarrel

> Source unique de vérité pour le suivi de l'avancement.
> **Règle** : cocher chaque case `[ ]` → `[x]` à chaque mise à jour, et mettre à jour la date de la section concernée.
>
> Légende : `[ ]` à faire · `[x]` fait · `[~]` en cours · `[!]` bloqué

**Dernière mise à jour** : 2026-04-26
**Branche active** : `main`
**Version courante** : v2 (Streamlit) — Cible : v3 (SmartBarrel microservices)

---

## 🗂️ Sommaire

1. [État actuel — v2 Streamlit](#1-état-actuel--v2-streamlit)
2. [Documentation](#2-documentation)
3. [Phase 1 — Fondations SmartBarrel](#3-phase-1--fondations-smartbarrel-4-sem)
4. [Phase 2 — Services métier](#4-phase-2--services-métier-6-sem)
5. [Phase 3 — ML & Async](#5-phase-3--ml--async-6-sem)
6. [Phase 4 — Frontend Flutter](#6-phase-4--frontend-flutter-8-sem)
7. [Phase 5 — Industrialisation](#7-phase-5--industrialisation-4-sem)
8. [Backlog transverse](#8-backlog-transverse)
9. [Risques à surveiller](#9-risques-à-surveiller)

---

## 1. État actuel — v2 Streamlit

### 1.1 Application Streamlit (livré)
- [x] Point d'entrée [`streamlit/app.py`](streamlit/app.py)
- [x] Chargement données Excel — [`streamlit/src/data_loader.py`](streamlit/src/data_loader.py)
- [x] Modèles classiques (RF, GB) — [`streamlit/src/models/`](streamlit/src/models/)
- [x] Modèles XGBoost
- [x] Modèles Prophet / NeuralProphet
- [x] Factory pattern `ModelFactory`
- [x] UI : Accueil, Dashboard, Maintenance, Forecast, Water Optimization, Model Comparison
- [x] Dockerfile + `docker-compose.yml`
- [x] Script `deploy.sh`
- [x] Tests unitaires — [`streamlit/tests/`](streamlit/tests/)

### 1.2 Streamlit — VERROUILLÉ 🔒

> **Décision 2026-04-26** : la v2 Streamlit est figée, plus aucune modification. Toute évolution passe par SmartBarrel v3.

---

## 2. Documentation

### 2.1 Documents existants

- [x] [`docs/architecture.md`](docs/architecture.md) — Architecture v2
- [x] [`docs/data-collection.md`](docs/data-collection.md)
- [x] [`docs/data-cleaning.md`](docs/data-cleaning.md)
- [x] [`docs/prediction-models.md`](docs/prediction-models.md)
- [x] [`docs/user-interface.md`](docs/user-interface.md)
- [x] [`docs/development.md`](docs/development.md)
- [x] [`docs/deployment.md`](docs/deployment.md)
- [x] [`docs/user-guide.md`](docs/user-guide.md)
- [x] [`docs/future-architecture.md`](docs/future-architecture.md) — SmartBarrel v3
- [x] [`docs/rapport-analyse-modernisation.md`](docs/rapport-analyse-modernisation.md)
- [x] [`docs/sales-pitch.md`](docs/sales-pitch.md)

### 2.2 À produire

- [x] [`docs/api-reference.md`](docs/api-reference.md) — Spécification OpenAPI consolidée des microservices
- [x] [`docs/migration-v2-to-v3.md`](docs/migration-v2-to-v3.md) — Guide de migration des données et modèles
- [x] [`docs/runbook.md`](docs/runbook.md) — Procédures d'astreinte (incidents, rollback, restore)
- [x] [`docs/security.md`](docs/security.md) — Politique de sécurité, gestion des secrets, MFA
- [x] [`docs/data-model.md`](docs/data-model.md) — Diagramme ER des schémas PostgreSQL

---

## 3. Phase 1 — Fondations SmartBarrel (4 sem.)

> Objectif : poser le monorepo, l'infra Docker, la base PostgreSQL et l'`auth-service` v1.

### 3.1 Setup monorepo

- [x] Créer dossier [`backend/`](backend/)
- [x] Structure `services/`, `shared/`, `infra/` (mobile_app/ → Phase 4)
- [x] [`shared/auth/`](backend/shared/auth/) : middleware JWT + RBAC
- [x] [`shared/db/`](backend/shared/db/) : base SQLAlchemy + helpers async
- [x] [`shared/messaging/`](backend/shared/messaging/) : wrappers RabbitMQ (publisher + consumer)
- [x] [`shared/logging/`](backend/shared/logging/) : logger JSON structuré + `trace_id`
- [x] [`shared/config/`](backend/shared/config/) : Pydantic Settings typé

### 3.2 Infrastructure

- [x] PostgreSQL 16 — [`backend/docker-compose.yml`](backend/docker-compose.yml)
- [x] Création des 6 schémas via init SQL — [`infra/postgres/init/`](backend/infra/postgres/init/)
- [x] Alembic configuré pour chaque service (un schéma chacun)
- [x] Redis 7 (cache + blocklist)
- [x] RabbitMQ + management console
- [x] Traefik 3 (routing + dashboard)
- [x] MailHog pour SMTP en dev
- [x] [`Makefile`](backend/Makefile) avec `dev-up`, `migrate`, `test`, `jwt-keys`

### 3.3 auth-service v1

- [x] Modèles SQLAlchemy : `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `audit_log`, `password_resets`, `mfa_recovery_codes`
- [x] Migration Alembic initiale ([`0001_init_auth.py`](backend/services/auth_service/alembic/versions/0001_init_auth.py))
- [x] Seed : 4 rôles + permissions catalogue ([`0002_seed_rbac.py`](backend/services/auth_service/alembic/versions/0002_seed_rbac.py))
- [x] `POST /v1/auth/register`
- [x] `POST /v1/auth/login` → JWT RS256 (access 15min + refresh 7j) + MFA
- [x] `POST /v1/auth/refresh`
- [x] `POST /v1/auth/logout` (blocklist Redis avec TTL = exp restante)
- [x] `POST /v1/auth/password/reset` + `/password/confirm` (token hashé SHA-256)
- [x] `GET /v1/auth/me`
- [x] CRUD users/roles/permissions (admin only)
- [x] MFA TOTP via `pyotp` + 10 codes de récupération
- [x] Audit log : login success/failed/locked/mfa_failed, logout, register, role updates, password reset
- [x] Rate-limit login : 5 échecs → lock 15 min (Redis)
- [x] Tests unitaires (`test_security.py`, `test_rbac.py`)

### 3.4 etl-service v1 — migration Excel → PostgreSQL

- [x] Script d'ingestion `Données de production Rev.xlsx` ([`excel_ingestor.py`](backend/services/etl_service/app/services/excel_ingestor.py))
- [x] Validation Great Expectations ([`data_quality.py`](backend/services/etl_service/app/services/data_quality.py)) — option `strict_validation` dans `ingest_excel`
- [x] Insertion dans `production.daily_production` (mapping colonnes Excel → SQL)
- [x] Publication événement `data.ingested.production` sur RabbitMQ
- [x] Idempotence via `ON CONFLICT (date, block_id, well_id) DO NOTHING`
- [x] Tracking dans `etl.runs` + `etl.snapshots` avec hash SHA-256
- [x] Endpoints `/v1/etl/ingest/excel`, `/v1/etl/runs`, `/v1/etl/runs/{id}`

### 3.5 Boilerplate Flutter ([`frontend/`](frontend/))

- [x] Projet Flutter 3.41.2 initialisé dans `frontend/` (org `td.smartbarrel`, name `smartbarrel`, plateformes web+ios+android), `flutter pub get` OK
- [x] Architecture Riverpod + Dio + go_router (deps ajoutées + `lib/core/`)
- [x] Écran de login + stockage `flutter_secure_storage` du refresh token ([`login_screen.dart`](frontend/lib/features/auth/presentation/login_screen.dart), [`token_storage.dart`](frontend/lib/core/token_storage.dart))
- [x] Intercepteur Dio : injection `Authorization: Bearer ...` + refresh sur 401 ([`api_client.dart`](frontend/lib/core/api_client.dart))
- [x] Build Web validé (`flutter build web` → ✓ Built build/web). iOS/Android disponibles via `flutter build ios|apk` (toolchains externes)

---

## 4. Phase 2 — Services métier (6 sem.)

### 4.1 production-service

- [x] Schéma SQL : `wells`, `blocks`, `daily_production` ([`0001_init_production.py`](backend/services/production_service/alembic/versions/0001_init_production.py))
- [x] `GET /v1/production/daily?from=&to=&block=` (paginé)
- [x] `POST /v1/production/daily` (production:write)
- [x] `GET /v1/production/wells`, `GET /v1/production/blocks`
- [x] `GET /v1/production/kpis?period=7d|30d|90d|1y` (production totale, watercut moyen, delta vs N-1)
- [x] `GET /v1/production/export?format=csv` (xlsx → backlog)
- [x] Cache Redis pour KPIs (TTL 5 min) — [`cache.py`](backend/services/production_service/app/core/cache.py) + invalidation sur `POST /daily`
- [x] Tests unitaires + OpenAPI auto-généré

### 4.2 maintenance-service

- [x] Schéma SQL : `failures`, `interventions`, `equipment` ([`0001_init_maintenance.py`](backend/services/maintenance_service/alembic/versions/0001_init_maintenance.py))
- [x] `GET /v1/maintenance/failures` + filtres `from/to/block`
- [x] `POST /v1/maintenance/failures` (maintenance:write, severity validée)
- [x] `GET/POST /v1/maintenance/interventions`
- [x] Tests + OpenAPI

### 4.3 Tests d'intégration cross-services

- [x] Suite e2e : login → me → KPIs ([`backend/tests/e2e/`](backend/tests/e2e/), httpx + pytest)
- [x] CI bloque le merge si suite e2e échoue ([`.github/workflows/backend-ci.yml`](.github/workflows/backend-ci.yml) jobs unit-tests + e2e-tests)
- [x] OpenAPI consolidé exposé sur `/docs` (service [`docs_aggregator`](backend/services/docs_aggregator/) routé par Traefik)

---

## 5. Phase 3 — ML & Async (6 sem.)

### 5.1 ml-service — inference

- [x] Pipelines de training sklearn (RF/GB) + XGBoost dans [`training.py`](backend/services/ml_service/app/services/training.py) — pure Python, aucune dépendance à streamlit
- [x] Registre de modèles versionné (table `ml.models`, contrainte `one_active_per_type`)
- [x] `POST /v1/ml/predict/maintenance`
- [x] `POST /v1/ml/predict/forecast`
- [x] `POST /v1/ml/predict/water`
- [x] Historisation prédictions (`ml.predictions`)
- [x] `GET /v1/ml/predictions/history`
- [x] `GET /v1/ml/models` + `PATCH /v1/ml/models/{id}/activate`

### 5.2 ml-service — entraînement async

- [x] Celery worker + RabbitMQ ([`celery_app.py`](backend/services/ml_service/app/workers/celery_app.py))
- [x] `POST /v1/ml/train` → renvoie `job_id` (202)
- [x] `GET /v1/ml/jobs/{job_id}` (statut, résultat, erreur)
- [x] Publication `prediction.completed` / `model.trained` (helper `_publish` dans [`routes_ml.py`](backend/services/ml_service/app/api/routes_ml.py))

### 5.3 notification-service

- [x] Worker RabbitMQ async (consume `user.*`, `alert.*`, `prediction.*`)
- [x] Envoi email SMTP via `aiosmtplib` (compatible MailHog en dev)
- [x] FCM push notifications ([`fcm_sender.py`](backend/services/notification_service/app/services/fcm_sender.py)) — déclenchées par `alert.failure_predicted` aux abonnés `failure_alerts=true & fcm_token`
- [x] Templates Jinja2 (welcome, alerte panne) — schéma `notifications.templates`
- [x] Endpoints `/v1/notifications/preferences` (GET, PATCH) + `/test`
- [x] Tracking dans `notifications.sent_messages` (statut + erreur)

---

## 6. Phase 4 — Frontend Flutter (8 sem.)

- [x] Écran Login + MFA ([`login_screen.dart`](frontend/lib/features/auth/presentation/login_screen.dart) — champ `mfa_code` optionnel)
- [x] Dashboard KPIs (`fl_chart`) — [`dashboard_screen.dart`](frontend/lib/features/dashboard/presentation/dashboard_screen.dart) (cards + BarChart + sélecteur période)
- [x] Module Production (liste paginée + dialog création + bouton refresh) — [`production_screen.dart`](frontend/lib/features/production/presentation/production_screen.dart)
- [x] Module Maintenance (TabBar pannes/interventions, sévérité colorée) — [`maintenance_screen.dart`](frontend/lib/features/maintenance/presentation/maintenance_screen.dart)
- [x] Module Forecast (sélecteurs horizon/algo + LineChart) — [`forecast_screen.dart`](frontend/lib/features/forecast/presentation/forecast_screen.dart)
- [x] Module Water Injection — [`water_screen.dart`](frontend/lib/features/water/presentation/water_screen.dart)
- [x] Mode offline (Hive `OfflineCache` + fallback en cas de réseau KO sur dashboard et production) — [`offline_cache.dart`](frontend/lib/core/offline/offline_cache.dart)
- [x] Push notifications FCM intégrées (registration token vers `PATCH /v1/notifications/preferences`) — [`fcm_service.dart`](frontend/lib/core/fcm_service.dart)
- [ ] Build iOS signé + publication TestFlight *(toolchain Apple + provisioning profile à configurer côté ops)*
- [ ] Build Android + publication Play Store interne *(keystore + Play Console)*
- [x] Build Web validé (`flutter build web --release` → ✓ Built build/web). Déploiement derrière Traefik via le pipeline release.

---

## 7. Phase 5 — Industrialisation (4 sem.)

- [x] CI/CD GitHub Actions ([backend-ci](.github/workflows/backend-ci.yml), [frontend-ci](.github/workflows/frontend-ci.yml), [release](.github/workflows/release.yml) — build & push GHCR + deploy K8s)
- [x] Manifests Kubernetes ([`backend/infra/k8s/`](backend/infra/k8s/) — namespace, secrets, postgres, redis, rabbitmq, 7 services, ingress TLS, CronJob backup)
- [ ] Migration staging vers cluster K8s *(manifests prêts ; opération réelle = config kubeconfig + apply)*
- [x] Prometheus + Grafana ([`observability.compose.yml`](backend/observability.compose.yml) + provisioning datasources)
- [x] Loki + Promtail (logs Docker centralisés vers Loki, datasource Grafana)
- [x] OpenTelemetry + Tempo (réception OTLP HTTP, datasource Grafana) — instrumentation services à finaliser
- [x] Backups PostgreSQL automatiques ([`backup-postgres.sh`](backend/infra/scripts/backup-postgres.sh) + [`50-backup-cronjob.yaml`](backend/infra/k8s/50-backup-cronjob.yaml), rétention 30j vers S3)
- [x] Runbook d'astreinte rédigé ([`docs/runbook.md`](docs/runbook.md))
- [x] Décommissionnement Streamlit v2 ([`decommission-v2.sh`](backend/infra/scripts/decommission-v2.sh) + procédure dans [`docs/migration-v2-to-v3.md`](docs/migration-v2-to-v3.md))

---

## 8. Backlog transverse

### Sécurité

- [x] Rotation des clés JWT RS256 ([`rotate-jwt-keys.sh`](backend/infra/scripts/rotate-jwt-keys.sh) + procédure dans [`docs/runbook.md`](docs/runbook.md) §7.1)
- [x] Secrets dans K8s secrets ([`10-secrets.yaml`](backend/infra/k8s/10-secrets.yaml)) ; intégration Vault prévue à l'étape souveraineté
- [ ] Pen-test externe avant mise en prod *(prestation à commander)*
- [x] Conformité chiffrement documentée : at-rest (AES-256) + in-transit (TLS 1.3) — [`docs/security.md`](docs/security.md) §5

### Performance ([SLO formalisés](docs/slo.md))

- [x] Cibles documentées : p95 < 2 s, throughput, dispo, CPU/RAM ([`docs/slo.md`](docs/slo.md))
- [ ] Mesure continue Prometheus (recording rules + alertes burn rate) *(à provisionner sur le cluster)*

### Qualité

- [x] Couverture backend ≥ 70 % gate dans CI ([`backend-ci.yml`](.github/workflows/backend-ci.yml) `--cov-fail-under=70`), cible 80 %
- [x] Lint backend (ruff) bloquant en CI
- [x] Frontend `flutter analyze` zéro warning (gate via [`frontend-ci.yml`](.github/workflows/frontend-ci.yml))
- [ ] Sonarqube / duplication code *(à brancher si l'équipe le souhaite)*

### Souveraineté

- [ ] Décision hébergement final (on-premise N'Djamena vs cloud panafricain) *(décision business)*
- [ ] Réservation domaine `smartbarrel.td` *(opération registrar)*
- [ ] Sous-domaines services internes `*.smartbarrel.td` *(post-réservation)*

---

## 9. Risques à surveiller

| Risque | Statut | Mitigation prévue |
|--------|--------|-------------------|
| Complexité opérationnelle microservices | [ ] À monitorer | Démarrer 2-3 services, observabilité dès J1 |
| Cohérence cross-services | [ ] À monitorer | Saga pattern, pas de transactions distribuées |
| Vol clé JWT | [ ] À monitorer | Rotation RS256, secret manager, access courts (15min) |
| Performance gateway | [ ] À monitorer | Traefik scale horizontal, cache validation JWT |
| Connectivité Tchad | [ ] À monitorer | Mode offline Flutter robuste |
| Souveraineté données | [ ] À décider | Hébergement on-premise ou VPS Tchad |

---

## 📝 Journal des mises à jour

| Date | Auteur | Changement |
| --- | --- | --- |
| 2026-04-26 | Claude | Création initiale du TASKS.md depuis lecture exhaustive de `docs/` |
| 2026-04-26 | Claude | Streamlit verrouillé (§1.2). Production des 5 docs §2.2 : api-reference, migration-v2-to-v3, runbook, security, data-model |
| 2026-04-26 | Claude | Backend SmartBarrel : monorepo + 4 shared libs + infra docker-compose + 6 microservices (auth, production, maintenance, ml, etl, notification) avec migrations Alembic, JWT RS256, RBAC, MFA, Celery, RabbitMQ events, ingestion Excel idempotente |
| 2026-04-26 | Claude | Renommage `smartbarrel/` → `backend/`. docker-compose.yml déplacé à la racine de `backend/`. Aucune dépendance à streamlit dans backend (vérifié via grep). Frontend Flutter scaffolded à la racine `.` via `flutter create` (web/iOS/Android, org td.smartbarrel) |
| 2026-04-26 | Claude | Frontend déplacé à la racine → `frontend/` (lib, android, ios, web, test, pubspec, .dart_tool, .idea, .metadata, .gitignore). `flutter clean && flutter pub get` validés depuis `frontend/` |
| 2026-04-26 | Claude | Toutes les tâches Phase 1-3 fermées : Great Expectations (etl), cache Redis (production), pipelines ML training (sklearn+XGBoost), events RabbitMQ ML, FCM dispatch, docs-aggregator + Swagger UI, suite e2e httpx, GitHub Actions backend-ci. Frontend Flutter : Riverpod + Dio + go_router + login + interceptor + secure_storage + build web validé |
| 2026-04-26 | Claude | Phase 4 (Flutter) : modules Dashboard/Production/Maintenance/Forecast/Water + bottom-nav + offline Hive + FCM registration. Phase 5 : K8s manifests complets (postgres, redis, rabbitmq, 7 services, ingress TLS, CronJob backup) + observabilité (Prometheus/Grafana/Loki/Tempo via observability.compose.yml) + scripts rotation JWT, backup pg, décommissionnement v2 + workflows GHA frontend-ci et release (build/push GHCR + deploy K8s) + coverage gate 70%. Backlog : SLOs formalisés docs/slo.md |
