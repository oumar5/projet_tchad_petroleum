# 🗄️ Modèle de Données — SmartBarrel

> Diagramme ER et description détaillée des schémas PostgreSQL 16 utilisés par les microservices SmartBarrel.
>
> **Règle de découpage** : un schéma par service, un service n'écrit que dans son schéma.

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Schéma `auth`](#2-schéma-auth)
3. [Schéma `production`](#3-schéma-production)
4. [Schéma `maintenance`](#4-schéma-maintenance)
5. [Schéma `ml`](#5-schéma-ml)
6. [Schéma `etl`](#6-schéma-etl)
7. [Schéma `notifications`](#7-schéma-notifications)
8. [Index et performance](#8-index-et-performance)
9. [Migrations Alembic](#9-migrations-alembic)
10. [Conventions](#10-conventions)

---

## 1. Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                  PostgreSQL 16 — smartbarrel_db                 │
│                                                                  │
│  ┌──────────┐   ┌────────────┐   ┌────────────┐   ┌──────────┐  │
│  │  auth    │   │ production │   │maintenance │   │   ml     │  │
│  │          │   │            │   │            │   │          │  │
│  │ users    │   │ wells      │   │ failures   │   │ models   │  │
│  │ roles    │◀──│ blocks     │   │ interv.    │   │ jobs     │  │
│  │ perms    │   │ daily_prod │   │ equip_stat │   │ predict. │  │
│  │ audit    │   │            │   │            │   │          │  │
│  └──────────┘   └────────────┘   └────────────┘   └──────────┘  │
│                                                                  │
│  ┌──────────┐   ┌────────────────┐                              │
│  │   etl    │   │ notifications  │                              │
│  │          │   │                │                              │
│  │ runs     │   │ sent_messages  │                              │
│  │ snapshots│   │ preferences    │                              │
│  │ migr.runs│   │ templates      │                              │
│  └──────────┘   └────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### Diagramme ER simplifié

```
         ┌──────────────┐
         │  auth.users  │
         └──────┬───────┘
                │ N
                ▼
       ┌─────────────────┐         N ┌──────────────────┐
       │auth.user_roles  │───────────│ auth.role_perms  │
       └────────┬────────┘           └────────┬─────────┘
                │                             │
              N │                             │ N
                ▼                             ▼
         ┌──────────────┐              ┌──────────────┐
         │  auth.roles  │              │auth.permiss. │
         └──────────────┘              └──────────────┘


    ┌──────────────────┐          ┌──────────────────┐
    │production.blocks │◀─────────│production.wells  │
    └────────┬─────────┘   1   N  └─────────┬────────┘
             │                              │
             │ 1                            │ 1
             ▼ N                            ▼ N
    ┌────────────────────────────────────────────────┐
    │           production.daily_production          │
    └────────────────────────────────────────────────┘
                        ▲
                        │ FK logique (cross-schema, REST only)
                        │
    ┌────────────────────────────┐
    │ maintenance.failures       │
    │ maintenance.interventions  │
    │ maintenance.equipment      │
    └────────────────────────────┘


    ┌──────────────┐   1   N   ┌──────────────┐
    │  ml.models   │◀──────────│ml.predictions│
    └──────┬───────┘           └──────────────┘
           │
           │ 1   N
           ▼
    ┌──────────────┐
    │   ml.jobs    │
    └──────────────┘
```

---

## 2. Schéma `auth`

> Détail complet dans [`future-architecture.md`](future-architecture.md) §5.2.

### Tables

| Table | Rôle |
|-------|------|
| `users` | Utilisateurs de l'application |
| `roles` | Rôles RBAC (admin, engineer, analyst, viewer) |
| `permissions` | Permissions granulaires (`resource:action`) |
| `user_roles` | N-N user ↔ role |
| `role_permissions` | N-N role ↔ permission |
| `audit_log` | Journal immuable des actions sensibles |
| `password_resets` | Tokens de reset mot de passe (hashés) |
| `mfa_recovery_codes` | Codes de récupération MFA (hashés, single-use) |

### Tables additionnelles

```sql
CREATE TABLE auth.password_resets (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash   TEXT NOT NULL,
    expires_at   TIMESTAMPTZ NOT NULL,
    used_at      TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON auth.password_resets (token_hash);
CREATE INDEX ON auth.password_resets (user_id, expires_at);

CREATE TABLE auth.mfa_recovery_codes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    code_hash   TEXT NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX ON auth.mfa_recovery_codes (user_id, code_hash);
```

---

## 3. Schéma `production`

### Référentiel : blocs et puits

Le bloc est l'entité racine de la production. Un bloc regroupe plusieurs puits.
**Il n'y a pas de notion de "zone" supérieure** dans le modèle actuel — un bloc
correspond directement à une zone géographique de production.

CRUD complet exposé sous `/v1/production/blocks` et `/v1/production/wells`
(voir [api-reference.md](api-reference.md#32-référentiels)). Les codes
(`block.code`, `well.code`) sont **immuables** après création ; pour renommer
un bloc, mettre à jour `name` via `PATCH`.

Les contraintes d'intégrité empêchent la suppression d'un bloc/puits encore
référencé par une ligne de production (HTTP 409).

### Tables

```sql
CREATE SCHEMA production;

-- Hiérarchie : zones → blocs → puits
CREATE TABLE production.zones (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        TEXT UNIQUE NOT NULL,           -- 'TCHAD', 'NORD', 'SUD'…
    name        TEXT NOT NULL,
    description TEXT
);

CREATE TABLE production.blocks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        TEXT UNIQUE NOT NULL,           -- 'X', 'Y', 'Z'
    name        TEXT NOT NULL,
    description TEXT,
    zone_id     UUID NOT NULL REFERENCES production.zones(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_blocks_zone_id ON production.blocks(zone_id);

CREATE TABLE production.wells (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        TEXT UNIQUE NOT NULL,           -- ex: 'Y-04'
    block_id    UUID NOT NULL REFERENCES production.blocks(id),
    pump_type   TEXT,                           -- ESP, beam_pump, ...
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON production.wells (block_id);

CREATE TABLE production.daily_production (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date            DATE NOT NULL,
    block_id        UUID NOT NULL REFERENCES production.blocks(id),
    well_id         UUID REFERENCES production.wells(id),    -- null = agrégé bloc
    wells_total     INTEGER NOT NULL CHECK (wells_total >= 0),
    wells_active    INTEGER NOT NULL CHECK (wells_active >= 0),
    oil_bbl         NUMERIC(12,2) NOT NULL CHECK (oil_bbl >= 0),
    water_bbl       NUMERIC(12,2) NOT NULL CHECK (water_bbl >= 0),
    watercut_pct    NUMERIC(5,2) NOT NULL CHECK (watercut_pct BETWEEN 0 AND 100),
    wor             NUMERIC(8,3),                            -- water-oil ratio
    water_kbbl_day  NUMERIC(10,3),
    source          TEXT NOT NULL DEFAULT 'manual',          -- manual | excel_import | scada
    created_by      UUID REFERENCES auth.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (date, block_id, well_id)
);

CREATE INDEX ON production.daily_production (date DESC, block_id);
CREATE INDEX ON production.daily_production (block_id, date DESC);
CREATE INDEX ON production.daily_production (well_id, date DESC) WHERE well_id IS NOT NULL;
```

### Vues utilitaires

```sql
CREATE VIEW production.kpi_30d AS
SELECT
    block_id,
    SUM(oil_bbl) AS oil_total_30d,
    AVG(watercut_pct) AS watercut_avg_30d,
    AVG(wells_active) AS wells_active_avg_30d
FROM production.daily_production
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY block_id;
```

---

## 4. Schéma `maintenance`

```sql
CREATE SCHEMA maintenance;

CREATE TABLE maintenance.equipment (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code          TEXT UNIQUE NOT NULL,         -- ex: 'PUMP-Y-04'
    type          TEXT NOT NULL,                -- ESP, BEAM_PUMP, COMPRESSOR, ...
    well_code     TEXT,                         -- FK logique vers production.wells.code
    install_date  DATE,
    status        TEXT NOT NULL DEFAULT 'active', -- active | failed | retired
    metadata      JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE maintenance.failures (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_date   DATE NOT NULL,
    block               TEXT NOT NULL,
    equipment_id        UUID REFERENCES maintenance.equipment(id),
    failure_type        TEXT NOT NULL,
    severity            TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    description         TEXT,
    estimated_duration_h INTEGER,
    repair_cost         NUMERIC(12,2),
    parts_replaced      JSONB,
    reported_by         UUID REFERENCES auth.users(id),
    resolved_at         TIMESTAMPTZ,
    metadata            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON maintenance.failures (notification_date DESC);
CREATE INDEX ON maintenance.failures (block, notification_date DESC);
CREATE INDEX ON maintenance.failures (equipment_id, notification_date DESC) WHERE equipment_id IS NOT NULL;

CREATE TABLE maintenance.interventions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    failure_id      UUID REFERENCES maintenance.failures(id),
    intervention_date DATE NOT NULL,
    intervention_type TEXT NOT NULL,           -- corrective | preventive | inspection
    duration_h      NUMERIC(6,2),
    personnel       JSONB,                     -- liste des intervenants
    result          TEXT,
    cost            NUMERIC(12,2),
    notes           TEXT,
    performed_by    UUID REFERENCES auth.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON maintenance.interventions (intervention_date DESC);
CREATE INDEX ON maintenance.interventions (failure_id) WHERE failure_id IS NOT NULL;
```

---

## 5. Schéma `ml`

```sql
CREATE SCHEMA ml;

CREATE TABLE ml.models (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  TEXT NOT NULL,                -- 'maintenance_xgboost'
    version               TEXT NOT NULL,                -- 'v3.0.0'
    model_type            TEXT NOT NULL,                -- maintenance | forecast | water_injection
    algorithm             TEXT NOT NULL,                -- random_forest | xgboost | prophet | ...
    metrics               JSONB NOT NULL,               -- accuracy, rmse, r2, ...
    hyperparameters       JSONB NOT NULL,
    training_dataset_id   UUID,                         -- FK vers etl.snapshots
    blob_url              TEXT NOT NULL,                -- s3://smartbarrel-ml/models/...
    is_active             BOOLEAN NOT NULL DEFAULT false,
    trained_at            TIMESTAMPTZ NOT NULL,
    trained_by            UUID REFERENCES auth.users(id),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

CREATE INDEX ON ml.models (model_type, is_active);

-- Un seul modèle actif par type
CREATE UNIQUE INDEX one_active_per_type ON ml.models (model_type) WHERE is_active = true;

CREATE TABLE ml.jobs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type      TEXT NOT NULL,                  -- train | retrain | evaluate
    model_type    TEXT,
    algorithm     TEXT,
    status        TEXT NOT NULL DEFAULT 'queued', -- queued | running | success | failed
    params        JSONB,
    result        JSONB,
    error         TEXT,
    started_at    TIMESTAMPTZ,
    finished_at   TIMESTAMPTZ,
    requested_by  UUID REFERENCES auth.users(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON ml.jobs (status, created_at DESC);

CREATE TABLE ml.predictions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id        UUID NOT NULL REFERENCES ml.models(id),
    prediction_type TEXT NOT NULL,                  -- maintenance | forecast | water
    input_data      JSONB NOT NULL,
    output_data     JSONB NOT NULL,
    confidence      NUMERIC(5,4),
    requested_by    UUID REFERENCES auth.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON ml.predictions (model_id, created_at DESC);
CREATE INDEX ON ml.predictions (prediction_type, created_at DESC);
```

---

## 6. Schéma `etl`

```sql
CREATE SCHEMA etl;

CREATE TABLE etl.snapshots (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label        TEXT UNIQUE NOT NULL,           -- 'v2-snapshot-20260426'
    source_type  TEXT NOT NULL,                  -- excel | scada | iot | api
    source_uri   TEXT,
    row_counts   JSONB,                          -- { production: 3500, failures: 67 }
    file_hash    TEXT,                           -- SHA-256 du fichier source
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE etl.runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id     UUID REFERENCES etl.snapshots(id),
    status          TEXT NOT NULL,                -- running | success | failed
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    rows_processed  INTEGER,
    rows_skipped    INTEGER,
    rows_failed     INTEGER,
    error_message   TEXT,
    metadata        JSONB
);

CREATE INDEX ON etl.runs (status, started_at DESC);

CREATE TABLE etl.migration_runs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase         TEXT NOT NULL,                  -- data | models | users | shadow | switch
    status        TEXT NOT NULL,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    rows_processed INTEGER,
    error_message TEXT,
    metadata      JSONB
);
```

---

## 7. Schéma `notifications`

```sql
CREATE SCHEMA notifications;

CREATE TABLE notifications.templates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        TEXT UNIQUE NOT NULL,             -- 'welcome', 'reset_password', 'failure_alert'
    channel     TEXT NOT NULL,                    -- email | push | sms
    locale      TEXT NOT NULL DEFAULT 'fr',
    subject     TEXT,
    body        TEXT NOT NULL,
    variables   JSONB,                            -- liste des placeholders attendus
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (code, channel, locale)
);

CREATE TABLE notifications.preferences (
    user_id           UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email_enabled     BOOLEAN NOT NULL DEFAULT true,
    push_enabled      BOOLEAN NOT NULL DEFAULT true,
    failure_alerts    BOOLEAN NOT NULL DEFAULT true,
    weekly_report     BOOLEAN NOT NULL DEFAULT true,
    fcm_token         TEXT,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notifications.sent_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES auth.users(id),
    template_id  UUID REFERENCES notifications.templates(id),
    channel      TEXT NOT NULL,
    recipient    TEXT NOT NULL,                   -- email ou device_id
    subject      TEXT,
    body         TEXT,
    status       TEXT NOT NULL,                   -- queued | sent | failed | delivered
    error        TEXT,
    sent_at      TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON notifications.sent_messages (user_id, created_at DESC);
CREATE INDEX ON notifications.sent_messages (status, created_at DESC);
```

---

## 8. Index et performance

### 8.1 Stratégie

- **Index B-tree** par défaut sur les colonnes de tri / filtre fréquentes
- **Index partiels** quand colonnes nullable / état (`WHERE is_active = true`)
- **JSONB GIN** sur `metadata` si requêtes fréquentes (à ajouter au cas par cas)
- **Pas de sur-indexation** : limiter à 5 index max par table sauf justification

### 8.2 Partitionnement futur

Lorsque `production.daily_production` dépasse **10M lignes**, partitionner par range sur `date` (RANGE 1 mois).

### 8.3 Vacuum et autovacuum

Configuration recommandée :
```
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_scale_factor = 0.02
```

Pour les tables append-only volumineuses (`auth.audit_log`, `notifications.sent_messages`, `ml.predictions`).

---

## 9. Migrations Alembic

### 9.1 Structure

```
services/<service>/alembic/
├── alembic.ini
├── env.py
└── versions/
    ├── 0001_init.py
    ├── 0002_add_audit_log.py
    └── ...
```

### 9.2 Conventions

- Une migration = un objectif clair
- Toujours réversible (`upgrade()` + `downgrade()`)
- Nommage : `<NNNN>_<description_courte>.py`
- Pas de DDL destructive sans backup préalable
- Tests d'idempotence en CI

### 9.3 Pipeline CI

1. Lint Alembic (`alembic check`)
2. Application sur DB de test vide → success
3. Rollback `downgrade -1` → success
4. Re-application → success

---

## 10. Conventions

### 10.1 Nommage

- Tables / colonnes : `snake_case`
- Clés primaires : `id` (UUID v4 par défaut)
- Clés étrangères : `<table_singulier>_id` (ex: `block_id`, `user_id`)
- Timestamps : `created_at`, `updated_at` (TIMESTAMPTZ)
- Booléens : préfixe `is_`, `has_` (ex: `is_active`)

### 10.2 Types préférés

| Sémantique | Type SQL |
|------------|----------|
| Identifiant | `UUID DEFAULT gen_random_uuid()` |
| Texte court (< 256) | `TEXT` (pas de `VARCHAR(N)`) |
| Email | `CITEXT` (case-insensitive) |
| Booléen | `BOOLEAN NOT NULL` |
| Date sans heure | `DATE` |
| Date avec heure | `TIMESTAMPTZ` (toujours TZ-aware) |
| Décimal financier | `NUMERIC(12,2)` |
| JSON arbitraire | `JSONB` (jamais `JSON`) |
| IP | `INET` |

### 10.3 Contraintes

- `NOT NULL` par défaut, sauf justification
- `CHECK` pour les invariants métier (ex: `watercut_pct BETWEEN 0 AND 100`)
- `UNIQUE` pour les contraintes naturelles
- `ON DELETE CASCADE` réservé aux relations propriétaires (user → user_roles)

### 10.4 Cross-schema

> **Pas de FOREIGN KEY entre schémas** : un service n'écrit que dans son schéma. Les références cross-schema sont logiques uniquement (ex: `maintenance.failures.equipment.well_code` → `production.wells.code`), résolues via API REST.

Cela permet de splitter en bases physiques distinctes plus tard sans rework.

---

## 11. Diagramme complet (à générer)

Le diagramme ER complet est généré automatiquement à partir des migrations Alembic via `dbdiagram.io` ou `schemaspy` :

```bash
# Génération
make schema-diagram

# Sortie
docs/diagrams/data-model-erd.svg
```

Régénération **obligatoire** à chaque migration affectant la structure.

---

*Document vivant — mis à jour à chaque migration.*
