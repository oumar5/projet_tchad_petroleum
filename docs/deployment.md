# 🚀 Guide de Déploiement

## Vue d'Ensemble

Ce document détaille les processus de déploiement, configuration production, et maintenance du système de modélisation prédictive de Tchad Petroleum Company.

## 🎯 Objectifs du Déploiement

- **Production** : Déploiement stable et sécurisé
- **Scalabilité** : Architecture évolutive
- **Monitoring** : Surveillance et alertes
- **Maintenance** : Mises à jour et sauvegarde
- **Sécurité** : Protection des données et accès

## 🐳 Déploiement Docker

### Architecture de Déploiement

```
Production Environment
├── 🌐 Reverse Proxy (Nginx)
├── 🐳 Application Container (Streamlit)
├── 📊 Database (PostgreSQL) [Futur]
├── 📈 Monitoring (Prometheus/Grafana) [Futur]
└── 🔒 SSL/TLS Certificates
```

### Configuration Docker Production

#### 📁 Structure des Fichiers
```
deployment/
├── docker-compose.prod.yml     # Configuration production
├── docker-compose.staging.yml  # Configuration staging
├── nginx/
│   ├── nginx.conf              # Configuration Nginx
│   └── ssl/                    # Certificats SSL
├── scripts/
│   ├── deploy.sh               # Script de déploiement
│   ├── backup.sh               # Script de sauvegarde
│   └── health-check.sh         # Vérification santé
└── monitoring/
    ├── prometheus.yml          # Configuration monitoring
    └── grafana/                # Dashboards Grafana
```

#### 🐳 Docker Compose Production
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: tchad-petroleum-app-prod
    restart: unless-stopped
    volumes:
      # Données persistantes uniquement
      - ./data:/app/data:ro
      - ./logs:/app/logs
      - app-models:/app/models  # Volume pour modèles entraînés
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  nginx:
    image: nginx:alpine
    container_name: tchad-petroleum-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - streamlit-app
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Base de données future
  # postgres:
  #   image: postgres:15-alpine
  #   container_name: tchad-petroleum-db
  #   restart: unless-stopped
  #   environment:
  #     POSTGRES_DB: petroleum_db
  #     POSTGRES_USER: petroleum_user
  #     POSTGRES_PASSWORD_FILE: /run/secrets/db_password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #     - ./backups:/backups
  #   networks:
  #     - app-network
  #   secrets:
  #     - db_password

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  app-models:
    driver: local
  # postgres_data:
  #   driver: local

# secrets:
#   db_password:
#     file: ./secrets/db_password.txt
```

#### 🐳 Dockerfile Production
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder

# Variables d'environnement pour build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système pour build
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage de production
FROM python:3.11-slim as production

# Variables d'environnement production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

# Dépendances runtime uniquement
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Utilisateur non-root pour sécurité
RUN useradd -m -u 1000 appuser
USER appuser
WORKDIR /app

# Copier les dépendances depuis builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copier le code application
COPY --chown=appuser:appuser . .

# Créer les dossiers nécessaires
RUN mkdir -p logs models

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Exposition du port
EXPOSE 8501

# Commande de démarrage
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Configuration Nginx

#### 🌐 Configuration Nginx
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Upstream pour Streamlit
    upstream streamlit {
        server streamlit-app:8501;
    }
    
    # Redirection HTTP vers HTTPS
    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }
    
    # Configuration HTTPS
    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;
        
        # Certificats SSL
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        
        # Configuration SSL moderne
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        # OCSP Stapling
        ssl_stapling on;
        ssl_stapling_verify on;
        
        # Client max body size
        client_max_body_size 100M;
        
        # Proxy vers Streamlit
        location / {
            proxy_pass http://streamlit;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Rate limiting
            limit_req zone=api burst=20 nodelay;
        }
        
        # WebSocket support pour Streamlit
        location /_stcore/stream {
            proxy_pass http://streamlit;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check endpoint
        location /health {
            proxy_pass http://streamlit/_stcore/health;
            access_log off;
        }
        
        # Static files caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            proxy_pass http://streamlit;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 🔧 Scripts de Déploiement

### Script de Déploiement Principal

```bash
#!/bin/bash
# scripts/deploy.sh

set -e  # Arrêt en cas d'erreur

# Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
BACKUP_BEFORE_DEPLOY=${3:-true}

echo "🚀 Déploiement Tchad Petroleum - Environnement: $ENVIRONMENT"

# Vérifications préalables
echo "📋 Vérifications préalables..."
if [ ! -f "docker-compose.$ENVIRONMENT.yml" ]; then
    echo "❌ Fichier docker-compose.$ENVIRONMENT.yml non trouvé"
    exit 1
fi

if [ ! -f ".env.$ENVIRONMENT" ]; then
    echo "❌ Fichier .env.$ENVIRONMENT non trouvé"
    exit 1
fi

# Sauvegarde avant déploiement
if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
    echo "💾 Sauvegarde avant déploiement..."
    ./scripts/backup.sh
fi

# Arrêt des services existants
echo "⏹️ Arrêt des services existants..."
docker-compose -f docker-compose.$ENVIRONMENT.yml down --remove-orphans

# Nettoyage des images obsolètes
echo "🧹 Nettoyage des images obsolètes..."
docker image prune -f

# Construction des nouvelles images
echo "🔨 Construction des images..."
docker-compose -f docker-compose.$ENVIRONMENT.yml build --no-cache

# Démarrage des services
echo "▶️ Démarrage des services..."
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d

# Attente du démarrage
echo "⏳ Attente du démarrage des services..."
sleep 30

# Vérification de santé
echo "🏥 Vérification de santé..."
./scripts/health-check.sh

if [ $? -eq 0 ]; then
    echo "✅ Déploiement réussi !"
    
    # Nettoyage post-déploiement
    echo "🧹 Nettoyage post-déploiement..."
    docker system prune -f
    
    echo "📊 État des services:"
    docker-compose -f docker-compose.$ENVIRONMENT.yml ps
else
    echo "❌ Échec du déploiement - Rollback..."
    
    # Rollback automatique
    docker-compose -f docker-compose.$ENVIRONMENT.yml down
    
    # Restauration depuis sauvegarde si disponible
    if [ -f "backups/latest.tar.gz" ]; then
        echo "🔄 Restauration depuis sauvegarde..."
        ./scripts/restore.sh backups/latest.tar.gz
    fi
    
    exit 1
fi

echo "🎉 Déploiement terminé avec succès !"
```

### Script de Vérification de Santé

```bash
#!/bin/bash
# scripts/health-check.sh

set -e

ENVIRONMENT=${1:-production}
MAX_RETRIES=10
RETRY_INTERVAL=5

echo "🏥 Vérification de santé des services..."

# Fonction de vérification HTTP
check_http_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        echo "📡 Test $url (tentative $((retries + 1))/$MAX_RETRIES)..."
        
        if curl -f -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
            echo "✅ $url répond correctement"
            return 0
        fi
        
        retries=$((retries + 1))
        sleep $RETRY_INTERVAL
    done
    
    echo "❌ $url ne répond pas après $MAX_RETRIES tentatives"
    return 1
}

# Fonction de vérification Docker
check_docker_service() {
    local service_name=$1
    
    echo "🐳 Vérification du service Docker: $service_name"
    
    if docker-compose -f docker-compose.$ENVIRONMENT.yml ps | grep -q "$service_name.*Up"; then
        echo "✅ Service $service_name est actif"
        return 0
    else
        echo "❌ Service $service_name n'est pas actif"
        return 1
    fi
}

# Vérifications des services Docker
check_docker_service "streamlit-app" || exit 1
check_docker_service "nginx" || exit 1

# Vérifications des endpoints HTTP
check_http_endpoint "http://localhost/health" 200 || exit 1
check_http_endpoint "https://localhost" 200 || exit 1

# Vérification des logs pour erreurs critiques
echo "📋 Vérification des logs..."
if docker-compose -f docker-compose.$ENVIRONMENT.yml logs --tail=50 | grep -i "error\|exception\|failed" | grep -v "INFO\|DEBUG"; then
    echo "⚠️ Erreurs détectées dans les logs"
    # Ne pas échouer pour les erreurs non-critiques
fi

# Vérification de l'utilisation des ressources
echo "📊 Vérification des ressources..."
CPU_USAGE=$(docker stats --no-stream --format "table {{.CPUPerc}}" | tail -n +2 | sed 's/%//' | sort -nr | head -1)
MEM_USAGE=$(docker stats --no-stream --format "table {{.MemPerc}}" | tail -n +2 | sed 's/%//' | sort -nr | head -1)

echo "💻 CPU max: ${CPU_USAGE}%"
echo "🧠 Mémoire max: ${MEM_USAGE}%"

if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
    echo "⚠️ Utilisation CPU élevée: ${CPU_USAGE}%"
fi

if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    echo "⚠️ Utilisation mémoire élevée: ${MEM_USAGE}%"
fi

echo "✅ Vérification de santé terminée avec succès"
```

### Script de Sauvegarde

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="tchad_petroleum_backup_$TIMESTAMP"
RETENTION_DAYS=30

echo "💾 Début de la sauvegarde..."

# Création du dossier de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarde des données
echo "📊 Sauvegarde des données..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" data/ || true

# Sauvegarde des logs
echo "📋 Sauvegarde des logs..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz" logs/ || true

# Sauvegarde des modèles entraînés
echo "🤖 Sauvegarde des modèles..."
if [ -d "models" ]; then
    tar -czf "$BACKUP_DIR/${BACKUP_NAME}_models.tar.gz" models/ || true
fi

# Sauvegarde de la configuration
echo "⚙️ Sauvegarde de la configuration..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" \
    docker-compose*.yml \
    .env* \
    nginx/ \
    scripts/ || true

# Export des volumes Docker
echo "🐳 Export des volumes Docker..."
docker run --rm -v tchad-petroleum_app-models:/data -v $(pwd)/$BACKUP_DIR:/backup \
    alpine tar -czf /backup/${BACKUP_NAME}_volumes.tar.gz -C /data . || true

# Création d'une archive complète
echo "📦 Création de l'archive complète..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz" \
    "$BACKUP_DIR/${BACKUP_NAME}_"*.tar.gz

# Lien vers la dernière sauvegarde
ln -sf "${BACKUP_NAME}_complete.tar.gz" "$BACKUP_DIR/latest.tar.gz"

# Nettoyage des anciennes sauvegardes
echo "🧹 Nettoyage des anciennes sauvegardes..."
find $BACKUP_DIR -name "tchad_petroleum_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete || true

# Vérification de l'intégrité
echo "🔍 Vérification de l'intégrité..."
if tar -tzf "$BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz" > /dev/null; then
    echo "✅ Sauvegarde créée avec succès: ${BACKUP_NAME}_complete.tar.gz"
    
    # Taille de la sauvegarde
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz" | cut -f1)
    echo "📏 Taille de la sauvegarde: $BACKUP_SIZE"
else
    echo "❌ Erreur lors de la création de la sauvegarde"
    exit 1
fi

echo "💾 Sauvegarde terminée avec succès"
```

## 🔒 Sécurité

### Configuration SSL/TLS

#### 🔐 Génération des Certificats
```bash
# Avec Let's Encrypt (Certbot)
sudo apt-get install certbot python3-certbot-nginx

# Génération du certificat
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Renouvellement automatique
sudo crontab -e
# Ajouter: 0 12 * * * /usr/bin/certbot renew --quiet

# Ou avec Docker
docker run -it --rm --name certbot \
    -v "/etc/letsencrypt:/etc/letsencrypt" \
    -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
    -p 80:80 \
    certbot/certbot certonly --standalone -d your-domain.com
```

#### 🛡️ Configuration de Sécurité
```yaml
# docker-compose.prod.yml - Section sécurité
services:
  streamlit-app:
    environment:
      # Désactiver le mode debug
      - STREAMLIT_SERVER_ENABLE_CORS=false
      - STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
      - STREAMLIT_LOGGER_LEVEL=INFO
    
    # Utilisateur non-root
    user: "1000:1000"
    
    # Limitations de ressources
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    
    # Pas de privilèges élevés
    privileged: false
    
    # Système de fichiers en lecture seule
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
```

### Gestion des Secrets

#### 🔑 Docker Secrets
```yaml
# docker-compose.prod.yml
secrets:
  db_password:
    file: ./secrets/db_password.txt
  ssl_cert:
    file: ./secrets/ssl_cert.pem
  ssl_key:
    file: ./secrets/ssl_key.pem

services:
  app:
    secrets:
      - db_password
      - ssl_cert
      - ssl_key
```

#### 🔐 Variables d'Environnement
```bash
# .env.production
# Ne jamais commiter ce fichier !

# Base de données
DB_HOST=localhost
DB_PORT=5432
DB_NAME=petroleum_db
DB_USER=petroleum_user
# DB_PASSWORD défini via Docker secret

# Application
SECRET_KEY=your-very-long-secret-key-here
JWT_SECRET=another-secret-for-jwt

# Monitoring
MONITORING_TOKEN=monitoring-token

# Email (pour alertes)
SMTP_HOST=smtp.company.com
SMTP_PORT=587
SMTP_USER=alerts@company.com
# SMTP_PASSWORD défini via Docker secret
```

## 📊 Monitoring et Logging

### Configuration Logging

#### 📝 Logging Centralisé
```yaml
# docker-compose.prod.yml - Logging
services:
  streamlit-app:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
        labels: "service=streamlit,environment=production"
    
  nginx:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
        labels: "service=nginx,environment=production"
```

#### 📊 Monitoring avec Prometheus (Futur)
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'streamlit-app'
    static_configs:
      - targets: ['streamlit-app:8501']
    metrics_path: '/metrics'
    scrape_interval: 30s
  
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
    scrape_interval: 30s
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Alertes et Notifications

#### 🚨 Script d'Alertes
```bash
#!/bin/bash
# scripts/alerts.sh

# Configuration
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
EMAIL_RECIPIENT="admin@company.com"
SERVICE_NAME="Tchad Petroleum App"

# Fonction d'envoi d'alerte
send_alert() {
    local severity=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Slack
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"[$severity] $SERVICE_NAME - $timestamp\\n$message\"}" \
        $SLACK_WEBHOOK
    
    # Email
    echo "$message" | mail -s "[$severity] $SERVICE_NAME Alert" $EMAIL_RECIPIENT
    
    # Log local
    echo "[$timestamp] [$severity] $message" >> logs/alerts.log
}

# Vérifications automatiques
check_service_health() {
    if ! curl -f -s http://localhost/health > /dev/null; then
        send_alert "CRITICAL" "Service non accessible - Health check échoué"
        return 1
    fi
    
    # Vérification de l'utilisation des ressources
    CPU_USAGE=$(docker stats --no-stream --format "{{.CPUPerc}}" streamlit-app | sed 's/%//')
    MEM_USAGE=$(docker stats --no-stream --format "{{.MemPerc}}" streamlit-app | sed 's/%//')
    
    if (( $(echo "$CPU_USAGE > 85" | bc -l) )); then
        send_alert "WARNING" "Utilisation CPU élevée: ${CPU_USAGE}%"
    fi
    
    if (( $(echo "$MEM_USAGE > 85" | bc -l) )); then
        send_alert "WARNING" "Utilisation mémoire élevée: ${MEM_USAGE}%"
    fi
    
    return 0
}

# Exécution des vérifications
check_service_health
```

## 🔄 Maintenance et Mises à Jour

### Processus de Mise à Jour

#### 🔄 Mise à Jour Rolling
```bash
#!/bin/bash
# scripts/rolling-update.sh

set -e

NEW_VERSION=$1
if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "🔄 Mise à jour rolling vers la version $NEW_VERSION"

# 1. Sauvegarde préventive
echo "💾 Sauvegarde préventive..."
./scripts/backup.sh

# 2. Construction de la nouvelle image
echo "🔨 Construction de la nouvelle image..."
docker build -t tchad-petroleum:$NEW_VERSION -f Dockerfile.prod .

# 3. Test de la nouvelle image
echo "🧪 Test de la nouvelle image..."
docker run --rm -d --name test-app \
    -p 8502:8501 \
    tchad-petroleum:$NEW_VERSION

# Attendre le démarrage
sleep 30

# Test de santé
if curl -f -s http://localhost:8502/_stcore/health > /dev/null; then
    echo "✅ Nouvelle image testée avec succès"
    docker stop test-app
else
    echo "❌ Test de la nouvelle image échoué"
    docker stop test-app
    exit 1
fi

# 4. Mise à jour du service
echo "🔄 Mise à jour du service..."
docker-compose -f docker-compose.prod.yml up -d --no-deps streamlit-app

# 5. Vérification post-mise à jour
echo "🏥 Vérification post-mise à jour..."
sleep 30
./scripts/health-check.sh

if [ $? -eq 0 ]; then
    echo "✅ Mise à jour réussie vers la version $NEW_VERSION"
    
    # Nettoyage des anciennes images
    docker image prune -f
else
    echo "❌ Mise à jour échouée - Rollback..."
    
    # Rollback vers la version précédente
    docker-compose -f docker-compose.prod.yml down
    ./scripts/restore.sh backups/latest.tar.gz
    
    exit 1
fi
```

### Maintenance Programmée

#### 🕐 Cron Jobs
```bash
# Crontab pour maintenance automatique
# crontab -e

# Sauvegarde quotidienne à 2h du matin
0 2 * * * /path/to/project/scripts/backup.sh

# Vérification de santé toutes les 5 minutes
*/5 * * * * /path/to/project/scripts/health-check.sh

# Nettoyage des logs hebdomadaire
0 3 * * 0 /path/to/project/scripts/cleanup-logs.sh

# Mise à jour des certificats SSL mensuelle
0 4 1 * * /usr/bin/certbot renew --quiet

# Redémarrage mensuel pour maintenance
0 5 1 * * /path/to/project/scripts/maintenance-restart.sh
```

#### 🧹 Script de Nettoyage
```bash
#!/bin/bash
# scripts/cleanup.sh

echo "🧹 Début du nettoyage système..."

# Nettoyage des logs anciens
echo "📋 Nettoyage des logs..."
find logs/ -name "*.log" -mtime +30 -delete
find logs/ -name "*.log.*" -mtime +7 -delete

# Nettoyage Docker
echo "🐳 Nettoyage Docker..."
docker system prune -f
docker volume prune -f
docker image prune -a -f

# Nettoyage des sauvegardes anciennes
echo "💾 Nettoyage des sauvegardes..."
find backups/ -name "*.tar.gz" -mtime +60 -delete

# Nettoyage des fichiers temporaires
echo "🗑️ Nettoyage des fichiers temporaires..."
find /tmp -name "streamlit-*" -mtime +1 -delete 2>/dev/null || true

# Vérification de l'espace disque
echo "💽 Vérification de l'espace disque..."
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "⚠️ Espace disque faible: ${DISK_USAGE}%"
    # Envoyer une alerte
    ./scripts/alerts.sh
fi

echo "✅ Nettoyage terminé"
```

## 🌍 Déploiement Multi-Environnements

### Environnements

#### 🧪 Staging
```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: tchad-petroleum-staging
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=staging
      - LOG_LEVEL=DEBUG
      - STREAMLIT_SERVER_PORT=8501
    networks:
      - staging-network

networks:
  staging-network:
    driver: bridge
```

#### 🏭 Production
```bash
# Configuration par environnement
# .env.production
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
STREAMLIT_SERVER_HEADLESS=true

# .env.staging
ENVIRONMENT=staging
LOG_LEVEL=DEBUG
DEBUG=true
STREAMLIT_SERVER_HEADLESS=false
```

### Pipeline CI/CD (Exemple)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      - name: Run tests
        run: pytest tests/
  
  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to staging
        run: |
          # Déploiement staging
          ./scripts/deploy.sh staging
  
  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Déploiement production
          ./scripts/deploy.sh production
```

## 🔍 Dépannage Déploiement

### Problèmes Courants

#### 🚨 "Service ne démarre pas"
```bash
# Vérifier les logs
docker-compose logs streamlit-app

# Vérifier la configuration
docker-compose config

# Vérifier les ressources
docker stats

# Redémarrer le service
docker-compose restart streamlit-app
```

#### 🚨 "Certificat SSL expiré"
```bash
# Renouveler le certificat
certbot renew

# Redémarrer Nginx
docker-compose restart nginx

# Vérifier la validité
openssl x509 -in /etc/nginx/ssl/fullchain.pem -text -noout
```

#### 🚨 "Performance dégradée"
```bash
# Vérifier les ressources
docker stats --no-stream

# Vérifier les logs d'erreur
docker-compose logs | grep -i error

# Analyser les métriques
./scripts/performance-check.sh
```

## 📞 Support Déploiement

Pour assistance sur le déploiement :
- **Documentation** : Ce guide complet
- **Scripts** : Outils dans `scripts/`
- **Monitoring** : Dashboards et alertes
- **Support** : Équipe DevOps

---

*Guide de déploiement complet pour environnements de production. Version 2.0*