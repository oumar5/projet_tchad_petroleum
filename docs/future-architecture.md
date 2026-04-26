# SmartBarrel — Architecture v3

> Document de cadrage de la nouvelle plateforme **SmartBarrel** : passage d'une application Streamlit monolithique vers une architecture **microservices** (Flutter front + FastAPI back + PostgreSQL + JWT/RBAC).

---

## 1. Décisions arrêtées

| Domaine | Choix |
|---------|-------|
| **Nom produit** | **SmartBarrel** |
| **Frontend** | Flutter (Web + iOS + Android) |
| **Backend** | FastAPI (Python 3.11+) — **architecture microservices** |
| **Authentification** | **JWT custom** (PyJWT + passlib/bcrypt) |
| **Autorisation** | **RBAC** (rôles + permissions granulaires) |
| **Base de données** | **PostgreSQL 16** (un schéma par service) |
| **Cache / Sessions / Tokens révoqués** | Redis 7 |
| **Message broker (async inter-services)** | RabbitMQ |
| **API Gateway** | Traefik |
| **Containerisation** | Docker + docker-compose → Kubernetes (cible) |

---

## 2. Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENTS                                 │
│   Flutter Web   │   Flutter iOS   │   Flutter Android            │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS
                ┌────────────▼────────────┐
                │   API Gateway (Traefik) │
                │   - TLS termination     │
                │   - JWT validation      │
                │   - Rate limiting       │
                │   - Routing             │
                └────────────┬────────────┘
                             │
        ┌────────┬───────────┼───────────┬──────────┬───────────┐
        │        │           │           │          │           │
   ┌────▼───┐ ┌──▼─────┐ ┌───▼────┐ ┌────▼────┐ ┌───▼───┐ ┌─────▼─────┐
   │ auth-  │ │product-│ │mainten-│ │   ml-   │ │  etl- │ │notification│
   │service │ │ service│ │ service│ │ service │ │service│ │  service   │
   └────┬───┘ └──┬─────┘ └───┬────┘ └────┬────┘ └───┬───┘ └─────┬─────┘
        │        │           │           │          │           │
        │        │           │           │          │           │
   ┌────▼────────▼───────────▼───────────▼──────────▼───────────▼────┐
   │                  PostgreSQL 16 (schémas isolés)                 │
   │  auth │ production │ maintenance │ ml │ etl │ notifications     │
   └─────────────────────────────────────────────────────────────────┘

   ┌──────────────┐     ┌─────────────┐
   │    Redis     │     │  RabbitMQ   │
   │ (cache,      │     │  (events,   │
   │  blocklist,  │     │   jobs)     │
   │  rate limit) │     │             │
   └──────────────┘     └─────────────┘
```

---

## 3. Découpage en microservices

### 3.1 auth-service

**Responsabilités** :
- Inscription, login, logout
- Émission JWT (access + refresh)
- Gestion users / rôles / permissions (RBAC)
- Reset password, MFA TOTP
- Audit log connexions

**Endpoints clés** :
```
POST   /auth/register
POST   /auth/login              → { access_token, refresh_token }
POST   /auth/refresh            → nouveau access_token
POST   /auth/logout             → blacklist du refresh
POST   /auth/password/reset
GET    /auth/me                 → profil + rôles + permissions
POST   /auth/users              [admin]
GET    /auth/users              [admin]
PATCH  /auth/users/{id}/roles   [admin]
GET    /auth/roles              [admin]
POST   /auth/roles              [admin]
GET    /auth/permissions        [admin]
```

**Stack** : FastAPI + SQLAlchemy + PyJWT + passlib[bcrypt] + Redis (blocklist).

### 3.2 production-service

**Responsabilités** :
- CRUD données production journalière
- Référentiels puits / blocs
- Calcul KPIs (production totale, watercut, WOR)
- Export CSV / Excel

**Endpoints clés** :
```
GET    /production/daily?from=&to=&block=
POST   /production/daily        [engineer+]
GET    /production/wells
GET    /production/blocks
GET    /production/kpis?period=
GET    /production/export?format=csv
```

### 3.3 maintenance-service

**Responsabilités** :
- Historique pannes par bloc
- Interventions correctives
- Statut équipements

**Endpoints clés** :
```
GET    /maintenance/failures?from=&to=&block=
POST   /maintenance/failures    [engineer+]
GET    /maintenance/interventions
POST   /maintenance/interventions [engineer+]
```

### 3.4 ml-service

**Responsabilités** :
- Inference des modèles (réutilise `src/models/` v2)
- Lancement de jobs d'entraînement (asynchrone via RabbitMQ)
- Registre des modèles (versionning)
- Historisation des prédictions

**Endpoints clés** :
```
POST   /ml/predict/maintenance   → probabilité panne
POST   /ml/predict/forecast      → prévision production N jours
POST   /ml/predict/water         → recommandation injection
POST   /ml/train                 [engineer+] → job_id
GET    /ml/jobs/{job_id}
GET    /ml/models                → registre
GET    /ml/predictions/history
```

### 3.5 etl-service

**Responsabilités** :
- Ingestion Excel (`Données de production Rev.xlsx`)
- Connecteurs SCADA / IoT (futur)
- Validation et nettoyage
- Publication d'événements `data.ingested` sur RabbitMQ

### 3.6 notification-service

**Responsabilités** :
- Emails (reset password, alertes pannes)
- Push notifications mobile (FCM)
- Consomme les événements RabbitMQ (`alert.failure`, `prediction.completed`)

---

## 4. Authentification JWT

### 4.1 Schéma de tokens

| Token | Durée | Stockage client | Révocable |
|-------|-------|-----------------|-----------|
| `access_token` | 15 min | mémoire Flutter | non (TTL court) |
| `refresh_token` | 7 jours | `flutter_secure_storage` | oui (Redis blocklist) |

**Algorithme** : `RS256` (clé asymétrique) — la clé publique est distribuée aux microservices pour validation locale, seule l'auth-service possède la clé privée.

### 4.2 Claims JWT

```json
{
  "sub": "user-uuid",
  "email": "user@smartbarrel.td",
  "roles": ["engineer"],
  "permissions": [
    "production:read",
    "production:write",
    "maintenance:read",
    "ml:predict",
    "ml:train"
  ],
  "iat": 1735200000,
  "exp": 1735200900,
  "jti": "token-uuid",
  "type": "access"
}
```

### 4.3 Flux d'authentification

```
1. Login
   Flutter → POST /auth/login (email, password)
   auth-service vérifie bcrypt
   → renvoie { access_token, refresh_token }
   Flutter stocke refresh dans secure_storage, access en mémoire

2. Appel API
   Flutter → GET /production/kpis
            Header: Authorization: Bearer <access_token>
   Traefik valide JWT (signature + exp) via clé publique
   Forward vers production-service avec headers enrichis :
     X-User-Id: <uuid>
     X-User-Roles: engineer
     X-User-Permissions: production:read,production:write,...

3. Refresh
   Access expire → Flutter intercepte 401
   POST /auth/refresh (refresh_token)
   auth-service vérifie blocklist Redis + valide
   → nouveau access_token

4. Logout
   POST /auth/logout
   refresh_token ajouté à blocklist Redis (TTL = exp restante)
```

### 4.4 Validation par les services

Chaque microservice utilise un middleware FastAPI commun (`shared/auth.py`) qui :
1. Extrait le JWT du header `Authorization`
2. Valide la signature avec la clé publique (cachée)
3. Vérifie `exp` et `type == "access"`
4. Injecte un `current_user: User` dans la dépendance FastAPI

```python
@router.get("/kpis")
def get_kpis(
    user: User = Depends(get_current_user),
    _: None = Depends(require_permission("production:read")),
):
    ...
```

---

## 5. RBAC — Modèle et schéma

### 5.1 Modèle conceptuel

```
User ──N─┐         ┌─N── Permission
         │         │
       UserRole──Role──RolePermission
```

Un utilisateur a **plusieurs rôles**, chaque rôle a **plusieurs permissions**. Les permissions effectives = union des permissions de tous les rôles.

### 5.2 Schéma SQL (`auth.*`)

```sql
CREATE SCHEMA auth;

CREATE TABLE auth.users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         CITEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT true,
    mfa_secret    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auth.roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT UNIQUE NOT NULL,           -- admin, engineer, analyst, viewer
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auth.permissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource    TEXT NOT NULL,                  -- production, maintenance, ml, users
    action      TEXT NOT NULL,                  -- read, write, delete, train, export
    description TEXT,
    UNIQUE (resource, action)
);

CREATE TABLE auth.user_roles (
    user_id    UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id    UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    granted_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE auth.role_permissions (
    role_id       UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES auth.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE auth.audit_log (
    id         BIGSERIAL PRIMARY KEY,
    user_id    UUID REFERENCES auth.users(id),
    event      TEXT NOT NULL,                   -- login, logout, role_granted, ...
    metadata   JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON auth.audit_log (user_id, created_at DESC);
```

### 5.3 Rôles et permissions par défaut (seed)

| Rôle | Permissions |
|------|-------------|
| **admin** | `*:*` (toutes) |
| **engineer** | `production:read,write` · `maintenance:read,write` · `ml:read,predict,train` · `reports:read,export` |
| **analyst** | `production:read` · `maintenance:read` · `ml:read,predict` · `reports:read,export` |
| **viewer** | `production:read` · `maintenance:read` · `reports:read` |

### 5.4 Permissions définies (catalogue initial)

```
production:read          production:write         production:delete       production:export
maintenance:read         maintenance:write        maintenance:delete
ml:read                  ml:predict               ml:train                ml:delete
reports:read             reports:export
users:read               users:write              users:delete
roles:read               roles:write
audit:read
```

### 5.5 Vérification de permission

```python
# shared/auth.py
def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)):
        if "*:*" in user.permissions or permission in user.permissions:
            return
        raise HTTPException(403, f"Missing permission: {permission}")
    return checker
```

Wildcard supporté : `production:*` autorise toutes les actions sur `production`.

---

## 6. Base de données — découpage

PostgreSQL 16 unique, **un schéma par service** (database-per-service light) :

```
smartbarrel_db
├── auth.*              → auth-service
├── production.*        → production-service
├── maintenance.*       → maintenance-service
├── ml.*                → ml-service
├── etl.*               → etl-service
└── notifications.*     → notification-service
```

**Règle** : un service n'écrit que dans son schéma. Les lectures cross-schema se font **uniquement via API REST** entre services, jamais en SQL direct. Cela permet de splitter en bases physiques distinctes plus tard sans rework.

---

## 7. Communication inter-services

| Type | Mécanisme | Cas d'usage |
|------|-----------|-------------|
| Sync request/response | REST (HTTP/JSON) | ml-service → production-service pour récupérer features |
| Async events | RabbitMQ | etl-service publie `data.ingested` → ml-service ré-entraîne |
| Async jobs longs | RabbitMQ + worker Celery | training de modèles |
| Streaming temps réel | WebSocket via gateway | dashboard live KPIs, alertes pannes |

**Exemples d'événements** :
```
data.ingested.production       → triggers KPI recompute
data.ingested.failures         → triggers ml retrain (si seuil)
prediction.completed           → notification-service push alerte
alert.failure_predicted        → notification-service email + FCM
user.created                   → notification-service email bienvenue
```

---

## 8. Structure du repository

```
smartbarrel/
├── mobile_app/                  # Flutter
│   ├── lib/
│   │   ├── core/
│   │   ├── data/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── production/
│   │   │   ├── maintenance/
│   │   │   ├── forecast/
│   │   │   └── water_injection/
│   │   └── shared/
│   └── test/
│
├── services/
│   ├── auth_service/
│   ├── production_service/
│   ├── maintenance_service/
│   ├── ml_service/
│   ├── etl_service/
│   └── notification_service/
│
├── shared/                      # libs Python communes
│   ├── auth/                    # middleware JWT, RBAC
│   ├── db/                      # base SQLAlchemy
│   ├── messaging/               # RabbitMQ wrappers
│   ├── logging/
│   └── config/
│
├── infra/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   ├── traefik/
│   ├── postgres/
│   └── k8s/                     # manifests futurs
│
├── docs/
└── README.md
```

---

## 9. Stack technique récapitulative

| Couche | Technologie |
|--------|-------------|
| Frontend | Flutter 3.x (Riverpod, Dio, fl_chart, go_router) |
| Backend | FastAPI 0.115+ (Python 3.11+) |
| ORM | SQLAlchemy 2.x + Alembic (migrations) |
| Auth | PyJWT (RS256) + passlib[bcrypt] + pyotp (MFA) |
| ML | scikit-learn, XGBoost, Prophet (réutilisés v2) |
| Tâches async | Celery + RabbitMQ |
| DB | PostgreSQL 16 |
| Cache / Blocklist | Redis 7 |
| Gateway | Traefik 3 |
| Containers | Docker → Kubernetes |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |
| Logs | Loki + Grafana |
| Tracing | OpenTelemetry + Tempo |

---

## 10. Plan de migration

Le projet se déroule en **deux grandes phases stratégiques** :

> **Phase 1 — Application logicielle** (saisie de données manuelle ou import Excel/CSV)
> **Phase 2 — IoT & systèmes embarqués** (capteurs terrain → ingestion automatique)

L'architecture v3 est conçue dès le départ pour absorber les flux IoT de la Phase 2 sans refactor : l'`etl-service` et le bus RabbitMQ servent de point d'entrée unique pour toutes les sources de données, qu'elles soient humaines ou machines.

---

### **PHASE 1 — Application SmartBarrel** (~28 sem.)

#### Jalon 1.1 — Fondations (4 sem.)
- [ ] Setup monorepo + `shared/` libs
- [ ] PostgreSQL + schémas + Alembic
- [ ] Traefik + docker-compose
- [ ] `auth-service` v1 (login, JWT, RBAC core)
- [ ] Migration Excel → PostgreSQL via `etl-service` v1
- [ ] Boilerplate Flutter avec login

#### Jalon 1.2 — Services métier (6 sem.)
- [ ] `production-service` (CRUD + KPIs)
- [ ] `maintenance-service` (CRUD)
- [ ] Tests d'intégration cross-services
- [ ] OpenAPI consolidé

#### Jalon 1.3 — ML & async (6 sem.)
- [ ] `ml-service` (inference des modèles v2)
- [ ] RabbitMQ + Celery workers
- [ ] `notification-service` (email + FCM)
- [ ] Pipeline d'entraînement async

#### Jalon 1.4 — Frontend Flutter (8 sem.)
- [ ] Écrans : login, dashboard, production, maintenance, forecast, water
- [ ] Mode offline (Hive + sync)
- [ ] Builds iOS / Android / Web

#### Jalon 1.5 — Industrialisation (4 sem.)
- [ ] CI/CD GitHub Actions
- [ ] Migration K8s
- [ ] Monitoring + logs centralisés
- [ ] Backups Postgres
- [ ] Décommissionnement Streamlit

---

### **PHASE 2 — IoT & systèmes embarqués** (~32 sem.)

Objectif : **automatiser la collecte de données terrain** via capteurs sur les puits, pompes et lignes de production. Élimine la saisie manuelle, fiabilise les données, débloque le temps réel.

> **Détails complets** : voir `docs/iot-roadmap.md`

#### Jalon 2.1 — POC sur 1 puits (8 sem.)
- [ ] Sélection capteurs (pression, température, débit, vibration)
- [ ] Edge gateway (Raspberry Pi industriel ou PLC)
- [ ] Connectivité (LoRaWAN ou cellulaire)
- [ ] Broker MQTT + ingestion vers `etl-service`

#### Jalon 2.2 — Pilote 1 bloc (12 sem.)
- [ ] Déploiement sur tous les puits d'un bloc
- [ ] Alimentation solaire + boîtiers IP68
- [ ] Intégration SCADA existante (OPC UA / Modbus)
- [ ] Pré-traitement edge (filtrage, agrégation)

#### Jalon 2.3 — Généralisation (12 sem.)
- [ ] Roll-out multi-blocs
- [ ] Re-entraînement des modèles ML sur données haute fréquence
- [ ] Alertes temps réel (WebSocket vers Flutter)
- [ ] Dashboard SCADA-like pour opérateurs

---

**Total estimé** : ~60 semaines (Phase 1 + Phase 2).

---

## 11. Risques et mitigations

| Risque | Mitigation |
|--------|------------|
| Complexité opérationnelle des microservices | Démarrer 2-3 services, splitter au besoin ; outillage observabilité dès J1 |
| Cohérence transactionnelle cross-services | Saga pattern ; éviter les transactions distribuées |
| Sécurité JWT (clé volée) | Rotation des clés RS256 ; clé privée dans secret manager ; access tokens courts (15min) |
| Performance gateway | Traefik horizontal scale ; cache validations JWT |
| Gestion des migrations DB multi-services | Alembic par service, pipelines CI séparés |
| Connectivité terrain (Tchad) | Mode offline Flutter robuste + sync différée |
| Souveraineté données | Hébergement on-premise ou VPS Tchad/Afrique |
| Saut technologique vers l'IoT (Phase 2) | Architecture pensée dès J1 pour l'ingestion machine ; `etl-service` et bus RabbitMQ absorbent les flux capteurs sans refactor |

---

## 12. Conventions

- **Nom de domaine pressenti** : `smartbarrel.td` (à réserver) + `*.smartbarrel.td` pour les services internes
- **Versioning API** : préfixe `/v1/` (ex. `/v1/production/daily`)
- **Codes erreur** : norme RFC 7807 (Problem Details for HTTP APIs)
- **Logs** : JSON structuré avec `trace_id` propagé entre services
- **Secrets** : Vault ou Kubernetes secrets ; jamais dans le code

---

*Document vivant — mis à jour à chaque jalon de la roadmap.*
