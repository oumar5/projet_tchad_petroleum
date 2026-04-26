-- Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

-- Schemas (one per service)
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS production;
CREATE SCHEMA IF NOT EXISTS maintenance;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS etl;
CREATE SCHEMA IF NOT EXISTS notifications;

GRANT USAGE ON SCHEMA auth, production, maintenance, ml, etl, notifications TO smartbarrel;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth, production, maintenance, ml, etl, notifications
    GRANT ALL ON TABLES TO smartbarrel;
