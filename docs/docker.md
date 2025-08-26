# 🐳 Guide Docker - Tchad Petroleum Application

Ce guide explique comment containeriser et déployer l'application Tchad Petroleum avec Docker.

## 📋 Prérequis

- Docker Desktop installé
- Docker Compose installé
- 4GB de RAM disponible minimum
- Port 8501 libre

## 🚀 Démarrage Rapide

### Option 1: Script de déploiement (Recommandé)

```bash
# Construire et démarrer l'application
./deploy.sh build
./deploy.sh start

# Accéder à l'application
open http://localhost:8501
```

### Option 2: Docker Compose manuel

```bash
# Construire l'image
docker-compose build

# Démarrer l'application
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

### Option 3: Docker classique

```bash
# Construire l'image
docker build -t tchad-petroleum .

# Lancer le conteneur
docker run -d -p 8501:8501 --name tchad-petroleum-app tchad-petroleum
```

## 📁 Structure des Fichiers Docker

```
├── Dockerfile              # Configuration de l'image
├── .dockerignore           # Fichiers à exclure
├── docker-compose.yml      # Orchestration des services
└── deploy.sh              # Script de déploiement
```

## 🔧 Configuration

### Variables d'Environnement

| Variable | Valeur par défaut | Description |
|----------|-------------------|-------------|
| `STREAMLIT_SERVER_PORT` | 8501 | Port d'écoute |
| `STREAMLIT_SERVER_ADDRESS` | 0.0.0.0 | Adresse d'écoute |
| `STREAMLIT_SERVER_HEADLESS` | true | Mode sans interface |
| `STREAMLIT_BROWSER_GATHER_USAGE_STATS` | false | Collecte de stats |

### Volumes

- `./data:/app/data:ro` - Données en lecture seule
- `./logs:/app/logs` - Logs de l'application

## 📊 Monitoring et Logs

### Voir les logs en temps réel
```bash
./deploy.sh logs
# ou
docker-compose logs -f
```

### Vérifier le statut
```bash
./deploy.sh status
# ou
docker-compose ps
```

### Health Check
L'application inclut un health check automatique :
- URL: `http://localhost:8501/_stcore/health`
- Intervalle: 30 secondes
- Timeout: 10 secondes
- Retries: 3

## 🛠️ Commandes Utiles

### Script de déploiement
```bash
./deploy.sh build     # Construire l'image
./deploy.sh start     # Démarrer l'application
./deploy.sh stop      # Arrêter l'application
./deploy.sh restart   # Redémarrer
./deploy.sh logs      # Voir les logs
./deploy.sh status    # Statut des conteneurs
./deploy.sh clean     # Nettoyer les ressources
./deploy.sh help      # Aide
```

### Docker Compose
```bash
docker-compose up -d           # Démarrer en arrière-plan
docker-compose down            # Arrêter et supprimer
docker-compose down -v         # Arrêter et supprimer les volumes
docker-compose build --no-cache # Reconstruire sans cache
docker-compose exec streamlit-app bash # Accéder au conteneur
```

### Docker classique
```bash
docker ps                      # Lister les conteneurs
docker logs tchad-petroleum-app # Voir les logs
docker exec -it tchad-petroleum-app bash # Accéder au conteneur
docker stop tchad-petroleum-app # Arrêter
docker rm tchad-petroleum-app   # Supprimer
```

## 🔒 Sécurité

### Utilisateur non-root
L'application s'exécute avec un utilisateur non-root (`streamlit:1000`) pour la sécurité.

### Données sensibles
- Les fichiers de données sont montés en lecture seule
- Les secrets ne sont pas inclus dans l'image
- Le `.dockerignore` exclut les fichiers sensibles

## 🚀 Déploiement en Production

### Recommandations

1. **Reverse Proxy** : Utiliser nginx ou traefik
2. **HTTPS** : Configurer SSL/TLS
3. **Monitoring** : Ajouter Prometheus/Grafana
4. **Backup** : Sauvegarder les volumes de données
5. **Scaling** : Utiliser Docker Swarm ou Kubernetes

### Exemple avec nginx
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - streamlit-app
```

## 🐛 Dépannage

### Problèmes courants

**Port déjà utilisé**
```bash
# Changer le port dans docker-compose.yml
ports:
  - "8502:8501"  # Utiliser 8502 au lieu de 8501
```

**Problème de permissions**
```bash
# Vérifier les permissions des volumes
ls -la data/
chmod 755 data/
```

**Mémoire insuffisante**
```bash
# Augmenter la mémoire Docker Desktop
# Settings > Resources > Memory > 4GB+
```

**Logs de debug**
```bash
# Logs détaillés
docker-compose logs --tail=100 streamlit-app

# Accéder au conteneur
docker-compose exec streamlit-app bash
```

## 📈 Performance

### Optimisations

1. **Multi-stage build** : Réduire la taille de l'image
2. **Cache layers** : Optimiser l'ordre des instructions
3. **Health checks** : Monitoring automatique
4. **Resource limits** : Limiter CPU/mémoire

### Exemple de limites
```yaml
services:
  streamlit-app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## 🔄 Mise à jour

```bash
# Arrêter l'application
./deploy.sh stop

# Reconstruire avec les dernières modifications
./deploy.sh build

# Redémarrer
./deploy.sh start
```

## 📞 Support

Pour toute question ou problème :
1. Vérifier les logs : `./deploy.sh logs`
2. Consulter le statut : `./deploy.sh status`
3. Nettoyer et redémarrer : `./deploy.sh clean && ./deploy.sh build && ./deploy.sh start`