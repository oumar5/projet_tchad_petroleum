# 👨‍💻 Guide de Développement

## Vue d'Ensemble

Ce document détaille l'environnement de développement, les standards de code, et les processus de contribution pour le projet de digitalisation de Tchad Petroleum Company.

## 🎯 Objectifs du Guide

- **Setup** : Configuration rapide de l'environnement
- **Standards** : Conventions de code et bonnes pratiques
- **Workflow** : Processus de développement et contribution
- **Testing** : Stratégies de test et validation
- **Collaboration** : Outils et méthodes de travail en équipe

## 🛠️ Configuration de l'Environnement

### Prérequis Système

#### 💻 Logiciels Requis
- **Python 3.11+** : Langage principal
- **Git** : Contrôle de version
- **Docker** : Containerisation (optionnel)
- **VS Code** : IDE recommandé
- **Node.js** : Pour outils de développement (optionnel)

#### 🔧 Vérification des Prérequis
```bash
# Vérifier Python
python --version  # Doit être >= 3.11

# Vérifier Git
git --version

# Vérifier Docker (optionnel)
docker --version
docker-compose --version
```

### Installation Locale

#### 1️⃣ Clonage du Projet
```bash
# Cloner le repository
git clone <repository-url>
cd projet_tchad_petroleum

# Vérifier la structure
ls -la
```

#### 2️⃣ Environnement Virtuel
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur macOS/Linux:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Vérifier l'activation
which python  # Doit pointer vers venv/bin/python
```

#### 3️⃣ Installation des Dépendances
```bash
# Installer les dépendances principales
pip install --upgrade pip
pip install -r requirements.txt

# Installer les dépendances de développement
pip install -r requirements-dev.txt  # Si disponible

# Ou installer manuellement les outils de dev
pip install pytest black flake8 mypy jupyter
```

#### 4️⃣ Configuration des Données
```bash
# Créer le dossier data s'il n'existe pas
mkdir -p data

# Copier les fichiers de données
# Placer 'Données de production Rev.xlsx' dans data/

# Vérifier la structure des données
ls -la data/
```

#### 5️⃣ Test de l'Installation
```bash
# Tester l'application
streamlit run app.py

# Vérifier dans le navigateur
# http://localhost:8501
```

### Configuration Docker

#### 🐳 Setup Docker (Recommandé)
```bash
# Construction de l'image
docker-compose build

# Démarrage des services
docker-compose up -d

# Vérification des logs
docker-compose logs -f streamlit-app

# Accès à l'application
# http://localhost:8501
```

#### 🔧 Développement avec Docker
```bash
# Mode développement avec hot reload
docker-compose -f docker-compose.dev.yml up

# Accès au conteneur pour debugging
docker-compose exec streamlit-app bash

# Arrêt des services
docker-compose down
```

## 📁 Structure du Projet

### Architecture des Dossiers

```
projet_tchad_petroleum/
├── 📱 app.py                    # Point d'entrée Streamlit
├── 📋 requirements.txt          # Dépendances Python
├── 🐳 docker-compose.yml       # Configuration Docker
├── 📊 data/                     # Données (non versionnées)
│   └── Données de production Rev.xlsx
├── 📚 docs/                     # Documentation
│   ├── development.md           # Ce guide
│   ├── deployment.md            # Guide déploiement
│   └── ...
├── 🧪 tests/                    # Tests unitaires
│   ├── test_models.py
│   ├── test_data_loader.py
│   └── ...
└── 🔧 src/                      # Code source principal
    ├── 📥 data_loader.py        # Chargement des données
    ├── 🤖 models/               # Modèles ML
    │   ├── base_model.py
    │   ├── classical_models.py
    │   ├── prophet_models.py
    │   └── ...
    ├── 📊 plotting/             # Visualisations
    │   ├── basic_plots.py
    │   ├── model_plots.py
    │   └── ...
    └── 🖥️ ui_components/        # Interface utilisateur
        ├── home_ui.py
        ├── maintenance_ui.py
        └── ...
```

### Conventions de Nommage

#### 📂 Fichiers et Dossiers
- **Modules Python** : `snake_case.py`
- **Classes** : `PascalCase`
- **Fonctions** : `snake_case()`
- **Constantes** : `UPPER_SNAKE_CASE`
- **Dossiers** : `snake_case/`

#### 🏷️ Variables et Fonctions
```python
# ✅ Bonnes pratiques
class ModelEvaluator:           # PascalCase pour classes
    def calculate_metrics(self): # snake_case pour méthodes
        pass

DATA_PATH = './data/'          # UPPER_SNAKE_CASE pour constantes
production_df = load_data()    # snake_case pour variables

# ❌ À éviter
class modelEvaluator:          # Mauvais casing
    def CalculateMetrics(self): # Mauvais casing
        pass

dataPath = './data/'           # Mauvais style
```

## 📝 Standards de Code

### Style de Code Python

#### 🎨 Formatage avec Black
```bash
# Installation
pip install black

# Formatage automatique
black src/ tests/

# Vérification sans modification
black --check src/

# Configuration dans pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
```

#### 🔍 Linting avec Flake8
```bash
# Installation
pip install flake8

# Vérification du code
flake8 src/ tests/

# Configuration dans .flake8
[flake8]
max-line-length = 88
ignore = E203, W503
exclude = venv/, __pycache__/
```

#### 🏷️ Type Hints avec MyPy
```bash
# Installation
pip install mypy

# Vérification des types
mypy src/

# Configuration dans mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
```

### Documentation du Code

#### 📚 Docstrings
```python
def calculate_production_metrics(df: pd.DataFrame, target_col: str) -> Dict[str, float]:
    """
    Calcule les métriques de production à partir des données.
    
    Args:
        df: DataFrame contenant les données de production
        target_col: Nom de la colonne cible à analyser
        
    Returns:
        Dictionnaire contenant les métriques calculées:
        - mean: Moyenne de production
        - std: Écart-type
        - min/max: Valeurs extrêmes
        
    Raises:
        ValueError: Si la colonne cible n'existe pas
        
    Example:
        >>> df = pd.DataFrame({'production': [100, 200, 150]})
        >>> metrics = calculate_production_metrics(df, 'production')
        >>> metrics['mean']
        150.0
    """
    if target_col not in df.columns:
        raise ValueError(f"Colonne '{target_col}' non trouvée")
    
    return {
        'mean': df[target_col].mean(),
        'std': df[target_col].std(),
        'min': df[target_col].min(),
        'max': df[target_col].max()
    }
```

#### 📝 Commentaires
```python
# ✅ Bons commentaires
class ModelTrainer:
    def __init__(self):
        # Cache pour éviter le recalcul des métriques
        self._metrics_cache = {}
        
    def train_model(self, X, y):
        # Division stratifiée pour maintenir la distribution des classes
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, stratify=y, test_size=0.2
        )
        
        # TODO: Implémenter la validation croisée
        # FIXME: Gérer le cas où y contient des NaN
        
# ❌ Commentaires inutiles
def add_numbers(a, b):
    # Additionne a et b
    return a + b  # Retourne la somme
```

## 🧪 Tests et Validation

### Structure des Tests

```
tests/
├── __init__.py
├── conftest.py                 # Configuration pytest
├── test_data_loader.py         # Tests chargement données
├── test_models.py              # Tests modèles ML
├── test_ui_components.py       # Tests interface
├── test_all_models_complete.py # Tests d'intégration
└── fixtures/                   # Données de test
    ├── sample_production.csv
    └── sample_failures.csv
```

### Tests Unitaires avec Pytest

#### 🧪 Configuration Pytest
```python
# conftest.py
import pytest
import pandas as pd
import numpy as np
from src.models.model_factory import ModelFactory

@pytest.fixture
def sample_production_data():
    """Données de production pour les tests."""
    return pd.DataFrame({
        'Date': pd.date_range('2023-01-01', periods=100),
        'Production journaliere d\'huile bbl': np.random.normal(1000, 100, 100),
        'Teneur en eau (Watercut)': np.random.uniform(20, 80, 100)
    })

@pytest.fixture
def trained_model():
    """Modèle pré-entraîné pour les tests."""
    model = ModelFactory.create_model('production_forecast', 'random_forest')
    # Configuration minimale pour tests
    return model
```

#### 🧪 Exemples de Tests
```python
# test_data_loader.py
import pytest
from src.data_loader import load_production_data, calculate_production_kpis

class TestDataLoader:
    def test_load_production_data_structure(self, sample_production_data):
        """Test de la structure des données chargées."""
        df = sample_production_data
        
        # Vérifications de base
        assert not df.empty
        assert 'Date' in df.columns
        assert 'Production journaliere d\'huile bbl' in df.columns
        
        # Vérifications des types
        assert pd.api.types.is_datetime64_any_dtype(df['Date'])
        assert pd.api.types.is_numeric_dtype(df['Production journaliere d\'huile bbl'])
    
    def test_calculate_kpis(self, sample_production_data):
        """Test du calcul des KPIs."""
        kpis = calculate_production_kpis(sample_production_data)
        
        # Vérifications des KPIs
        assert 'production_totale' in kpis
        assert 'production_moyenne' in kpis
        assert kpis['production_totale'] > 0
        assert kpis['production_moyenne'] > 0
    
    def test_empty_dataframe_handling(self):
        """Test de gestion des DataFrames vides."""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="DataFrame vide"):
            calculate_production_kpis(empty_df)

# test_models.py
from src.models.classical_models import ClassicalModels
from sklearn.datasets import make_classification

class TestClassicalModels:
    def test_model_initialization(self):
        """Test d'initialisation des modèles."""
        model = ClassicalModels('random_forest', 'classification')
        
        assert model.algorithm == 'random_forest'
        assert model.model_type == 'classification'
        assert not model.is_trained
    
    def test_model_training(self):
        """Test d'entraînement des modèles."""
        # Données de test
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
        y_series = pd.Series(y)
        
        # Entraînement
        model = ClassicalModels('random_forest', 'classification')
        results = model.train(X_df, y_series)
        
        # Vérifications
        assert model.is_trained
        assert 'training_metrics' in results
        assert 'validation_metrics' in results
        assert results['training_metrics']['accuracy'] > 0.5
    
    def test_model_prediction(self):
        """Test de prédiction des modèles."""
        # Entraînement préalable
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
        y_series = pd.Series(y)
        
        model = ClassicalModels('random_forest', 'classification')
        model.train(X_df, y_series)
        
        # Prédiction
        predictions = model.predict(X_df.head(5))
        
        # Vérifications
        assert len(predictions) == 5
        assert all(pred in [0, 1] for pred in predictions)
```

#### 🧪 Exécution des Tests
```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_models.py

# Tests avec couverture
pytest --cov=src tests/

# Tests avec rapport HTML
pytest --cov=src --cov-report=html tests/

# Tests en mode verbose
pytest -v tests/

# Tests avec marqueurs
pytest -m "not slow" tests/
```

### Tests d'Intégration

```python
# test_integration.py
class TestIntegration:
    def test_full_pipeline(self, sample_production_data):
        """Test du pipeline complet."""
        # 1. Chargement des données
        df = sample_production_data
        
        # 2. Création du modèle
        model = ModelFactory.create_model('production_forecast', 'random_forest')
        
        # 3. Préparation des données
        X, y = model.prepare_data(df, 'Production journaliere d\'huile bbl')
        
        # 4. Entraînement
        results = model.train(X, y)
        
        # 5. Prédiction
        predictions = model.predict(X.head(10))
        
        # Vérifications end-to-end
        assert len(predictions) == 10
        assert all(isinstance(p, (int, float)) for p in predictions)
        assert results['validation_metrics']['r2'] > 0
```

## 🔄 Workflow de Développement

### Git Workflow

#### 🌿 Stratégie de Branches
```bash
# Structure des branches
main/master     # Production stable
├── develop     # Intégration continue
├── feature/*   # Nouvelles fonctionnalités
├── bugfix/*    # Corrections de bugs
└── hotfix/*    # Corrections urgentes
```

#### 🔄 Processus de Développement
```bash
# 1. Créer une branche feature
git checkout develop
git pull origin develop
git checkout -b feature/maintenance-prediction-ui

# 2. Développement avec commits atomiques
git add src/ui_components/maintenance_ui.py
git commit -m "feat: add maintenance prediction interface

- Add MaintenanceUI class with algorithm selection
- Implement model training workflow
- Add results visualization components

Closes #123"

# 3. Push et Pull Request
git push origin feature/maintenance-prediction-ui
# Créer PR via interface GitHub/GitLab

# 4. Après review et merge
git checkout develop
git pull origin develop
git branch -d feature/maintenance-prediction-ui
```

#### 📝 Convention de Commits
```bash
# Format: type(scope): description
#
# [optional body]
#
# [optional footer]

# Types:
feat:     # Nouvelle fonctionnalité
fix:      # Correction de bug
docs:     # Documentation
style:    # Formatage, pas de changement de code
refactor: # Refactoring sans changement de fonctionnalité
test:     # Ajout ou modification de tests
chore:    # Maintenance, outils, configuration

# Exemples:
feat(models): add XGBoost support for classification
fix(ui): resolve data loading error in dashboard
docs(api): update model training documentation
test(data): add unit tests for data validation
```

### Code Review

#### ✅ Checklist de Review
- [ ] **Fonctionnalité** : Le code fait ce qui est attendu
- [ ] **Tests** : Tests unitaires et d'intégration présents
- [ ] **Documentation** : Docstrings et commentaires appropriés
- [ ] **Style** : Respect des conventions de code
- [ ] **Performance** : Pas de régression de performance
- [ ] **Sécurité** : Pas de vulnérabilités introduites
- [ ] **Compatibilité** : Fonctionne avec les versions supportées

#### 🔍 Processus de Review
1. **Auto-review** : Vérifier sa propre PR avant soumission
2. **Tests automatiques** : CI/CD doit passer
3. **Review par les pairs** : Au moins 1 approbation
4. **Tests manuels** : Vérification fonctionnelle si nécessaire
5. **Merge** : Squash and merge recommandé

## 🚀 Outils de Développement

### IDE Configuration (VS Code)

#### 📦 Extensions Recommandées
```json
// .vscode/extensions.json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-python.mypy-type-checker",
        "ms-toolsai.jupyter",
        "ms-vscode.docker",
        "redhat.vscode-yaml",
        "yzhang.markdown-all-in-one"
    ]
}
```

#### ⚙️ Configuration VS Code
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/venv": true
    },
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### 🐛 Configuration de Debug
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Streamlit App",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": ["run", "app.py"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Python Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

### Pre-commit Hooks

#### 🪝 Configuration Pre-commit
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

#### 🔧 Installation et Usage
```bash
# Installation
pip install pre-commit

# Installation des hooks
pre-commit install

# Test manuel
pre-commit run --all-files

# Les hooks s'exécutent automatiquement à chaque commit
```

## 📊 Monitoring et Debugging

### Logging

#### 📝 Configuration du Logging
```python
# src/utils/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = None):
    """Configure le système de logging."""
    
    # Format des logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Handler fichier (optionnel)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configuration root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return logging.getLogger(__name__)

# Usage dans les modules
logger = logging.getLogger(__name__)

def train_model(X, y):
    logger.info(f"Début entraînement avec {len(X)} échantillons")
    try:
        # Entraînement
        model.fit(X, y)
        logger.info("Entraînement terminé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement: {e}")
        raise
```

### Profiling et Performance

#### ⚡ Profiling avec cProfile
```python
# Profiling d'une fonction
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    """Profile une fonction et affiche les résultats."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10
    
    return result

# Usage
result = profile_function(model.train, X_train, y_train)
```

#### 📊 Monitoring Streamlit
```python
# Monitoring des performances Streamlit
import time
import streamlit as st

def monitor_performance(func):
    """Décorateur pour monitorer les performances."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if execution_time > 2.0:  # Seuil d'alerte
            st.warning(f"⚠️ Opération lente: {execution_time:.2f}s")
        
        return result
    return wrapper

@monitor_performance
def load_and_process_data():
    # Opération potentiellement lente
    return process_large_dataset()
```

## 🤝 Contribution

### Processus de Contribution

#### 1️⃣ Préparation
- Fork du repository
- Clone en local
- Configuration de l'environnement
- Lecture de la documentation

#### 2️⃣ Développement
- Création d'une branche feature
- Développement avec tests
- Commits atomiques et descriptifs
- Respect des standards de code

#### 3️⃣ Soumission
- Push de la branche
- Création d'une Pull Request
- Description détaillée des changements
- Tests automatiques passants

#### 4️⃣ Review et Merge
- Review par les mainteneurs
- Corrections si nécessaires
- Merge après approbation
- Nettoyage des branches

### Guidelines de Contribution

#### ✅ Bonnes Pratiques
- **Tests** : Toujours ajouter des tests pour le nouveau code
- **Documentation** : Mettre à jour la documentation si nécessaire
- **Backward compatibility** : Maintenir la compatibilité
- **Performance** : Considérer l'impact sur les performances
- **Sécurité** : Pas de secrets ou données sensibles

#### 📝 Template de Pull Request
```markdown
## Description
Brève description des changements apportés.

## Type de changement
- [ ] Bug fix (changement non-breaking qui corrige un problème)
- [ ] Nouvelle fonctionnalité (changement non-breaking qui ajoute une fonctionnalité)
- [ ] Breaking change (correction ou fonctionnalité qui casserait la fonctionnalité existante)
- [ ] Documentation (changements de documentation uniquement)

## Tests
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Tests d'intégration ajoutés/mis à jour
- [ ] Tests manuels effectués

## Checklist
- [ ] Mon code suit les standards du projet
- [ ] J'ai effectué une auto-review de mon code
- [ ] J'ai commenté mon code, particulièrement dans les zones difficiles
- [ ] J'ai mis à jour la documentation correspondante
- [ ] Mes changements ne génèrent pas de nouveaux warnings
- [ ] J'ai ajouté des tests qui prouvent que ma correction est efficace ou que ma fonctionnalité fonctionne
- [ ] Les tests unitaires nouveaux et existants passent localement

## Screenshots (si applicable)
[Ajouter des captures d'écran pour les changements UI]

## Notes supplémentaires
[Toute information supplémentaire pour les reviewers]
```

## 🔍 Dépannage Développement

### Problèmes Courants

#### 🚨 "Module not found"
```bash
# Vérifier l'environnement virtuel
which python
pip list

# Réinstaller les dépendances
pip install -r requirements.txt

# Vérifier PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 🚨 "Tests échouent localement"
```bash
# Nettoyer le cache pytest
pytest --cache-clear

# Vérifier les fixtures
pytest --fixtures

# Mode verbose pour plus d'infos
pytest -v -s tests/
```

#### 🚨 "Docker ne démarre pas"
```bash
# Vérifier les logs
docker-compose logs

# Reconstruire l'image
docker-compose build --no-cache

# Nettoyer les volumes
docker-compose down -v
```

### Ressources d'Aide

#### 📚 Documentation
- **Code source** : Commentaires et docstrings
- **Tests** : Exemples d'usage dans `tests/`
- **Documentation** : Guides dans `docs/`

#### 🤝 Support
- **Issues GitHub** : Signaler bugs et demandes
- **Discussions** : Questions et suggestions
- **Code Review** : Feedback sur les PRs
- **Équipe** : Contact direct si nécessaire

## 📞 Support Développement

Pour assistance sur le développement :
- **Documentation** : Ce guide et autres docs
- **Code source** : Exemples dans le projet
- **Tests** : Patterns dans `tests/`
- **Équipe** : Contact développeurs seniors

---

*Guide de développement complet pour contributeurs. Version 2.0*