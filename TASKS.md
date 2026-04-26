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
- [ ] Créer dossier `smartbarrel/` (ou nouveau repo)
- [ ] Structure `services/`, `mobile_app/`, `shared/`, `infra/`
- [ ] `shared/auth/` : middleware JWT + RBAC
- [ ] `shared/db/` : base SQLAlchemy + helpers
- [ ] `shared/messaging/` : wrappers RabbitMQ
- [ ] `shared/logging/` : logger JSON structuré + `trace_id`
- [ ] `shared/config/` : chargement `.env` typé (Pydantic Settings)

### 3.2 Infrastructure
- [ ] PostgreSQL 16 — `docker-compose.dev.yml`
- [ ] Création des 6 schémas : `auth`, `production`, `maintenance`, `ml`, `etl`, `notifications`
- [ ] Alembic configuré par service
- [ ] Redis 7 (cache + blocklist)
- [ ] RabbitMQ + console management
- [ ] Traefik (TLS local + routing)

### 3.3 auth-service v1
- [ ] Modèles SQLAlchemy : `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `audit_log`
- [ ] Migration Alembic initiale
- [ ] Seed : 4 rôles (admin, engineer, analyst, viewer) + permissions catalogue
- [ ] `POST /auth/register`
- [ ] `POST /auth/login` → JWT RS256 (access 15min + refresh 7j)
- [ ] `POST /auth/refresh`
- [ ] `POST /auth/logout` (blocklist Redis)
- [ ] `POST /auth/password/reset`
- [ ] `GET /auth/me`
- [ ] CRUD users/roles/permissions (admin only)
- [ ] MFA TOTP (`pyotp`)
- [ ] Audit log automatique (login, logout, role_granted)
- [ ] Tests unitaires + intégration (≥ 80 % couverture)

### 3.4 etl-service v1 — migration Excel → PostgreSQL
- [ ] Script d'ingestion `Données de production Rev.xlsx`
- [ ] Validation Great Expectations
- [ ] Insertion dans `production.daily`, `maintenance.failures`, `maintenance.interventions`
- [ ] Publication événement `data.ingested.production` sur RabbitMQ
- [ ] Idempotence (rejouable sans doublons)

### 3.5 Boilerplate Flutter
- [ ] Projet Flutter 3.x initialisé
- [ ] Architecture Riverpod + Dio + go_router
- [ ] Écran de login + stockage `flutter_secure_storage` du refresh token
- [ ] Intercepteur Dio : injection `Authorization: Bearer ...` + refresh sur 401
- [ ] Builds Web / iOS / Android lancent et atteignent l'écran login

---

## 4. Phase 2 — Services métier (6 sem.)

### 4.1 production-service
- [ ] Schéma SQL : `wells`, `blocks`, `daily_production`
- [ ] `GET /production/daily?from=&to=&block=`
- [ ] `POST /production/daily` (engineer+)
- [ ] `GET /production/wells`, `GET /production/blocks`
- [ ] `GET /production/kpis?period=` (production totale, watercut moyen, WOR)
- [ ] `GET /production/export?format=csv|xlsx`
- [ ] Cache Redis pour KPIs (TTL 5 min)
- [ ] Tests + OpenAPI

### 4.2 maintenance-service
- [ ] Schéma SQL : `failures`, `interventions`, `equipment_status`
- [ ] `GET /maintenance/failures` + filtres
- [ ] `POST /maintenance/failures` (engineer+)
- [ ] `GET/POST /maintenance/interventions`
- [ ] Tests + OpenAPI

### 4.3 Tests d'intégration cross-services
- [ ] Suite e2e : login → création prod → KPIs
- [ ] CI bloque le merge si suite e2e échoue
- [ ] OpenAPI consolidé exposé sur `/docs` (Traefik)

---

## 5. Phase 3 — ML & Async (6 sem.)

### 5.1 ml-service — inference
- [ ] Réutilisation des modèles `streamlit/src/models/`
- [ ] Registre de modèles versionné (table `ml.models`)
- [ ] `POST /ml/predict/maintenance`
- [ ] `POST /ml/predict/forecast`
- [ ] `POST /ml/predict/water`
- [ ] Historisation prédictions (`ml.predictions`)
- [ ] `GET /ml/predictions/history`

### 5.2 ml-service — entraînement async
- [ ] Celery worker + RabbitMQ
- [ ] `POST /ml/train` → renvoie `job_id`
- [ ] `GET /ml/jobs/{job_id}` (statut, métriques)
- [ ] Publication `prediction.completed` / `model.trained`

### 5.3 notification-service
- [ ] Worker RabbitMQ (consume `alert.failure_predicted`, `prediction.completed`, `user.created`)
- [ ] Envoi email SMTP
- [ ] FCM push notifications mobile
- [ ] Templates (welcome, reset password, alerte panne)

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

| Date       | Auteur | Changement                                                                                                                  |
|------------|--------|-----------------------------------------------------------------------------------------------------------------------------|
| 2026-04-26 | Claude | Création initiale du TASKS.md depuis lecture exhaustive de `docs/`                                                          |
| 2026-04-26 | Claude | Streamlit verrouillé (§1.2). Production des 5 docs §2.2 : api-reference, migration-v2-to-v3, runbook, security, data-model |
