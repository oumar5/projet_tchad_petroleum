# Architecture du Système de Modélisation Prédictive

## Vue d'ensemble

Le système de modélisation prédictive de Tchad Petroleum Company est conçu avec une architecture modulaire permettant l'utilisation de multiples algorithmes de machine learning pour différents cas d'usage.

## Structure du Projet

```
projet_tchad_petroleum/
├── app.py                          # Application principale Streamlit
├── requirements.txt                # Dépendances Python
├── README.md                      # Documentation utilisateur
├── data/
│   └── Données de production Rev.xlsx  # Données Excel
├── pages/
│   ├── 1_📈_Analyse_de_Production.py   # Page d'analyse de production
│   ├── 2_🔧_Analyse_des_Pannes.py      # Page d'analyse des pannes
│   └── 3_🔮_Modélisation_Prédictive.py # Page de modélisation prédictive
├── src/
│   ├── __init__.py
│   ├── data_loader.py              # Chargement et préparation des données
│   ├── plotting.py                 # Fonctions de visualisation
│   └── models/                     # Package des modèles ML
│       ├── __init__.py
│       ├── base_model.py           # Classe de base abstraite
│       ├── classical_models.py     # Modèles classiques (RF, GB)
│       ├── prophet_models.py       # Modèles Prophet/NeuralProphet
│       ├── xgboost_models.py       # Modèles XGBoost
│       ├── model_factory.py        # Factory pour création de modèles
│       └── model_evaluator.py      # Évaluation centralisée
└── docs/
    ├── architecture.md             # Ce document
    ├── models.md                   # Documentation des modèles
    ├── api.md                      # Documentation API
    └── deployment.md               # Guide de déploiement
```

## Composants Principaux

### 1. Classe de Base (BaseModel)

**Fichier**: `src/models/base_model.py`

Classe abstraite définissant l'interface commune pour tous les modèles :

- **Méthodes abstraites** :
  - `prepare_data()` : Préparation des données
  - `train()` : Entraînement du modèle
  - `predict()` : Prédictions

- **Méthodes communes** :
  - `evaluate_classification()` : Évaluation pour classification
  - `evaluate_regression()` : Évaluation pour régression
  - `evaluate_timeseries()` : Évaluation pour séries temporelles
  - `get_feature_importance()` : Importance des features
  - `save_model()` / `load_model()` : Sauvegarde/chargement

### 2. Modèles Classiques

**Fichier**: `src/models/classical_models.py`

Implémentation des algorithmes traditionnels :

- **Random Forest** (Classification/Régression)
- **Gradient Boosting** (Classification/Régression)
- **Régression Linéaire/Logistique**

**Classes spécialisées** :
- `MaintenancePredictiveModel` : Maintenance prédictive
- `ProductionForecastModel` : Prévision de production
- `WaterInjectionOptimizer` : Optimisation injection d'eau

### 3. Modèles Prophet

**Fichier**: `src/models/prophet_models.py`

Modèles spécialisés pour les séries temporelles :

- **Prophet** : Modèle de Facebook pour séries temporelles
- **NeuralProphet** : Version neuronale de Prophet

**Fonctionnalités** :
- Détection automatique de saisonnalité
- Gestion des jours fériés
- Détection d'anomalies
- Validation croisée temporelle

### 4. Modèles XGBoost

**Fichier**: `src/models/xgboost_models.py`

Implémentation XGBoost avec optimisations avancées :

- **XGBClassifier** : Classification
- **XGBRegressor** : Régression
- **Early Stopping** : Arrêt précoce
- **Hyperparameter Tuning** : Optimisation automatique
- **SHAP Integration** : Explainabilité

### 5. Factory de Modèles

**Fichier**: `src/models/model_factory.py`

Gestion centralisée de la création de modèles :

- **Registre des modèles** : Catalogue complet
- **Création automatique** : Factory pattern
- **Recommandations** : Suggestions basées sur le contexte
- **Ensembles** : Combinaison de modèles
- **Vérification des dépendances** : Contrôle de disponibilité

### 6. Évaluateur de Modèles

**Fichier**: `src/models/model_evaluator.py`

Évaluation et visualisation centralisées :

- **Métriques complètes** : Classification, régression, séries temporelles
- **Visualisations** : Matrices de confusion, courbes ROC, etc.
- **Comparaisons** : Benchmarking entre modèles
- **Rapports** : Génération automatique de rapports
- **Export** : Sauvegarde des résultats

## Flux de Données

### 1. Chargement des Données

```python
# data_loader.py
production_df = load_production_data()
failures_df = load_pump_failures_data()

# Validation temporelle
train_data, val_data = split_data_for_validation(production_df, validation_years=2)
```

### 2. Création de Modèles

```python
# model_factory.py
model = ModelFactory.create_model(
    use_case='maintenance_predictive',
    algorithm='xgboost'
)
```

### 3. Entraînement

```python
# Préparation des données
X, y = model.prepare_data(train_data, target_col='Failure_Next_Days')

# Entraînement
results = model.train(X, y, test_size=0.2, optimize_hyperparameters=True)
```

### 4. Évaluation

```python
# model_evaluator.py
evaluator = ModelEvaluator()
metrics = evaluator.evaluate_model(model, X_test, y_test, 'XGBoost_Maintenance')

# Visualisations
fig_cm = evaluator.plot_confusion_matrix('XGBoost_Maintenance')
fig_roc = evaluator.plot_roc_curve(['XGBoost_Maintenance'])
```

## Cas d'Usage Supportés

### 1. Maintenance Prédictive

**Objectif** : Prédire les pannes de pompes

**Algorithmes disponibles** :
- Random Forest Classification
- Gradient Boosting Classification
- XGBoost Classification

**Features** :
- Moyennes mobiles de production
- Tendances de watercut
- Historique des pannes
- Features cycliques (jour, mois)

### 2. Prévision de Production

**Objectif** : Prédire la production d'huile future

**Algorithmes disponibles** :
- Random Forest Regression
- Gradient Boosting Regression
- XGBoost Regression
- Prophet
- NeuralProphet

**Features** :
- Séries temporelles avec lags
- Saisonnalité
- Tendances
- Variables exogènes

### 3. Optimisation Injection d'Eau

**Objectif** : Optimiser les paramètres d'injection

**Algorithmes disponibles** :
- Random Forest Regression
- Gradient Boosting Regression
- XGBoost Regression

**Features** :
- Ratios huile/eau
- Efficacité d'injection
- Corrélations production-injection

## Extensibilité

### Ajout d'un Nouveau Modèle

1. **Hériter de BaseModel** :
```python
class MonNouveauModele(BaseModel):
    def __init__(self):
        super().__init__("mon_modele", "classification")
    
    def prepare_data(self, df, target_col, **kwargs):
        # Implémentation spécifique
        pass
    
    def train(self, X, y, **kwargs):
        # Implémentation spécifique
        pass
    
    def predict(self, X):
        # Implémentation spécifique
        pass
```

2. **Enregistrer dans la Factory** :
```python
# model_factory.py
AVAILABLE_MODELS['mon_cas_usage']['mon_algorithme'] = {
    'class': MonNouveauModele,
    'params': {},
    'description': 'Description du modèle',
    'type': 'classification',
    'category': 'custom'
}
```

### Ajout d'une Nouvelle Métrique

```python
# model_evaluator.py
def _evaluate_custom(self, y_true, y_pred, model_name):
    metrics = {
        'ma_metrique_custom': calculate_custom_metric(y_true, y_pred)
    }
    return metrics
```

## Bonnes Pratiques

### 1. Gestion des Erreurs

- **Validation des entrées** : Vérification systématique
- **Gestion des dépendances manquantes** : Messages d'erreur clairs
- **Fallback** : Solutions de repli

### 2. Performance

- **Cache Streamlit** : `@st.cache_data` pour les données
- **Lazy Loading** : Chargement à la demande
- **Optimisation mémoire** : Nettoyage des variables

### 3. Maintenabilité

- **Documentation** : Docstrings complètes
- **Tests unitaires** : Couverture des fonctions critiques
- **Logging** : Traçabilité des opérations

### 4. Sécurité

- **Validation des données** : Contrôle des entrées
- **Isolation des modèles** : Sandboxing
- **Gestion des secrets** : Variables d'environnement

## Déploiement

Voir `docs/deployment.md` pour les instructions détaillées de déploiement en production.

## Monitoring

### Métriques à Surveiller

- **Performance des modèles** : Accuracy, RMSE, etc.
- **Dérive des données** : Distribution des features
- **Temps de réponse** : Latence des prédictions
- **Utilisation des ressources** : CPU, mémoire

### Alertes

- **Dégradation des performances** : Seuils d'alerte
- **Erreurs système** : Notifications automatiques
- **Anomalies dans les données** : Détection automatique

## Évolutions Futures

### Court Terme

- **Deep Learning** : Réseaux de neurones
- **AutoML** : Optimisation automatique
- **API REST** : Interface programmatique

### Long Terme

- **MLOps** : Pipeline CI/CD pour ML
- **Edge Computing** : Déploiement sur site
- **Federated Learning** : Apprentissage distribué