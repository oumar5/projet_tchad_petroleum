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

- [x] Créer dossier [`smartbarrel/`](smartbarrel/)
- [x] Structure `services/`, `shared/`, `infra/` (mobile_app/ → Phase 4)
- [x] [`shared/auth/`](smartbarrel/shared/auth/) : middleware JWT + RBAC
- [x] [`shared/db/`](smartbarrel/shared/db/) : base SQLAlchemy + helpers async
- [x] [`shared/messaging/`](smartbarrel/shared/messaging/) : wrappers RabbitMQ (publisher + consumer)
- [x] [`shared/logging/`](smartbarrel/shared/logging/) : logger JSON structuré + `trace_id`
- [x] [`shared/config/`](smartbarrel/shared/config/) : Pydantic Settings typé

### 3.2 Infrastructure

- [x] PostgreSQL 16 — [`smartbarrel/infra/docker-compose.dev.yml`](smartbarrel/infra/docker-compose.dev.yml)
- [x] Création des 6 schémas via init SQL — [`infra/postgres/init/`](smartbarrel/infra/postgres/init/)
- [x] Alembic configuré pour chaque service (un schéma chacun)
- [x] Redis 7 (cache + blocklist)
- [x] RabbitMQ + management console
- [x] Traefik 3 (routing + dashboard)
- [x] MailHog pour SMTP en dev
- [x] [`Makefile`](smartbarrel/Makefile) avec `dev-up`, `migrate`, `test`, `jwt-keys`

### 3.3 auth-service v1

- [x] Modèles SQLAlchemy : `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `audit_log`, `password_resets`, `mfa_recovery_codes`
- [x] Migration Alembic initiale ([`0001_init_auth.py`](smartbarrel/services/auth_service/alembic/versions/0001_init_auth.py))
- [x] Seed : 4 rôles + permissions catalogue ([`0002_seed_rbac.py`](smartbarrel/services/auth_service/alembic/versions/0002_seed_rbac.py))
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

- [x] Script d'ingestion `Données de production Rev.xlsx` ([`excel_ingestor.py`](smartbarrel/services/etl_service/app/services/excel_ingestor.py))
- [ ] Validation Great Expectations *(reporté Phase 2)*
- [x] Insertion dans `production.daily_production` (mapping colonnes Excel → SQL)
- [x] Publication événement `data.ingested.production` sur RabbitMQ
- [x] Idempotence via `ON CONFLICT (date, block_id, well_id) DO NOTHING`
- [x] Tracking dans `etl.runs` + `etl.snapshots` avec hash SHA-256
- [x] Endpoints `/v1/etl/ingest/excel`, `/v1/etl/runs`, `/v1/etl/runs/{id}`

### 3.5 Boilerplate Flutter
- [ ] Projet Flutter 3.x initialisé
- [ ] Architecture Riverpod + Dio + go_router
- [ ] Écran de login + stockage `flutter_secure_storage` du refresh token
- [ ] Intercepteur Dio : injection `Authorization: Bearer ...` + refresh sur 401
- [ ] Builds Web / iOS / Android lancent et atteignent l'écran login

---

## 4. Phase 2 — Services métier (6 sem.)

### 4.1 production-service

- [x] Schéma SQL : `wells`, `blocks`, `daily_production` ([`0001_init_production.py`](smartbarrel/services/production_service/alembic/versions/0001_init_production.py))
- [x] `GET /v1/production/daily?from=&to=&block=` (paginé)
- [x] `POST /v1/production/daily` (production:write)
- [x] `GET /v1/production/wells`, `GET /v1/production/blocks`
- [x] `GET /v1/production/kpis?period=7d|30d|90d|1y` (production totale, watercut moyen, delta vs N-1)
- [x] `GET /v1/production/export?format=csv` (xlsx → backlog)
- [ ] Cache Redis pour KPIs (TTL 5 min) *(à brancher)*
- [x] Tests unitaires + OpenAPI auto-généré

### 4.2 maintenance-service

- [x] Schéma SQL : `failures`, `interventions`, `equipment` ([`0001_init_maintenance.py`](smartbarrel/services/maintenance_service/alembic/versions/0001_init_maintenance.py))
- [x] `GET /v1/maintenance/failures` + filtres `from/to/block`
- [x] `POST /v1/maintenance/failures` (maintenance:write, severity validée)
- [x] `GET/POST /v1/maintenance/interventions`
- [x] Tests + OpenAPI

### 4.3 Tests d'intégration cross-services

- [ ] Suite e2e : login → création prod → KPIs *(à écrire dans `infra/tests/e2e/`)*
- [ ] CI bloque le merge si suite e2e échoue
- [ ] OpenAPI consolidé exposé sur `/docs` (Traefik)

---

## 5. Phase 3 — ML & Async (6 sem.)

### 5.1 ml-service — inference

- [ ] Réutilisation des modèles `streamlit/src/models/` *(stub : InferenceService prêt à charger des `.joblib`)*
- [x] Registre de modèles versionné (table `ml.models`, contrainte `one_active_per_type`)
- [x] `POST /v1/ml/predict/maintenance`
- [x] `POST /v1/ml/predict/forecast`
- [x] `POST /v1/ml/predict/water`
- [x] Historisation prédictions (`ml.predictions`)
- [x] `GET /v1/ml/predictions/history`
- [x] `GET /v1/ml/models` + `PATCH /v1/ml/models/{id}/activate`

### 5.2 ml-service — entraînement async

- [x] Celery worker + RabbitMQ ([`celery_app.py`](smartbarrel/services/ml_service/app/workers/celery_app.py))
- [x] `POST /v1/ml/train` → renvoie `job_id` (202)
- [x] `GET /v1/ml/jobs/{job_id}` (statut, résultat, erreur)
- [ ] Publication `prediction.completed` / `model.trained` *(handler à finaliser)*

### 5.3 notification-service

- [x] Worker RabbitMQ async (consume `user.*`, `alert.*`, `prediction.*`)
- [x] Envoi email SMTP via `aiosmtplib` (compatible MailHog en dev)
- [ ] FCM push notifications mobile *(stub à brancher Phase 4)*
- [x] Templates Jinja2 (welcome, alerte panne) — schéma `notifications.templates`
- [x] Endpoints `/v1/notifications/preferences` (GET, PATCH) + `/test`
- [x] Tracking dans `notifications.sent_messages` (statut + erreur)

---

## 6. Phase 4 — Frontend Flutter (8 sem.)

- [ ] Écran Login + MFA
- [ ] Dashboard KPIs (fl_chart)
- [ ] Module Production (liste, création, export)
- [ ] Module Maintenance (pannes, interventions)
- [ ] Module Forecast (prévision N jours, graphes)
- [ ] Module Water Injection
- [ ] Mode offline (Hive + sync différée à la reconnexion)
- [ ] Push notifications FCM intégrées
- [ ] Build iOS signé + publication TestFlight
- [ ] Build Android + publication Play Store interne
- [ ] Build Web déployé derrière Traefik

---

## 7. Phase 5 — Industrialisation (4 sem.)

- [ ] CI/CD GitHub Actions (test → build → deploy staging → deploy prod sur release)
- [ ] Manifests Kubernetes (`infra/k8s/`)
- [ ] Migration staging vers cluster K8s
- [ ] Prometheus + Grafana (dashboards par service)
- [ ] Loki (logs centralisés)
- [ ] OpenTelemetry + Tempo (tracing distribué)
- [ ] Backups PostgreSQL automatiques (pg_dump quotidien + rétention 30j)
- [ ] Runbook d'astreinte rédigé
- [ ] Décommissionnement Streamlit v2 (après validation parallèle)

---

## 8. Backlog transverse

### Sécurité
- [ ] Rotation des clés JWT RS256 (procédure documentée)
- [ ] Secrets dans Vault ou K8s secrets (jamais en clair)
- [ ] Pen-test externe avant mise en prod
- [ ] Conformité chiffrement at-rest (AES-256) + in-transit (TLS 1.3)

### Performance (cibles architecture.md §métriques)
- [ ] Temps de réponse API < 2 s p95
- [ ] Throughput > 100 req/s par service
- [ ] Disponibilité 99,9 %
- [ ] CPU < 70 % en moyenne, RAM < 80 %

### Qualité
- [ ] Couverture tests ≥ 80 % par service
- [ ] Complexité cyclomatique < 10
- [ ] Duplication code < 5 % (sonarqube ou similaire)

### Souveraineté
- [ ] Décision hébergement final (on-premise N'Djamena vs cloud panafricain)
- [ ] Réservation domaine `smartbarrel.td`
- [ ] Sous-domaines services internes `*.smartbarrel.td`

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
