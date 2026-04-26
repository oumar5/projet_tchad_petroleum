# 🔄 Guide de Migration v2 (Streamlit) → v3 (SmartBarrel)

> Procédure de bascule des données, des modèles et des utilisateurs depuis l'application Streamlit monolithique vers la plateforme SmartBarrel microservices.
>
> **Statut v2** : verrouillée (lecture seule). Aucune nouvelle feature.
> **Cible v3** : architecture définie dans [`future-architecture.md`](future-architecture.md).

---

## 1. Vue d'ensemble

```
┌────────────────────┐                      ┌──────────────────────┐
│  Streamlit v2      │      Migration       │   SmartBarrel v3     │
│  (figée)           │ ───────────────────▶ │   (microservices)    │
│                    │                      │                      │
│  • Excel source    │                      │  • PostgreSQL 16     │
│  • Modèles pickle  │                      │  • Modèles versionn. │
│  • Sessions locale │                      │  • Auth JWT + RBAC   │
└────────────────────┘                      └──────────────────────┘
```

### Principes

- **Bascule progressive** : v2 et v3 tournent en parallèle pendant la phase de validation
- **Rollback garanti** : la v2 reste accessible pendant 90 jours après la mise en prod v3
- **Idempotence** : tous les scripts de migration peuvent être rejoués sans dégât
- **Audit** : chaque étape de migration est tracée dans `etl.migration_runs`

---

## 2. Phases de migration

| # | Phase | Durée | Bloquant pour bascule ? |
|---|-------|-------|--------------------------|
| 1 | Migration des données historiques | 3 j | Oui |
| 2 | Migration des modèles ML | 5 j | Oui |
| 3 | Création des comptes utilisateurs | 2 j | Oui |
| 4 | Validation parallèle (shadow mode) | 30 j | Oui |
| 5 | Bascule production | 1 j | — |
| 6 | Décommissionnement v2 | 90 j après bascule | Non |

---

## 3. Phase 1 — Données historiques

### 3.1 Source

Fichier `data/Données de production Rev.xlsx` (~1,2 Mo, 10+ ans d'historique).

Feuilles :
- `Prod YOM BlocsFaillés X, Y et Z` → `production.daily`
- `Historiq Pannes pompes` → `maintenance.failures`
- `Interventions` (si présente) → `maintenance.interventions`

### 3.2 Procédure

1. **Backup** : copie du fichier Excel dans `backups/migration/v2-snapshot-YYYYMMDD.xlsx`
2. **Lancement de l'ingestion** :

   ```bash
   cd services/etl_service
   python -m etl.cli ingest-excel \
     --file backups/migration/v2-snapshot-YYYYMMDD.xlsx \
     --target production,maintenance \
     --dry-run
   ```

3. **Vérification du dry-run** : compter les lignes attendues vs détectées
4. **Exécution réelle** :

   ```bash
   python -m etl.cli ingest-excel --file ... --target production,maintenance --commit
   ```

5. **Validation Great Expectations** :

   ```bash
   great_expectations checkpoint run production_v2_to_v3
   ```

### 3.3 Mapping des colonnes

| Excel (v2) | PostgreSQL (v3) |
|------------|------------------|
| `Date` | `production.daily.date` |
| `Nombre total des puits` | `production.daily.wells_total` |
| `Nombre des puits actifs` | `production.daily.wells_active` |
| `Production journaliere d'huile bbl` | `production.daily.oil_bbl` |
| `Production journaliere d'eau bbl` | `production.daily.water_bbl` |
| `Teneur en eau (Watercut)` | `production.daily.watercut_pct` |
| `Water Oil Ratio` | `production.daily.wor` (calculé si null) |
| `Date de notification d'endomagement de la pompe` | `maintenance.failures.notification_date` |
| `Bloc Faillé` | `maintenance.failures.block` |

### 3.4 Critères d'acceptation

- [ ] Total lignes `production.daily` = total lignes Excel non vides
- [ ] Aucune date dupliquée
- [ ] `watercut_pct` ∈ [0, 100]
- [ ] `wor = water_bbl / oil_bbl` recalculé si manquant
- [ ] Audit : `etl.migration_runs.status = 'success'`

---

## 4. Phase 2 — Modèles ML

### 4.1 Inventaire à migrer

Modèles entraînés dans `streamlit/src/models/` :

| Type | Algorithme | Format actuel | Cible |
|------|------------|---------------|-------|
| Maintenance | Random Forest | Mémoire (re-train à chaque session) | `ml.models` + S3/MinIO blob |
| Maintenance | Gradient Boosting | id. | id. |
| Maintenance | XGBoost | id. | id. |
| Forecast | Random Forest | id. | id. |
| Forecast | Prophet | id. | id. |
| Forecast | NeuralProphet | id. | id. |
| Forecast | XGBoost | id. | id. |
| Water Injection | Random Forest | id. | id. |
| Water Injection | Gradient Boosting | id. | id. |

### 4.2 Procédure

1. **Entraînement de référence** sur le snapshot des données v2 :

   ```bash
   cd services/ml_service
   python -m ml.cli train-baseline \
     --dataset-snapshot v2-snapshot-YYYYMMDD \
     --register-as v3-baseline
   ```

2. **Sérialisation** : chaque modèle est sauvé en pickle versionné + métadonnées :

   ```
   ml.models
   ├── id (uuid)
   ├── name (ex: "maintenance_xgboost")
   ├── version (ex: "v3.0.0-baseline")
   ├── algorithm
   ├── trained_at
   ├── training_dataset_id (FK vers etl.snapshots)
   ├── metrics (jsonb : accuracy, rmse, r2, ...)
   ├── blob_url (s3://smartbarrel-ml/models/...)
   └── is_active (bool)
   ```

3. **Comparaison v2 vs v3** : exécuter le même test set sur les deux et comparer les métriques. Tolérance : ±2 % sur la métrique principale.

### 4.3 Critères d'acceptation

- [ ] Tous les modèles ré-entraînés et enregistrés dans `ml.models`
- [ ] Métriques v3 ≥ métriques v2 - 2 %
- [ ] `is_active = true` pour le modèle de référence par type
- [ ] Test d'inference unitaire passe pour chaque modèle

---

## 5. Phase 3 — Utilisateurs

### 5.1 Source

La v2 n'a **pas d'authentification** : les comptes sont créés ex nihilo dans la v3.

### 5.2 Procédure

1. **Liste fournie par TPC** : tableau `users-import.csv` avec `email,full_name,role`
2. **Import en bulk** :

   ```bash
   cd services/auth_service
   python -m auth.cli import-users \
     --file users-import.csv \
     --send-welcome-email
   ```

3. **Génération de mots de passe temporaires** : 16 caractères aléatoires, expiration 7 jours
4. **Email d'accueil** envoyé via `notification-service` (template `welcome.html`)

### 5.3 Mapping des rôles

| Profil métier | Rôle v3 |
|---------------|---------|
| Direction / DSI | `admin` |
| Ingénieur production / maintenance | `engineer` |
| Analyste data | `analyst` |
| Manager opérationnel (lecture) | `viewer` |

### 5.4 Critères d'acceptation

- [ ] Tous les comptes créés
- [ ] Tous les rôles attribués
- [ ] 100 % des emails de bienvenue envoyés
- [ ] Première connexion forcée à changer le mot de passe
- [ ] MFA configurable au choix (forcé pour `admin`)

---

## 6. Phase 4 — Validation parallèle (shadow mode)

Pendant **30 jours**, v2 et v3 fonctionnent en parallèle :

- v2 reste l'outil de référence pour les décisions opérationnelles
- v3 reçoit les mêmes données via `etl-service` (cron quotidien)
- Comparaison automatique des KPIs et prédictions

### 6.1 Métriques de comparaison

Cron quotidien dans `etl-service` :

```python
# pseudo-code
v2_kpis = read_v2_streamlit_kpis()
v3_kpis = call_production_service_kpis()
diff = compute_diff(v2_kpis, v3_kpis)
if abs(diff) > THRESHOLD:
    publish("alert.migration_drift", diff)
```

### 6.2 Critères de bascule

Au bout de 30 jours :

- [ ] Drift KPIs < 1 % en moyenne
- [ ] Aucun incident bloquant
- [ ] 100 % des utilisateurs formés
- [ ] Runbook validé (cf. [`runbook.md`](runbook.md))
- [ ] Backup pre-bascule effectué

---

## 7. Phase 5 — Bascule production

### 7.1 Jour J — checklist

1. [ ] Backup PostgreSQL complet
2. [ ] Backup snapshot Excel v2 → `backups/v2-final/`
3. [ ] Bannière "lecture seule" sur Streamlit v2
4. [ ] DNS `app.smartbarrel.td` → cluster v3
5. [ ] Notification équipe (email + SMS)
6. [ ] Astreinte renforcée 48h
7. [ ] Communication clients (si applicable)

### 7.2 Rollback

Si incident critique dans les 24h :

```bash
# 1. Bascule DNS retour vers Streamlit
./scripts/rollback-dns.sh

# 2. Désactivation des écritures v3 (lecture seule)
kubectl scale deployment production-service --replicas=0

# 3. Communication
./scripts/notify-rollback.sh
```

---

## 8. Phase 6 — Décommissionnement v2

**90 jours après la bascule** :

- [ ] Confirmer absence d'incident remontant à v2
- [ ] Archive complète : `backups/decommission/v2-final.tar.gz`
- [ ] Arrêt du conteneur Streamlit (`docker compose down`)
- [ ] Suppression des routes Traefik vers v2
- [ ] Conservation du code source dans le repo (tag `v2-final`)
- [ ] Mise à jour `README.md` racine pour rediriger vers SmartBarrel

---

## 9. Annexes

### 9.1 Tables de migration

```sql
CREATE SCHEMA IF NOT EXISTS etl;

CREATE TABLE etl.migration_runs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase         TEXT NOT NULL,         -- data | models | users | shadow | switch
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    status        TEXT NOT NULL,         -- running | success | failed | rolled_back
    rows_processed INTEGER,
    error_message TEXT,
    metadata      JSONB
);

CREATE TABLE etl.snapshots (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label       TEXT UNIQUE NOT NULL,    -- v2-snapshot-YYYYMMDD
    source_file TEXT,
    row_counts  JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 9.2 Contacts

| Sujet | Contact |
|-------|---------|
| Migration données | équipe ETL |
| Migration ML | équipe Data Science |
| Migration utilisateurs | équipe Sécurité |
| Bascule prod | DevOps + astreinte |

---

*Document vivant — mis à jour à chaque phase de migration.*
