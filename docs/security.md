# 🔐 Politique de Sécurité — SmartBarrel

> Politique de sécurité applicative et organisationnelle de SmartBarrel.
>
> **Public** : ingénieurs, ops, auditeurs.
> **Référence** : OWASP Top 10, ISO 27001, RFC 7807, RFC 7519 (JWT).

---

## Sommaire

1. [Principes directeurs](#1-principes-directeurs)
2. [Authentification](#2-authentification)
3. [Autorisation (RBAC)](#3-autorisation-rbac)
4. [Gestion des secrets](#4-gestion-des-secrets)
5. [Chiffrement](#5-chiffrement)
6. [MFA](#6-mfa)
7. [Audit log](#7-audit-log)
8. [Sécurité réseau](#8-sécurité-réseau)
9. [Protection des données](#9-protection-des-données)
10. [Réponse à incident](#10-réponse-à-incident)
11. [Conformité](#11-conformité)

---

## 1. Principes directeurs

### 1.1 Defense in depth

Cinq couches indépendantes :

```
Réseau (TLS, firewall, rate limit)
  ▼
Gateway (JWT validation, anti-replay)
  ▼
Service (RBAC, validation Pydantic)
  ▼
Données (chiffrement at-rest, schémas isolés)
  ▼
Audit (logs immuables, alertes)
```

### 1.2 Principe du moindre privilège

- Un service n'écrit que dans son schéma PostgreSQL
- Un utilisateur n'a que les permissions strictement nécessaires
- Les workers Celery n'ont pas accès aux endpoints HTTP
- Les conteneurs tournent en `non-root` (UID 1000)

### 1.3 Zéro confiance interne

- Tout appel inter-service est authentifié (JWT machine ou mTLS)
- Pas de communication SQL cross-schéma : uniquement via API REST
- Validation systématique côté receveur même si l'émetteur est interne

---

## 2. Authentification

### 2.1 JWT RS256

| Paramètre | Valeur |
|-----------|--------|
| Algorithme | RS256 (4096 bits) |
| Émetteur | `auth-service` (seul détenteur de la clé privée) |
| Validateurs | Tous les microservices via clé publique distribuée |
| Durée access_token | 15 minutes |
| Durée refresh_token | 7 jours |
| Stockage côté client | refresh dans `flutter_secure_storage`, access en mémoire seule |
| Révocation | Blocklist Redis (TTL = exp restante) |

### 2.2 Claims standards

```json
{
  "sub": "user-uuid",
  "email": "...",
  "roles": ["engineer"],
  "permissions": [...],
  "iat": 1735200000,
  "exp": 1735200900,
  "jti": "token-uuid",
  "type": "access"
}
```

### 2.3 Politique mot de passe

- Minimum **12 caractères**
- Au moins 1 majuscule, 1 minuscule, 1 chiffre, 1 caractère spécial
- Hashing **bcrypt** (cost ≥ 12)
- Pas de stockage en clair, jamais dans les logs
- Vérification contre la base [HIBP Pwned Passwords](https://haveibeenpwned.com/Passwords) à la création
- Expiration : 180 jours pour rôle `admin`, jamais pour les autres (recommandation NIST)

### 2.4 Reset password

1. Demande via `POST /v1/auth/password/reset` (email)
2. Token à usage unique de 32 octets, valide 1 heure
3. Stocké hashé en base (pas en clair)
4. Email envoyé via `notification-service`
5. Confirmation via `POST /v1/auth/password/confirm`

### 2.5 Brute-force

- Rate limit `/auth/login` : 10 tentatives / IP / 15 min
- Verrouillage progressif du compte : 5 échecs → 15 min de lock
- Notification email à l'utilisateur après 3 échecs
- Logs de tentatives dans `auth.audit_log`

---

## 3. Autorisation (RBAC)

### 3.1 Modèle

Cf. [`future-architecture.md`](future-architecture.md) §5.

User ↔ N Roles ↔ N Permissions.

### 3.2 Format des permissions

`<resource>:<action>` — wildcards `*` autorisés.

### 3.3 Vérification

Middleware FastAPI commun (`shared/auth.require_permission`) appliqué via `Depends()` sur chaque endpoint.

### 3.4 Octroi de rôles

- Uniquement par un `admin`
- Tracé dans `auth.audit_log` avec `granted_by`
- Notification email automatique à l'utilisateur

---

## 4. Gestion des secrets

### 4.1 Outils

- **Production** : HashiCorp Vault (ou Kubernetes Secrets si Vault indisponible)
- **Développement** : `.env` ignoré dans `.gitignore`, **jamais** commité

### 4.2 Inventaire des secrets

| Secret | Stockage | Rotation |
|--------|----------|----------|
| Clé privée JWT RS256 | Vault / K8s secret `jwt-private-key` | 90 jours |
| Clé publique JWT | ConfigMap (pas confidentiel) | avec privée |
| Mot de passe PostgreSQL par service | Vault | 90 jours |
| Mot de passe Redis | Vault | 90 jours |
| Identifiants RabbitMQ | Vault | 90 jours |
| API keys SMTP | Vault | annuel ou compromission |
| Clés FCM | Vault | jamais sauf compromission |
| Token CI/CD GitHub | GitHub Secrets | 6 mois |

### 4.3 Bonnes pratiques

- Aucun secret en clair dans les variables d'environnement de manifest Git
- Aucun secret dans les logs (filtrer avec un middleware)
- Aucun secret dans les images Docker
- Pre-commit hook `detect-secrets` activé

---

## 5. Chiffrement

### 5.1 Au repos (at-rest)

| Donnée | Méthode |
|--------|---------|
| Volumes PostgreSQL | AES-256 (chiffrement du disque K8s / EBS) |
| Backups S3/MinIO | SSE-S3 (AES-256) |
| Modèles ML stockés | SSE-S3 |
| Logs Loki | Chiffrement disque sous-jacent |

### 5.2 En transit (in-transit)

| Flux | Protocole |
|------|-----------|
| Client ↔ Gateway | TLS 1.3 (TLS 1.2 minimum) |
| Gateway ↔ services | mTLS (cluster K8s) |
| Service ↔ PostgreSQL | TLS 1.3 |
| Service ↔ Redis | TLS 1.3 |
| Service ↔ RabbitMQ | TLS 1.3 + SASL |
| Workers ↔ S3 | HTTPS |

### 5.3 Données sensibles applicatives

Chiffrement applicatif additionnel (Fernet AES-128) pour :
- Secret MFA TOTP (`auth.users.mfa_secret`)
- Données personnelles non-clé (anonymisation par hash SHA-256)

---

## 6. MFA

### 6.1 Politique

- **Obligatoire** pour les rôles `admin` et `engineer`
- **Optionnel** pour `analyst` et `viewer`
- Méthode : **TOTP** (RFC 6238) via apps Google Authenticator, Authy, 1Password

### 6.2 Activation

```
POST /v1/auth/mfa/enable    → renvoie le QR code + secret base32
POST /v1/auth/mfa/verify    → confirme avec un premier code
POST /v1/auth/mfa/disable   → après vérification du mot de passe + code
```

### 6.3 Codes de récupération

À l'activation, génération de **10 codes** à usage unique (16 caractères chacun). Stockés hashés en base, affichés une seule fois à l'utilisateur.

### 6.4 Reset MFA

Uniquement par un `admin` après vérification d'identité hors-bande (téléphone + email). Tracé dans l'audit log.

---

## 7. Audit log

### 7.1 Périmètre

Toutes les actions sensibles sont tracées dans `auth.audit_log` :

- Login (succès / échec)
- Logout
- Reset password (demandé / effectué)
- Activation / désactivation MFA
- Création / modification / suppression d'utilisateur
- Changement de rôle
- Création / modification / suppression de permission
- Export de données
- Entraînement / activation d'un modèle ML

### 7.2 Schéma

```sql
CREATE TABLE auth.audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES auth.users(id),
    event       TEXT NOT NULL,
    metadata    JSONB,
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON auth.audit_log (user_id, created_at DESC);
CREATE INDEX ON auth.audit_log (event, created_at DESC);
```

### 7.3 Rétention

- **2 ans** pour les événements liés à l'authentification
- **5 ans** pour les modifications de rôles / permissions (compliance)
- Archivage froid (S3 Glacier) au-delà

### 7.4 Immuabilité

- Pas d'UPDATE ni DELETE sur la table (revoke des privilèges DB)
- Réplication temps réel vers stockage append-only séparé
- Hash chaîné optionnel (chaque ligne contient le hash de la précédente)

---

## 8. Sécurité réseau

### 8.1 Périmètre extérieur

- Pare-feu cloud / on-premise : seuls les ports 80, 443, 22 (admin) ouverts
- WAF devant Traefik (rules OWASP CRS)
- Rate limiting au niveau gateway (cf. [`api-reference.md`](api-reference.md) §9)
- Anti-DDoS basique (Traefik) + escalade si nécessaire

### 8.2 Cluster K8s

- NetworkPolicies : un service ne parle qu'aux services dont il dépend
- Pas d'accès direct depuis Internet vers les pods (uniquement via Ingress)
- mTLS interne (Istio ou Linkerd à évaluer en Phase 5)

### 8.3 Headers HTTP de sécurité

Configurés dans Traefik :

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; ...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

---

## 9. Protection des données

### 9.1 Classification

| Niveau | Exemples | Traitement |
|--------|----------|------------|
| **Public** | Documentation, sales pitch | Aucune restriction |
| **Interne** | Architecture, runbooks | Accès employés |
| **Confidentiel** | Données de production, KPIs | RBAC strict |
| **Critique** | Mots de passe, secrets, JWT | Chiffré + accès minimal |

### 9.2 Souveraineté

- **Hébergement** : on-premise N'Djamena ou cloud panafricain (selon décision finale)
- Aucune donnée client ne quitte le périmètre sans accord écrit
- Conformité aux réglementations nationales tchadiennes

### 9.3 RGPD-like

Bien que non soumis directement au RGPD, SmartBarrel applique :
- Droit d'accès à ses données (export user)
- Droit de rectification
- Droit à l'effacement (anonymisation, audit log conservé)
- Minimisation : ne collecter que le strictement nécessaire

### 9.4 Anonymisation

Données exportées pour analyse hors-prod :
- Emails → hash SHA-256 tronqué (8 caractères)
- Noms → suppression
- IDs métier (puits, blocs) → conservés

---

## 10. Réponse à incident

### 10.1 Détection

- Alertes Prometheus sur signaux anormaux : taux d'erreur, latence, login failures
- Monitoring `auth.audit_log` : pattern de bruteforce, connexions depuis IPs inhabituelles
- Notifications Slack `#security-alerts`

### 10.2 Procédure

Cf. [`runbook.md`](runbook.md) §10 (réponse à incident sécurité spécifique) :

1. **Confinement** : isoler le ou les services compromis
2. **Préservation des preuves** : snapshot logs, dumps mémoire, audit log
3. **Éradication** : rotation secrets, patch, redéploiement propre
4. **Restauration** : retour service contrôlé
5. **Leçons apprises** : post-mortem dans les 48h

### 10.3 Notification externe

- Compromission de données client → notification au client sous 72h (engagement contractuel)
- Décision de notification publique : CTO + juridique

---

## 11. Conformité

### 11.1 Audits

- **Interne** : revue trimestrielle par le référent sécurité
- **Externe** : pen-test annuel par un prestataire indépendant
- **Avant mise en prod** : pen-test obligatoire (cf. [`TASKS.md`](../TASKS.md) §8)

### 11.2 Documentation à maintenir

- Cette politique (révision annuelle)
- [`runbook.md`](runbook.md) (révision après chaque incident)
- Registre des traitements (RGPD-like)
- Inventaire des secrets et dates de rotation

### 11.3 Formation

- Onboarding sécurité obligatoire pour tout nouveau dev
- Sensibilisation phishing semestrielle
- Revue des bonnes pratiques OWASP avant chaque sprint majeur

---

## 12. Contacts

| Sujet | Contact |
|-------|---------|
| Questions sécurité | référent sécurité |
| Vulnérabilité découverte | `security@smartbarrel.td` (PGP disponible) |
| Disclosure responsable | publication 90j après fix |

---

*Document vivant — révision annuelle minimum, mise à jour après tout incident sécurité.*
