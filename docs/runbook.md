# 🚨 Runbook — Astreinte SmartBarrel

> Procédures opérationnelles pour l'équipe d'astreinte : incidents, rollback, restauration, escalade.
>
> **Public** : ingénieurs DevOps / SRE en astreinte.
> **Pré-requis** : accès kubectl + cluster prod + secrets manager + canal Slack `#astreinte`.

---

## Sommaire

1. [Contacts d'astreinte](#1-contacts-dastreinte)
2. [Niveaux de sévérité](#2-niveaux-de-sévérité)
3. [Diagnostic rapide](#3-diagnostic-rapide)
4. [Incidents fréquents](#4-incidents-fréquents)
5. [Rollback applicatif](#5-rollback-applicatif)
6. [Restauration base de données](#6-restauration-base-de-données)
7. [Rotation des secrets](#7-rotation-des-secrets)
8. [Escalade](#8-escalade)
9. [Post-mortem](#9-post-mortem)

---

## 1. Contacts d'astreinte

| Rôle | Canal | Délai max |
|------|-------|-----------|
| Astreinte L1 | Slack `#astreinte` + PagerDuty | 5 min |
| Astreinte L2 (lead DevOps) | Téléphone | 15 min |
| Astreinte L3 (CTO) | Téléphone | 30 min |
| Référent sécurité | Email + SMS | 1 h |
| Référent données | Email | 1 h |

PagerDuty : `smartbarrel-prod` service.

---

## 2. Niveaux de sévérité

| Sévérité | Critère | SLA réponse | SLA résolution |
|----------|---------|-------------|----------------|
| **SEV1** | Service totalement indisponible OU fuite de données | 5 min | 1 h |
| **SEV2** | Dégradation majeure (>50 % erreurs, latence x10) | 15 min | 4 h |
| **SEV3** | Fonctionnalité dégradée non bloquante | 1 h | 24 h |
| **SEV4** | Incident mineur, contournement possible | 4 h | 5 j |

---

## 3. Diagnostic rapide

### 3.1 Première vérification (≤ 2 min)

```bash
# État global du cluster
kubectl get pods -n smartbarrel
kubectl get nodes

# Endpoint de santé global
curl -s https://api.smartbarrel.td/health | jq

# Métriques Grafana
open https://grafana.smartbarrel.td/d/overview
```

### 3.2 Logs récents

```bash
# Logs centralisés (Loki via Grafana)
open https://grafana.smartbarrel.td/explore

# Direct kubectl (fallback)
kubectl logs -n smartbarrel -l app=auth-service --tail=200
kubectl logs -n smartbarrel -l app=production-service --tail=200
```

### 3.3 Tracing distribué

Si latence anormale, ouvrir Tempo et chercher `trace_id` retourné dans les erreurs RFC 7807.

---

## 4. Incidents fréquents

### 4.1 « 503 sur tous les endpoints »

**Symptôme** : Traefik renvoie 503 systématiquement.

**Diagnostic** :
```bash
kubectl get pods -n smartbarrel | grep -v Running
kubectl describe pod <pod-en-erreur>
```

**Causes habituelles** :
- Pod crashé en boucle → vérifier `kubectl logs --previous`
- Sonde liveness/readiness mal configurée
- Image récemment déployée KO → cf. [Rollback](#5-rollback-applicatif)

---

### 4.2 « Login en boucle / 401 systématique »

**Symptôme** : utilisateurs ne peuvent plus se connecter, JWT rejeté.

**Diagnostic** :
```bash
# Vérifier que la clé publique JWT est bien présente dans tous les services
kubectl exec -n smartbarrel deploy/production-service -- ls /etc/jwt
kubectl exec -n smartbarrel deploy/auth-service -- ls /etc/jwt

# Vérifier la cohérence des clés
kubectl get secret jwt-keys -n smartbarrel -o yaml
```

**Cause fréquente** : rotation de clé incomplète. Cf. [§7](#7-rotation-des-secrets).

**Mitigation immédiate** : redéployer la clé précédente (`kubectl rollout undo deployment auth-service -n smartbarrel`).

---

### 4.3 « Latence > 5s sur /production/kpis »

**Diagnostic** :
```bash
# Vérifier Redis
kubectl exec -n smartbarrel deploy/redis -- redis-cli INFO stats | grep keyspace

# Vérifier PostgreSQL
kubectl exec -n smartbarrel deploy/postgres -- psql -U smartbarrel -c \
  "SELECT query, state, wait_event, age(clock_timestamp(), query_start) AS dur
   FROM pg_stat_activity WHERE state != 'idle' ORDER BY dur DESC LIMIT 10;"
```

**Mitigations** :
- Si Redis vide → cache cold, attendre 5 min
- Si requête PG longue → killer la requête bloquante (`SELECT pg_cancel_backend(pid);`)
- Si connection pool saturé → scale up production-service (`kubectl scale --replicas=4`)

---

### 4.4 « Job d'entraînement ML bloqué »

**Diagnostic** :
```bash
kubectl logs -n smartbarrel -l app=ml-worker --tail=500
kubectl exec -n smartbarrel deploy/rabbitmq -- rabbitmqctl list_queues
```

**Mitigations** :
- Queue `ml.train` qui s'accumule → scaler les workers Celery
- Worker stuck → `kubectl rollout restart deployment ml-worker`
- Job impossible à finir → marquer `status=failed` dans `ml.jobs` + relancer manuellement

---

### 4.5 « Notifications non envoyées »

**Diagnostic** :
```bash
kubectl logs -n smartbarrel -l app=notification-service --tail=200
# Vérifier la queue
kubectl exec -n smartbarrel deploy/rabbitmq -- rabbitmqctl list_queues | grep notif
```

**Mitigations** :
- SMTP KO → vérifier credentials + connectivité
- FCM rate limit → batcher les envois
- Templates manquants → vérifier `notification-service:/app/templates/`

---

## 5. Rollback applicatif

### 5.1 Rollback d'un service spécifique

```bash
# Vérifier les révisions disponibles
kubectl rollout history deployment <service> -n smartbarrel

# Rollback à la révision précédente
kubectl rollout undo deployment <service> -n smartbarrel

# Rollback à une révision précise
kubectl rollout undo deployment <service> -n smartbarrel --to-revision=<N>

# Surveiller le rollout
kubectl rollout status deployment <service> -n smartbarrel
```

### 5.2 Rollback global (tous les services)

```bash
./scripts/rollback-all.sh <git-sha-cible>
```

Ce script :
1. Git checkout du SHA cible
2. Re-déploiement de toutes les images Docker
3. Vérification de santé post-rollback

### 5.3 Rollback DNS (bascule retour Streamlit v2)

À utiliser uniquement dans les 90 jours suivant la bascule v3 :

```bash
./scripts/rollback-dns.sh
```

Cf. [`migration-v2-to-v3.md`](migration-v2-to-v3.md) §7.2.

---

## 6. Restauration base de données

### 6.1 Liste des sauvegardes

```bash
aws s3 ls s3://smartbarrel-backups/postgres/ --recursive | tail -20
```

Conventions :
- `daily/YYYY-MM-DD.dump` (rétention 30j)
- `weekly/YYYY-Www.dump` (rétention 12 sem)
- `monthly/YYYY-MM.dump` (rétention 12 mois)

### 6.2 Restauration complète

⚠️ **Action destructive** — confirmer avec L2 minimum.

```bash
# 1. Mettre l'application en lecture seule
kubectl scale deployment production-service maintenance-service ml-service \
  --replicas=0 -n smartbarrel

# 2. Télécharger le dump
aws s3 cp s3://smartbarrel-backups/postgres/daily/YYYY-MM-DD.dump /tmp/

# 3. Restaurer
kubectl exec -n smartbarrel deploy/postgres -- pg_restore \
  --clean --if-exists --no-owner \
  -d smartbarrel /tmp/YYYY-MM-DD.dump

# 4. Vérifier l'intégrité
kubectl exec -n smartbarrel deploy/postgres -- psql -U smartbarrel -c \
  "SELECT schemaname, count(*) FROM pg_tables GROUP BY schemaname;"

# 5. Relancer les services
kubectl scale deployment production-service maintenance-service ml-service \
  --replicas=2 -n smartbarrel
```

### 6.3 Restauration ciblée (un schéma)

```bash
pg_restore --schema=production --clean --if-exists ...
```

---

## 7. Rotation des secrets

### 7.1 Clés JWT RS256

**Fréquence** : tous les 90 jours, ou immédiate en cas de compromission.

```bash
# 1. Générer une nouvelle paire
openssl genrsa -out jwt_private_new.pem 4096
openssl rsa -in jwt_private_new.pem -pubout -out jwt_public_new.pem

# 2. Ajouter la nouvelle clé publique dans tous les services (rotation à chaud)
kubectl create secret generic jwt-public-keys \
  --from-file=current=jwt_public.pem \
  --from-file=next=jwt_public_new.pem \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Redéployer les services qui valident le JWT (production, maintenance, ml, etc.)
kubectl rollout restart deployment -n smartbarrel \
  -l role=jwt-validator

# 4. Bascule de la clé privée sur auth-service
kubectl create secret generic jwt-private-key --from-file=jwt_private_new.pem \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment auth-service -n smartbarrel

# 5. Attendre 24h (durée max d'un access_token + refresh)

# 6. Retirer l'ancienne clé publique
kubectl create secret generic jwt-public-keys \
  --from-file=current=jwt_public_new.pem \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 7.2 Mots de passe DB / Redis / RabbitMQ

Procédure standard : rotation via Vault, redéploiement glissant.

### 7.3 Compromission immédiate

1. Révoquer les secrets compromis dans Vault
2. Forcer la déconnexion de tous les utilisateurs : `redis-cli FLUSHDB` sur la DB de blocklist (toutes les sessions tombent)
3. Notifier le référent sécurité
4. Lancer un scan d'intégrité

---

## 8. Escalade

### 8.1 Quand escalader

- SEV1 non résolu après 30 min → L2
- SEV1 non résolu après 1 h → L3
- Suspicion d'intrusion → référent sécurité immédiatement
- Perte de données → CTO + référent données

### 8.2 Comment escalader

1. Poster un message dans `#astreinte` avec :
   - Sévérité
   - Description (1 ligne)
   - Actions déjà tentées
   - Lien vers le ticket / dashboard
2. Appeler la personne en escalade (PagerDuty)
3. Mettre à jour le ticket toutes les 15 min minimum

### 8.3 Communication externe

- SEV1 > 30 min → bannière sur app + status page
- Reprise → message de rétablissement
- Post-mortem public si impact client

---

## 9. Post-mortem

À rédiger dans les **48h** après tout incident SEV1 ou SEV2.

### 9.1 Template

```markdown
# Post-mortem — <titre court> — <YYYY-MM-DD>

## Résumé
<3 lignes max>

## Impact
- Durée :
- Utilisateurs touchés :
- Services affectés :
- Pertes éventuelles :

## Timeline (UTC)
- HH:MM — détection
- HH:MM — diagnostic
- HH:MM — mitigation
- HH:MM — résolution

## Cause racine
<analyse 5 pourquoi>

## Ce qui a bien fonctionné
- ...

## Ce qui n'a pas fonctionné
- ...

## Actions correctives
| Action | Owner | Échéance |
|--------|-------|----------|
| ... | ... | ... |
```

### 9.2 Stockage

`docs/postmortems/YYYY-MM-DD-<slug>.md` — versionné dans le repo.

### 9.3 Revue d'équipe

Présenter en réunion d'équipe sous 1 semaine, sans recherche de bouc émissaire (blameless).

---

*Document vivant — mis à jour après chaque incident.*
