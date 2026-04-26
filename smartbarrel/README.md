# SmartBarrel — Monorepo

Plateforme microservices pour l'optimisation des opérations pétrolières.
Cf. [`../docs/future-architecture.md`](../docs/future-architecture.md) pour la vision complète.

## Structure

```
smartbarrel/
├── services/
│   ├── auth_service/           # JWT + RBAC + MFA
│   ├── production_service/     # CRUD prod, KPIs, exports
│   ├── maintenance_service/    # Pannes, interventions
│   ├── ml_service/             # Inference + training async
│   ├── etl_service/            # Ingestion Excel/SCADA
│   └── notification_service/   # Email + FCM
├── shared/                     # Libs Python communes
│   ├── auth/                   # Middleware JWT, RBAC
│   ├── db/                     # SQLAlchemy base
│   ├── messaging/              # RabbitMQ wrappers
│   ├── logging/                # Logger JSON + trace_id
│   └── config/                 # Pydantic Settings
└── infra/
    ├── docker-compose.dev.yml
    ├── docker-compose.prod.yml
    ├── traefik/
    ├── postgres/
    └── k8s/
```

## Démarrage local

```bash
cd infra
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d
```

Services disponibles :
- API Gateway : http://api.localhost
- Traefik dashboard : http://traefik.localhost:8080
- PostgreSQL : localhost:5432 (user: smartbarrel)
- Redis : localhost:6379
- RabbitMQ management : http://localhost:15672 (guest/guest)

## Tests

```bash
cd services/<service>
pytest
```
