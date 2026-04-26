#!/bin/bash

# Script de déploiement pour l'application Tchad Petroleum
# Usage: ./deploy.sh [build|start|stop|restart|logs|clean]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="tchad-petroleum-app"
IMAGE_NAME="tchad-petroleum"
COMPOSE_FILE="docker-compose.yml"

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
}

# Construire l'image Docker
build() {
    log_info "Construction de l'image Docker..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    log_success "Image construite avec succès!"
}

# Démarrer l'application
start() {
    log_info "Démarrage de l'application..."
    docker-compose -f $COMPOSE_FILE up -d
    log_success "Application démarrée!"
    log_info "Accédez à l'application sur: http://localhost:8501"
}

# Arrêter l'application
stop() {
    log_info "Arrêt de l'application..."
    docker-compose -f $COMPOSE_FILE down
    log_success "Application arrêtée!"
}

# Redémarrer l'application
restart() {
    log_info "Redémarrage de l'application..."
    stop
    start
}

# Afficher les logs
logs() {
    log_info "Affichage des logs..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Nettoyer les ressources Docker
clean() {
    log_warning "Nettoyage des ressources Docker..."
    docker-compose -f $COMPOSE_FILE down -v --remove-orphans
    docker system prune -f
    log_success "Nettoyage terminé!"
}

# Afficher le statut
status() {
    log_info "Statut des conteneurs:"
    docker-compose -f $COMPOSE_FILE ps
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commandes disponibles:"
    echo "  build     Construire l'image Docker"
    echo "  start     Démarrer l'application"
    echo "  stop      Arrêter l'application"
    echo "  restart   Redémarrer l'application"
    echo "  logs      Afficher les logs en temps réel"
    echo "  status    Afficher le statut des conteneurs"
    echo "  clean     Nettoyer les ressources Docker"
    echo "  help      Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 build && $0 start    # Construire et démarrer"
    echo "  $0 logs                 # Voir les logs"
    echo "  $0 clean                # Nettoyer tout"
}

# Script principal
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs
            ;;
        status)
            status
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Exécuter le script principal
main "$@"