# Architecture Future — Évolution v3

> Document de cadrage pour la prochaine génération de la plateforme : passage d'une application Streamlit monolithique vers une architecture **Flutter (frontend) + Python (backend API)** avec authentification dédiée.

---

## 1. Contexte et motivation

La version actuelle (v2) repose sur **Streamlit**, ce qui présente des limites pour une mise en production à grande échelle :

- Pas de séparation front/back claire → difficile à scaler indépendamment
- Pas d'application mobile native (les ingénieurs terrain ont besoin de mobilité)
- Authentification limitée et gestion de sessions rudimentaire
- Pas de support multi-utilisateurs concurrents performant
- Pas d'API exposable à des systèmes tiers (SCADA, ERP)

La v3 vise à transformer le projet en une **plateforme distribuée, mobile-first et sécurisée**, exploitable aussi bien sur desktop que sur le terrain.

---

## 2. Naming de l'application

### Candidats retenus

| Nom | Justification |
|------|--------------|
| **DobaIQ** | Référence au bassin de Doba (cœur de la production tchadienne) + dimension IA |
| **NjéraOil** | Intégration culturelle (langue locale) + identité produit |
| **PétroVision** | Vision prédictive, internationalisable |
| **TchadFlow** | Flux de production + ancrage national |
| **LogoneIQ** | Région du Logone + intelligence |

**Recommandation** : décision à valider avec les parties prenantes (direction, équipe produit, marketing). Critères : disponibilité du domaine `.com`/`.td`, dépôt de marque, prononçabilité internationale.

---

## 3. Architecture cible

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENTS                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │ Flutter Web  │  │ Flutter iOS  │  │Flutter Android│    │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└──────────┼─────────────────┼─────────────────┼─────────────┘
           │                 │                 │
           └─────────────────┴─────────────────┘
                             │
                       HTTPS / REST + WebSocket
                             │
┌────────────────────────────┴────────────────────────────────┐
│                      API GATEWAY (Nginx)                    │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Auth Service  │  │  Backend API    │  │  ML Service     │
│  (SuperTokens) │  │   (FastAPI)     │  │   (FastAPI)     │
└───────┬────────┘  └────────┬────────┘  └────────┬────────┘
        │                    │                    │
        │           ┌────────┴────────┐           │
        │           │                 │           │
   ┌────▼─────┐ ┌───▼──────┐  ┌──────▼──────┐ ┌──▼──────┐
   │ Postgres │ │ Postgres │  │   Redis     │ │ Models  │
   │  (auth)  │ │  (data)  │  │  (cache)    │ │ (.pkl)  │
   └──────────┘ └──────────┘  └─────────────┘ └─────────┘
```

### 3.1 Frontend — Flutter

**Pourquoi Flutter** :
- Une seule codebase pour Web, iOS, Android (et desktop si besoin)
- Performances natives, idéales pour les visualisations lourdes (graphiques, dashboards)
- Hot-reload, productivité élevée
- Adapté à un usage terrain (mode hors-ligne possible avec `sqflite` + sync)

**Structure proposée** :
```
mobile_app/
├── lib/
│   ├── core/                  # config, théme, constantes
│   ├── data/
│   │   ├── api/               # clients REST (Dio)
│   │   ├── models/            # DTOs
│   │   └── repositories/
│   ├── features/
│   │   ├── auth/              # login, signup, profile
│   │   ├── dashboard/         # KPIs
│   │   ├── maintenance/       # prédiction pannes
│   │   ├── forecast/          # prévision production
│   │   ├── water_injection/   # optimisation
│   │   └── reports/           # rapports & exports
│   ├── shared/                # widgets réutilisables
│   └── main.dart
└── test/
```

**Stack Flutter** :
- `dio` — client HTTP
- `riverpod` ou `bloc` — state management
- `fl_chart` / `syncfusion_flutter_charts` — visualisations
- `go_router` — navigation
- `flutter_secure_storage` — stockage tokens
- `hive` / `sqflite` — cache local + offline

### 3.2 Backend — Python (FastAPI)

**Pourquoi FastAPI plutôt que Django/Flask** :
- Async natif → essentiel pour endpoints ML lents
- Génération automatique d'OpenAPI/Swagger → consommable par Flutter
- Validation Pydantic alignée avec les DTOs Flutter
- Performance proche de Node.js / Go
- Réutilisation directe du code ML existant (`src/models/`)

**Découpage en services** :

| Service | Responsabilité | Stack |
|---------|---------------|-------|
| `auth-service` | Authentification, sessions, RBAC | SuperTokens core + FastAPI |
| `api-service` | CRUD données production/pannes, KPIs | FastAPI + SQLAlchemy + Postgres |
| `ml-service` | Inference modèles, training jobs | FastAPI + Celery + Redis |
| `etl-service` | Ingestion données (Excel, SCADA, IoT) | Python + Airflow ou Prefect |

**Structure backend** :
```
backend/
├── auth_service/
├── api_service/
│   ├── app/
│   │   ├── routers/      # endpoints REST
│   │   ├── schemas/      # Pydantic
│   │   ├── models/       # SQLAlchemy
│   │   ├── services/     # logique métier
│   │   └── main.py
│   └── tests/
├── ml_service/
│   ├── app/
│   │   ├── routers/
│   │   ├── inference/    # wrap src/models existants
│   │   ├── training/     # jobs entraînement
│   │   └── main.py
│   └── tests/
└── shared/               # libs communes (logging, config)
```

### 3.3 Authentification — SuperTokens

#### Pourquoi SuperTokens

| Critère | SuperTokens | Keycloak | Auth0 | Firebase Auth | JWT custom |
|---------|-------------|----------|-------|---------------|------------|
| Self-hosted | ✅ | ✅ | ❌ | ❌ | ✅ |
| Souveraineté Tchad | ✅ | ✅ | ❌ | ❌ | ✅ |
| Coût | Gratuit | Gratuit | $$$ | Freemium | Gratuit |
| SDK Flutter officiel | ⚠️ communautaire | ⚠️ via OIDC | ✅ | ✅ | n/a |
| SDK FastAPI officiel | ✅ | ⚠️ | ✅ | ❌ | n/a |
| Empreinte ressources | Légère | Lourde (JVM) | n/a | n/a | Légère |
| Maturité | Moyenne | Élevée | Élevée | Élevée | n/a |
| MFA / Passwordless | ✅ | ✅ | ✅ | ✅ | À coder |

**Décision proposée** : **SuperTokens self-hosté**, avec :
- SDK FastAPI officiel côté backend
- Côté Flutter : intégration **REST custom** (les endpoints SuperTokens sont documentés et standards), avec stockage sécurisé des tokens via `flutter_secure_storage`
- Fallback : Keycloak si l'équipe préfère un standard OIDC complet pour intégrations tierces (SCADA, ERP)

#### Fonctionnalités auth attendues

- Email + mot de passe
- Réinitialisation par email
- MFA (TOTP) pour rôles sensibles (managers, ingénieurs réservoir)
- Sessions JWT à courte durée + refresh tokens
- RBAC : `admin`, `engineer`, `analyst`, `viewer`
- Audit log des connexions

#### Modèle RBAC

| Rôle | Permissions |
|------|------------|
| `admin` | Tout (gestion users, config, ingestion, export) |
| `engineer` | Lecture + entraînement modèles + recommandations |
| `analyst` | Lecture + visualisations + export rapports |
| `viewer` | Lecture seule dashboard |

### 3.4 Base de données

Migration de l'Excel (`data/Données de production Rev.xlsx`) vers **PostgreSQL** :

```sql
-- Schéma simplifié
CREATE SCHEMA production;
CREATE SCHEMA maintenance;
CREATE SCHEMA auth;        -- géré par SuperTokens

-- Tables principales
production.daily_records     -- production journalière
production.wells             -- référentiel puits
production.blocks            -- référentiel blocs
maintenance.failures         -- historique pannes
maintenance.interventions    -- interventions correctives
ml.models                    -- registre des modèles entraînés
ml.predictions               -- prédictions historisées
audit.logs                   -- traçabilité
```

ETL : pipeline d'ingestion qui lit l'Excel existant et migre les données initiales, puis ingère en continu via des connecteurs SCADA / IoT.

### 3.5 Communication client ↔ serveur

- **REST** pour CRUD et inference synchrone
- **WebSocket** pour streaming temps réel (alertes pannes, KPIs live)
- **Server-Sent Events** pour suivi de jobs ML (entraînement long)
- Format : JSON, schémas validés par OpenAPI 3.1

---

## 4. Plan de migration

### Phase 1 — Fondations (4-6 semaines)
- [ ] Décision finale du nom + dépôt de marque + domaines
- [ ] Setup monorepo (`/backend`, `/mobile_app`, `/infra`)
- [ ] Migration des données Excel → PostgreSQL (script ETL)
- [ ] Stand up SuperTokens core en Docker
- [ ] Boilerplate FastAPI `api-service` avec auth intégrée
- [ ] Boilerplate Flutter avec login + navigation

### Phase 2 — API & ML service (6-8 semaines)
- [ ] Exposer les modèles existants (`src/models/`) via `ml-service` REST
- [ ] Endpoints CRUD production / pannes
- [ ] Tests d'intégration
- [ ] Documentation OpenAPI

### Phase 3 — Frontend Flutter (8-10 semaines)
- [ ] Écrans : login, dashboard, prévision, maintenance, optimisation eau
- [ ] Composants graphiques (port des visualisations Streamlit)
- [ ] Mode offline (cache local + sync)
- [ ] Build iOS / Android / Web

### Phase 4 — Industrialisation (4 semaines)
- [ ] CI/CD (GitHub Actions ou GitLab CI)
- [ ] Déploiement Kubernetes ou Docker Swarm
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Logs centralisés (Loki ou ELK)
- [ ] Backup automatisé Postgres

### Phase 5 — Migration utilisateurs (2 semaines)
- [ ] Formation des utilisateurs
- [ ] Mode dual-run (Streamlit + nouvelle plateforme)
- [ ] Décommissionnement Streamlit

---

## 5. Stack technique récapitulative

| Couche | Technologie |
|--------|------------|
| Frontend | Flutter 3.x (Dart) |
| State management | Riverpod |
| Charts | fl_chart / syncfusion |
| Backend API | FastAPI (Python 3.11+) |
| ML | scikit-learn, XGBoost, Prophet (réutilisé v2) |
| Async tasks | Celery + Redis |
| Auth | SuperTokens self-hosted |
| Base de données | PostgreSQL 16 |
| Cache | Redis 7 |
| Reverse proxy | Nginx |
| Containerisation | Docker + docker-compose (puis K8s) |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |
| Logs | Loki + Grafana |

---

## 6. Risques et points d'attention

| Risque | Mitigation |
|--------|-----------|
| SDK Flutter SuperTokens non officiel | Implémentation REST manuelle ; envisager Keycloak en plan B |
| Complexité opérationnelle accrue (microservices) | Démarrer en monolithe modulaire, splitter quand nécessaire |
| Migration des données existantes | Script ETL idempotent + validation croisée Excel ↔ PG |
| Connectivité terrain (Tchad) | Mode offline Flutter + sync différée |
| Souveraineté des données | Tout self-hosté, pas de cloud étranger |
| Compétences équipe Flutter | Formation ou recrutement Dart/Flutter |
| Coûts infrastructure | Démarrer sur un seul VPS, scaler progressivement |

---

## 7. Décisions à valider

Ce document propose une direction. Les décisions suivantes doivent être tranchées par l'équipe avant le démarrage :

1. **Nom définitif** de l'application
2. **SuperTokens vs Keycloak** (selon expertise équipe et besoins OIDC)
3. **Monorepo vs polyrepo**
4. **Cloud hôte** : on-premise Tchad / VPS Europe / hybride
5. **Niveau de support offline** attendu sur mobile
6. **Périmètre v3.0** : faut-il livrer toutes les features v2 d'un coup, ou itérer ?

---

*Document vivant — à mettre à jour au fil des décisions et du démarrage de chaque phase.*
