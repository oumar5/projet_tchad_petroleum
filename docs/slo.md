# 📈 Service Level Objectives (SLO)

> Cibles de performance et disponibilité de SmartBarrel — base contractuelle pour Enterprise (SLA 99,9%).

## 1. Disponibilité

| Périmètre | SLO | Mesure |
|---|---|---|
| API gateway (`api.smartbarrel.td`) | **99,9 %** mensuel | Sonde Prometheus `probe_success` toutes les 30 s |
| auth-service | 99,95 % | Idem |
| Autres services | 99,9 % | Idem |

Budget d'erreur : **43 min 49 s / mois** à 99,9 %.

## 2. Latence

| Endpoint | p95 | p99 |
|---|---|---|
| `GET /v1/auth/me` | < 150 ms | < 400 ms |
| `POST /v1/auth/login` | < 600 ms (bcrypt) | < 1,5 s |
| `GET /v1/production/kpis` (cache hit) | < 80 ms | < 250 ms |
| `GET /v1/production/kpis` (cache miss) | < 600 ms | < 1,5 s |
| `GET /v1/production/daily` | < 400 ms | < 1 s |
| `POST /v1/ml/predict/*` | < 800 ms | < 2 s |
| `POST /v1/ml/train` (acceptation) | < 200 ms | < 500 ms |

## 3. Throughput

- **API gateway** : ≥ 200 req/s soutenues, ≥ 500 req/s en pic
- **ml-service inference** : ≥ 50 req/s par pod
- **etl-service ingestion Excel** : ≥ 5000 lignes/s

## 4. Ressources

| Composant | CPU moyen | RAM moyen | Quotas K8s |
|---|---|---|---|
| auth-service | < 70 % | < 80 % | requests 0.25/256Mi · limits 1/1Gi |
| production-service | < 70 % | < 80 % | requests 0.5/512Mi · limits 2/2Gi |
| maintenance-service | < 70 % | < 80 % | requests 0.25/256Mi · limits 1/1Gi |
| ml-service | < 80 % | < 85 % | requests 1/1Gi · limits 4/4Gi |
| etl-service | < 60 % | < 70 % | requests 0.5/512Mi · limits 2/2Gi |
| notification-service | < 50 % | < 60 % | requests 0.25/256Mi · limits 1/512Mi |

## 5. Couverture qualité

| Métrique | Seuil |
|---|---|
| Couverture tests backend (unit) | ≥ 70 % (gate CI), cible 80 % |
| Couverture tests backend (e2e) | endpoints critiques : login, /me, KPIs, predict |
| Lint backend | ruff sans erreurs (warnings autorisés) |
| `flutter analyze` | 0 issue |
| Duplication code | < 5 % (sonarqube si configuré) |

## 6. Mesure & Alertes

- Dashboards Grafana provisionnés via [`infra/observability/grafana/`](../backend/infra/observability/grafana/)
- Alertes Prometheus à configurer pour : `availability < 99.9%`, `p95_latency > seuil`, `error_rate > 1%`
- Burn rate budget d'erreur : alerte si > 14× sur 1 h ou > 6× sur 6 h
