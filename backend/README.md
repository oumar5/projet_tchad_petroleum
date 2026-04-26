# Backend SmartBarrel

Plateforme microservices pour l'optimisation des opérations pétrolières.
Cf. [`../docs/future-architecture.md`](../docs/future-architecture.md) pour la vision complète.

## Structure

```text
backend/
├── smartbarrel.compose.yml     # Stack dev complète (project name: smartbarrel)
├── .env.example
├── .env                        # créé depuis .env.example (git-ignoré)
├── Makefile
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
    ├── jwt/                    # Clés RS256 (dev)
    ├── postgres/init/          # SQL d'initialisation
    ├── traefik/
    └── k8s/
```

## Démarrage local

```bash
make jwt-keys     # génère les clés RS256
make dev-up       # docker compose up
make migrate      # applique les migrations Alembic
```

Services disponibles :

- API Gateway : `http://api.localhost`
- Traefik dashboard : `http://localhost:8080`
- PostgreSQL : `localhost:5432` (user: `smartbarrel`)
- Redis : `localhost:6379`
- RabbitMQ management : `http://localhost:15672` (guest/guest)
- MailHog : `http://localhost:8025`

## Tests

```bash
make test
```
