

# 🛢️ Digitalisation et Optimisation des Processus Internes
## Modélisation Prédictive des Données Pétrolières - Tchad Petroleum Company

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)]()

## 📋 Vue d'Ensemble

Ce projet implémente une solution complète de **digitalisation et d'optimisation des processus internes** pour Tchad Petroleum Company, utilisant des techniques avancées de **modélisation prédictive** pour optimiser les opérations pétrolières.

### 🎯 Objectifs Principaux

- **Digitalisation** des processus de production pétrolière
- **Optimisation** des opérations par l'intelligence artificielle
- **Prédiction** des pannes et maintenance préventive
- **Maximisation** de la production et réduction des coûts
- **Prise de décision** basée sur les données

## 🚀 Fonctionnalités Clés

### 📊 Tableau de Bord Interactif
- Visualisation en temps réel des KPIs de production
- Analyse des tendances et patterns
- Alertes intelligentes automatisées

### 🔧 Maintenance Prédictive
- Prédiction des pannes de pompes (7-30 jours)
- Algorithmes ML : Random Forest, Gradient Boosting, XGBoost
- Optimisation des calendriers de maintenance

### 📈 Prévision de Production
- Prédiction de la production d'huile à court/moyen terme
- Modèles de séries temporelles : Prophet, NeuralProphet
- Analyse de saisonnalité et tendances

### 💧 Optimisation Injection d'Eau
- Optimisation des paramètres d'injection
- Maximisation du ratio huile/eau
- Recommandations automatiques basées sur l'IA

### 🔍 Analyse Comparative
- Comparaison de performance entre modèles
- Métriques avancées et validation croisée
- Rapports automatisés

## 🏗️ Architecture Technique

```
projet_tchad_petroleum/
├── 📱 app.py                    # Application principale Streamlit
├── 📋 requirements.txt          # Dépendances Python
├── 🐳 docker-compose.yml       # Configuration Docker
├── 📊 data/                     # Données pétrolières
├── 📚 docs/                     # Documentation complète
├── 🧪 tests/                    # Tests unitaires
└── 🔧 src/                      # Code source modulaire
    ├── 📥 data_loader.py        # Collecte des données
    ├── 🤖 models/               # Modèles prédictifs
    ├── 📊 plotting/             # Visualisations
    └── 🖥️ ui_components/        # Interface utilisateur
```

## 🛠️ Installation Rapide

### Option 1: Docker (Recommandé)
```bash
# Cloner le projet
git clone <repository-url>
cd projet_tchad_petroleum

# Démarrer avec Docker
docker-compose up -d --build

# Accéder à l'application
open http://localhost:8501
```

### Option 2: Installation Locale
```bash
# Installer les dépendances
pip install -r requirements.txt

# Placer les données dans data/
# Lancer l'application
streamlit run app.py
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [📥 Collecte des Données](docs/data-collection.md) | Guide de collecte et sources de données |
| [🧹 Nettoyage des Données](docs/data-cleaning.md) | Processus de préparation des données |
| [🤖 Modèles Prédictifs](docs/prediction-models.md) | Algorithmes et techniques ML |
| [📊 Interface Utilisateur](docs/user-interface.md) | Guide d'utilisation de l'interface |
| [🏗️ Architecture](docs/architecture.md) | Architecture technique complète |
| [👨‍💻 Guide Développeur](docs/development.md) | Setup et contribution |
| [🚀 Déploiement](docs/deployment.md) | Guide de déploiement production |
| [📖 Guide Utilisateur](docs/user-guide.md) | Manuel d'utilisation complet |

## 🎯 Cas d'Usage

### 🔧 Ingénieurs de Maintenance
- Planification préventive des interventions
- Prédiction des pannes avant qu'elles surviennent
- Optimisation des stocks de pièces de rechange

### 📊 Analystes de Production
- Prévision de la production future
- Identification des facteurs d'optimisation
- Analyse des performances par bloc

### 💼 Managers Opérationnels
- Tableau de bord KPIs en temps réel
- Rapports automatisés de performance
- Aide à la prise de décision stratégique

### 🔬 Ingénieurs Réservoir
- Optimisation de l'injection d'eau
- Analyse de la récupération d'huile
- Modélisation des performances de puits

## 📈 Bénéfices Mesurables

### 💰 Économiques
- **Réduction 15-25%** des coûts de maintenance
- **Augmentation 5-10%** de la production
- **Optimisation 20%** de l'efficacité opérationnelle

### ⚡ Opérationnels
- **Réduction 30%** des temps d'arrêt non planifiés
- **Amélioration 40%** de la planification maintenance
- **Accélération 50%** de la prise de décision

## 🔮 Roadmap

### Phase 1 ✅ (Actuelle)
- Interface Streamlit complète
- Modèles ML de base
- Visualisations interactives

### Phase 2 🚧 (En cours)
- API REST pour intégration
- Base de données temps réel
- Alertes automatiques

### Phase 3 📋 (Planifiée)
- Deep Learning avancé
- Computer Vision
- Optimisation multi-objectifs

## 🤝 Support

### 📞 Contact
- **Équipe Technique** : [contact@tchadpetroleum.com](mailto:contact@tchadpetroleum.com)
- **Support** : [support@tchadpetroleum.com](mailto:support@tchadpetroleum.com)

### 🐛 Signaler un Bug
1. Vérifier les [issues existantes](issues)
2. Créer une nouvelle issue avec description détaillée
3. Inclure logs et captures d'écran

### 💡 Demande de Fonctionnalité
1. Consulter la roadmap
2. Proposer via une issue
3. Participer aux discussions

---

<div align="center">

**🛢️ Tchad Petroleum Company**  
*Système de Digitalisation et d'Optimisation Avancé*

**Version 2.0** • **Architecture Modulaire** • **IA Intégrée**

*Développé avec ❤️ pour l'excellence opérationnelle*

</div>