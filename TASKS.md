# 📋 TASKS — Tchad Petroleum / SmartBarrel

> Source unique de vérité pour le suivi de l'avancement.
> **Règle** : cocher chaque case `[ ]` → `[x]` à chaque mise à jour, et mettre à jour la date de la section concernée.
>
> Légende : `[ ]` à faire · `[x]` fait · `[~]` en cours · `[!]` bloqué

**Dernière mise à jour** : 2026-04-28
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
8. [Sprints ouverts (post-2026-04-28)](#10-sprints-ouverts-post-2026-04-28)
9. [Backlog transverse](#8-backlog-transverse)
10. [Risques à surveiller](#9-risques-à-surveiller)

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
- [!] **Couverture incomplète** : ingère seulement 1/9 onglets du fichier réel (audit 2026-04-28). Voir §10 ETL Excel sprint 1-3.

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

## 10. Sprints ouverts (post-2026-04-28)

> Travaux décidés après audit complet du 2026-04-28 (cycle persistence/maintenance/storage/etl).

### 10.1 Persistance frontend renforcée — ✅ livré 2026-04-28

- [x] `OfflineCache` v2 : schema versioning + TTL fresh/maxAge + helper générique `cached<T>()` ([`offline_cache.dart`](frontend/lib/core/offline/offline_cache.dart))
- [x] Cache étendue à 6 repositories (dashboard, production, zones, blocks, wells, maintenance failures, maintenance interventions, ml models)
- [x] Banner global hors-ligne agrégeant tous les statuts ([`cache_status.dart`](frontend/lib/core/offline/cache_status.dart) + intégré dans [`home_screen.dart`](frontend/lib/features/auth/presentation/home_screen.dart))
- [x] Persistance des sélections `selectedZoneProvider` / `selectedBlockProvider` via Hive ([`blocks_providers.dart`](frontend/lib/core/providers/blocks_providers.dart))

### 10.2 Workflow maintenance complet — ✅ livré 2026-04-28

- [x] Migration `0002_failure_workflow` : `failures.status` (enum), `assigned_to`, `well_code`, `last_updated_by` + table `attachments` ([`backend/services/maintenance_service/alembic/versions/0002_failure_workflow.py`](backend/services/maintenance_service/alembic/versions/0002_failure_workflow.py))
- [x] Endpoints PATCH failures + interventions, attachments multipart (10 MB, MIME whitelist), download streaming
- [x] Publication RabbitMQ `alert.failure_reported` (severity high/critical) + `failure.status_changed`
- [x] Frontend : FAB "Déclarer une panne" + dialog complet (zone/bloc cascadés, puits, type, sévérité, durée, description), menu contextuel (résoudre/rouvrir/photo/intervention), dialog intervention, FAB "Nouvelle intervention" ([`maintenance_screen.dart`](frontend/lib/features/maintenance/presentation/maintenance_screen.dart))
- [x] Frontend : repository étendu (`updateFailure`, `createIntervention`, `updateIntervention`, `uploadFailureAttachment`, `listFailureAttachments`)
- [x] StatusChip coloré (pending/in_progress/resolved/cancelled) sur chaque card

### 10.3 Stockage objet MinIO — ✅ livré 2026-04-28

- [x] Service `minio` + `minio-bootstrap` (mc) dans le compose, buckets `smartbarrel-attachments` + `smartbarrel-ml-models` créés au démarrage ([`smartbarrel.compose.yml`](backend/smartbarrel.compose.yml))
- [x] Abstraction `StorageBackend` avec `LocalDiskStorage` + `S3Storage` ([`shared/storage/backend.py`](backend/shared/storage/backend.py))
- [x] `boto3==1.35.49` ajouté à `shared/requirements.txt`
- [x] maintenance-service branché : `app.state.storage` via factory `build_storage()`, switch `STORAGE_BACKEND=local|s3` dans `.env`
- [x] Smoke test e2e validé : POST attachment 201 → `mc ls` confirme objet → GET download 200 bytes identiques
- [ ] ml-service : migrer `app/models` (joblib) du volume Docker vers MinIO bucket `smartbarrel-ml-models` *(prochain chantier)*
- [ ] backups Postgres : pointer vers MinIO local en dev (au lieu d'AWS S3) pour tester le flow `backup-postgres.sh`

### 10.4 ETL Excel — couverture multi-onglets — 🚧 à livrer

> Audit 2026-04-28 : le fichier `data/Données de production Rev.xlsx` contient **9 onglets** dont seul `Prod YOM BlocsFaillés X, Y et Z` est ingéré. Les 8 autres (Pression, Injection eau, Pannes, Interventions, Stimulation, CAPEX, Arrêts puits, Phase forage) sont silencieusement ignorés. Granularité minute/seconde non supportée par le schéma actuel.

#### Sprint 1 — Inspection auto (P0, 2-3 j)

- [ ] Endpoint `POST /v1/etl/inspect/excel` (analyse seule, ne touche pas la BDD) → retourne par onglet : `name`, `rows`, `detected_kind`, `header_row`, `columns`, `preview` (3 lignes), `target_table`, `warnings`, `ready` (bool)
- [ ] Détection par signature de colonnes (regex/set d'entêtes) pour chaque type connu (daily_production, well_pressure, water_injection, failures, interventions, stimulation, capex, downtime)
- [ ] Frontend : wizard upload Excel à 2 étapes — étape 1 = tableau des onglets détectés avec icônes ✅/⚠️/❌, étape 2 = checkboxes + confirmation ([`production_screen.dart`](frontend/lib/features/production/presentation/production_screen.dart) `_ExcelImportDialog` à étendre)
- [ ] Endpoint `POST /v1/etl/ingest/excel/selective` qui prend un body `{snapshot_id, sheets: [...]}` et ingère uniquement les onglets cochés (savepoint isolé par onglet)
- [ ] Stocker le fichier Excel uploadé dans MinIO bucket `smartbarrel-imports` pour permettre le replay

#### Sprint 2 — Tables manquantes + ingestors (P0, 3-4 j)

- [ ] Migration alembic `production.well_pressure` (well_code, measured_at TIMESTAMPTZ, pressure_psi, reservoir_segment, UNIQUE(well_code, measured_at))
- [ ] Migration alembic `production.water_injection` (date, injector_code, volume_kbj, reservoir_zones, UNIQUE(date, injector_code))
- [ ] Migration alembic `maintenance.stimulation_jobs` (well_code, operation, job_end TIMESTAMPTZ, fluid, segment, block, UNIQUE(well_code, job_end, operation))
- [ ] Migration alembic `maintenance.well_capex_jobs` (well_code, activity_type, operation, job_end TIMESTAMPTZ, description, segment, block, UNIQUE(well_code, job_end, operation))
- [ ] Migration alembic `maintenance.well_downtime` (well_code, start_date TIMESTAMPTZ, end_date, category, segment, block, UNIQUE(well_code, start_date))
- [ ] Refacto `excel_ingestor.py` : registry de `SheetIngestor` (1 par onglet), pattern `detect(headers) -> bool` + `ingest(df, session) -> SheetResult`
- [ ] Ingestor `failures` (Historiq Pannes pompes → maintenance.failures, mapping `Bloc Faillé → block`, `Well → well_code`)
- [ ] Ingestor `interventions` (Repartion pompes → maintenance.interventions, `Job End` → `intervention_date` timestamp)
- [ ] Ingestor `well_pressure` (parser format wide multi-puits, unpivot 4 puits côte à côte → time-series long format)
- [ ] Ingestor `water_injection` (Excel wide format avec 1 colonne par injecteur → unpivot)
- [ ] Ingestor `stimulation` (Stimulation → stimulation_jobs)
- [ ] Ingestor `capex` (Autres travaux sur puits → well_capex_jobs)
- [ ] Ingestor `downtime` (Puits à l'arret et causes → well_downtime)

#### Sprint 3 — Polish (P1, 1-2 j)

- [ ] Page "Imports" dans la sidebar Flutter : historique des `etl.runs`, drill-down par snapshot, statut par onglet, bouton "Réimporter onglets échoués"
- [ ] Téléchargement du fichier source depuis MinIO (replay/audit)
- [ ] Endpoint `GET /v1/etl/snapshots/{id}/sheets/{sheet}/preview` (debug)

### 10.5 Notifications maintenance — 🚧 à livrer

- [ ] notification-service : consumer `alert.failure_reported` → FCM aux rôles `engineer` + `admin` qui ont `failure_alerts=true`
- [ ] notification-service : consumer `failure.status_changed` → email au `assigned_to` si défini
- [ ] Frontend : écran "Mes alertes" dans la sidebar avec badge non-lus
- [ ] Push notification → tap → ouvre la card de la panne concernée

### 10.6 UX & complétude — 🚧 à livrer

- [ ] Onboarding première connexion (tour guidé, données vides → CTA import Excel)
- [ ] Saisie production **par puits** dans le dialog (en plus de bloc)
- [ ] Détection doublon avant POST (pré-vérification 409)
- [ ] Édition/suppression d'une saisie production existante
- [ ] Mémorisation cross-session de la zone/bloc déjà persistée par §10.1, mais propagation entre tabs Maintenance et Injection à confirmer

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
| 2026-04-28 | Claude | Hiérarchie Zone→Bloc (migration `0002_add_zones`, sélecteur cascadé `ZoneBlockPicker`, 4 endpoints zones). Sidebar consolidée 8→7 entrées (Modèles IA top-level, Configuration en 3 tabs). Excel import UI dans Production. CORS/422 fix sur ml-service (handler `ValueError` global) |
| 2026-04-28 | Claude | UX quick-wins : empty states pédagogiques avec CTA, `prettyError` partout (auth_controller fix), polling ML enrichi avec stepper visuel + barre progression + chrono temps réel + gestion d'échec |
| 2026-04-28 | Claude | Persistance frontend renforcée (§10.1) : OfflineCache v2 avec TTL/schema versioning, helper `cached<T>()`, cache étendue à 6 repositories, banner global hors-ligne, persistance des sélections zone/bloc dans Hive |
| 2026-04-28 | Claude | Workflow maintenance complet (§10.2) : migration `0002_failure_workflow` (status enum, assigned_to, well_code, attachments table), endpoints PATCH+attachments+download, events RabbitMQ `alert.failure_reported`/`failure.status_changed`, frontend FAB + dialogs + menu contextuel + StatusChip |
| 2026-04-28 | Claude | Stockage objet (§10.3) : MinIO + bootstrap mc dans le compose, abstraction `StorageBackend` (Local/S3) dans `shared/storage`, maintenance-service migré sur S3 (boto3), smoke test e2e validé. À suivre : ml-service models + backups Postgres |
| 2026-04-28 | Claude | Audit ETL Excel (§10.4) : couverture 1/9 onglets seulement. Sprint 1-3 planifiés (inspection auto, tables time-series manquantes, ingestors par onglet). 3.4 marqué `[!]` en attendant. Notifications maintenance + UX onboarding ouverts (§10.5/10.6) |
