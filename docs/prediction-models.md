# 🤖 Guide des Modèles Prédictifs

## Vue d'Ensemble

Ce document détaille l'ensemble des modèles de machine learning utilisés dans le système de modélisation prédictive de Tchad Petroleum Company.

## 🎯 Objectifs de la Modélisation

- **Maintenance Prédictive** : Anticiper les pannes d'équipements
- **Prévision de Production** : Optimiser la planification
- **Optimisation Injection** : Maximiser la récupération d'huile
- **Analyse Comparative** : Évaluer les performances
- **Aide à la Décision** : Support analytique avancé

## 🏗️ Architecture des Modèles

### Structure Modulaire

```
src/models/
├── base_model.py           # Classe abstraite de base
├── model_factory.py        # Factory pour création de modèles
├── model_evaluator.py      # Évaluation et métriques
├── model_utils.py          # Utilitaires communs
├── classical_models.py     # Random Forest, Gradient Boosting
├── xgboost_models.py       # Modèles XGBoost
└── prophet_models.py       # Prophet, NeuralProphet
```

### Hiérarchie des Classes

```python
BaseModel (Abstract)
├── ClassicalModels
│   ├── MaintenancePredictiveModel
│   ├── ProductionForecastModel
│   └── WaterInjectionOptimizer
├── XGBoostModels
│   ├── XGBoostMaintenanceModel
│   └── XGBoostProductionModel
└── ProphetModels
    └── ProductionProphetModel
```

## 🔧 Modèles Classiques

### Random Forest

#### 📊 Caractéristiques
- **Type** : Ensemble d'arbres de décision
- **Avantages** : Robuste, gère les valeurs manquantes
- **Usage** : Classification et régression
- **Hyperparamètres** : n_estimators, max_depth, min_samples_split

#### 🛠️ Implémentation
```python
class ClassicalModels(BaseModel):
    def _get_model(self, **kwargs):
        if self.algorithm == 'random_forest':
            if self.model_type == 'classification':
                return RandomForestClassifier(
                    n_estimators=kwargs.get('n_estimators', 100),
                    max_depth=kwargs.get('max_depth', 10),
                    min_samples_split=kwargs.get('min_samples_split', 5),
                    random_state=42
                )
            else:
                return RandomForestRegressor(
                    n_estimators=kwargs.get('n_estimators', 100),
                    max_depth=kwargs.get('max_depth', 10),
                    random_state=42
                )
```

#### 📈 Cas d'Usage
- **Maintenance Prédictive** : Classification des risques de panne
- **Prévision Production** : Régression pour volumes futurs
- **Feature Importance** : Identification des variables clés

### Gradient Boosting

#### 📊 Caractéristiques
- **Type** : Boosting séquentiel
- **Avantages** : Haute précision, gestion des non-linéarités
- **Usage** : Problèmes complexes de régression
- **Hyperparamètres** : learning_rate, n_estimators, max_depth

#### 🛠️ Configuration
```python
if self.algorithm == 'gradient_boosting':
    if self.model_type == 'classification':
        return GradientBoostingClassifier(
            n_estimators=kwargs.get('n_estimators', 100),
            learning_rate=kwargs.get('learning_rate', 0.1),
            max_depth=kwargs.get('max_depth', 6),
            random_state=42
        )
```

## 🚀 Modèles XGBoost

### XGBoost Classifier/Regressor

#### 📊 Caractéristiques
- **Type** : Gradient Boosting optimisé
- **Avantages** : Performance élevée, parallélisation
- **Usage** : Compétitions ML, production
- **Spécialités** : Gestion mémoire, régularisation

#### 🛠️ Implémentation
```python
class XGBoostModels(BaseModel):
    def _get_model(self, **kwargs):
        if self.model_type == 'classification':
            return xgb.XGBClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                subsample=kwargs.get('subsample', 0.8),
                colsample_bytree=kwargs.get('colsample_bytree', 0.8),
                random_state=42
            )
        else:
            return xgb.XGBRegressor(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                random_state=42
            )
```

#### ⚡ Optimisations
- **Early Stopping** : Arrêt automatique
- **Cross-Validation** : Validation croisée intégrée
- **Feature Importance** : Analyse SHAP
- **Hyperparameter Tuning** : GridSearch automatisé

## 📈 Modèles de Séries Temporelles

### Prophet (Facebook)

#### 📊 Caractéristiques
- **Type** : Modèle additif de séries temporelles
- **Avantages** : Gestion automatique de la saisonnalité
- **Usage** : Prévisions avec tendances et cycles
- **Spécialités** : Jours fériés, changements de tendance

#### 🛠️ Configuration
```python
class ProphetModels(BaseModel):
    def _create_prophet_model(self, **kwargs):
        return Prophet(
            daily_seasonality=kwargs.get('daily_seasonality', False),
            weekly_seasonality=kwargs.get('weekly_seasonality', True),
            yearly_seasonality=kwargs.get('yearly_seasonality', True),
            seasonality_mode=kwargs.get('seasonality_mode', 'additive'),
            changepoint_prior_scale=kwargs.get('changepoint_prior_scale', 0.05)
        )
```

#### 📊 Format des Données
```python
def prepare_data(self, df: pd.DataFrame, target_col: str, date_col: str = 'Date'):
    """Prépare les données au format Prophet (ds, y)."""
    prophet_data = pd.DataFrame({
        'ds': pd.to_datetime(df[date_col]),
        'y': df[target_col].astype(float)
    })
    return prophet_data
```

### NeuralProphet

#### 📊 Caractéristiques
- **Type** : Prophet avec réseaux de neurones
- **Avantages** : Patterns non-linéaires, variables externes
- **Usage** : Séries temporelles complexes
- **Spécialités** : Deep Learning, auto-régression

#### 🛠️ Configuration
```python
def _create_neuralprophet_model(self, **kwargs):
    return NeuralProphet(
        n_forecasts=kwargs.get('n_forecasts', 1),
        n_lags=kwargs.get('n_lags', 0),
        weekly_seasonality=kwargs.get('weekly_seasonality', True),
        yearly_seasonality=kwargs.get('yearly_seasonality', True),
        batch_size=kwargs.get('batch_size', 64),
        epochs=kwargs.get('epochs', 100)
    )
```

## 🎯 Cas d'Usage Spécialisés

### Maintenance Prédictive

#### 🔧 MaintenancePredictiveModel
```python
class MaintenancePredictiveModel(ClassicalModels):
    def __init__(self, algorithm: str = 'random_forest'):
        super().__init__(algorithm, 'classification')
    
    def prepare_features(self, production_df: pd.DataFrame, 
                        failures_df: pd.DataFrame) -> pd.DataFrame:
        """Prépare les features pour maintenance prédictive."""
        # Fusion des données
        merged_df = self._merge_production_failures(production_df, failures_df)
        
        # Features engineering
        merged_df = self._create_maintenance_features(merged_df)
        
        return merged_df
```

#### 📊 Features Engineering
- **Moyennes mobiles** : Tendances de production
- **Écarts-types** : Variabilité des paramètres
- **Ratios** : Water-oil ratio, efficacité
- **Temporelles** : Jours depuis dernière panne
- **Cumulative** : Production cumulée

### Prévision de Production

#### 📈 ProductionForecastModel
```python
class ProductionForecastModel(ClassicalModels):
    def __init__(self, algorithm: str = 'gradient_boosting'):
        super().__init__(algorithm, 'regression')
    
    def prepare_time_series_features(self, df: pd.DataFrame, 
                                   target_col: str, lookback_days: int = 30):
        """Crée des features de séries temporelles."""
        # Features temporelles
        df = FeatureEngineer.create_temporal_features(df)
        
        # Features de lag
        df = FeatureEngineer.create_lag_features(df, target_col, [1, 7, 14, 30])
        
        # Moyennes mobiles
        df = FeatureEngineer.create_rolling_features(df, target_col, [7, 14, 30])
        
        # Tendances
        df = FeatureEngineer.create_trend_features(df, target_col)
        
        return df
```

### Optimisation Injection d'Eau

#### 💧 WaterInjectionOptimizer
```python
class WaterInjectionOptimizer(ClassicalModels):
    def __init__(self, algorithm: str = 'random_forest'):
        super().__init__(algorithm, 'regression')
    
    def prepare_injection_features(self, production_df: pd.DataFrame):
        """Prépare les features pour optimisation injection."""
        # Ratios et efficacités
        df['water_oil_ratio'] = df['Production eau'] / df['Production huile']
        df['injection_efficiency'] = df['Production huile'] / df['Injection eau']
        
        # Features dérivées
        df['watercut_change'] = df['Watercut'].diff()
        df['production_efficiency'] = df['Production huile'] / df['Nombre puits actifs']
        
        return df
```

## 📊 Évaluation et Métriques

### Métriques de Classification

```python
def _evaluate_classification(self, y_true, y_pred, y_prob, model_name):
    """Évalue un modèle de classification."""
    metrics = ModelTrainer.calculate_metrics(y_true, y_pred, 'classification')
    
    return {
        'accuracy': metrics['accuracy'],
        'precision': metrics['precision'],
        'recall': metrics['recall'],
        'f1_score': metrics['f1_score'],
        'auc_roc': roc_auc_score(y_true, y_prob) if y_prob is not None else None,
        'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
    }
```

### Métriques de Régression

```python
def _evaluate_regression(self, y_true, y_pred, model_name):
    """Évalue un modèle de régression."""
    metrics = ModelTrainer.calculate_metrics(y_true, y_pred, 'regression')
    
    return {
        'mse': metrics['mse'],
        'rmse': metrics['rmse'],
        'mae': metrics['mae'],
        'r2': metrics['r2'],
        'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    }
```

### Validation Croisée

```python
def cross_validate_model(self, X, y, cv_folds=5):
    """Validation croisée du modèle."""
    scores = cross_val_score(
        self.model, X, y, 
        cv=cv_folds, 
        scoring='accuracy' if self.model_type == 'classification' else 'r2'
    )
    
    return {
        'mean_score': scores.mean(),
        'std_score': scores.std(),
        'scores': scores.tolist()
    }
```

## 🔧 Utilitaires Communs

### ModelTrainer

```python
class ModelTrainer:
    @staticmethod
    def prepare_train_test_split(X, y, test_size=0.2, random_state=42, stratify=False):
        """Division train/test avec stratification optionnelle."""
        stratify_param = y if stratify and len(np.unique(y)) > 1 else None
        return train_test_split(X, y, test_size=test_size, 
                              random_state=random_state, stratify=stratify_param)
    
    @staticmethod
    def calculate_metrics(y_true, y_pred, model_type='regression'):
        """Calcule les métriques selon le type de modèle."""
        if model_type == 'regression':
            return {
                'mse': mean_squared_error(y_true, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
                'mae': mean_absolute_error(y_true, y_pred),
                'r2': r2_score(y_true, y_pred)
            }
        else:  # classification
            return {
                'accuracy': accuracy_score(y_true, y_pred),
                'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
                'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
            }
```

### FeatureEngineer

```python
class FeatureEngineer:
    @staticmethod
    def create_temporal_features(df, date_col='Date'):
        """Crée des features temporelles."""
        df = df.copy()
        df['year'] = df[date_col].dt.year
        df['month'] = df[date_col].dt.month
        df['day'] = df[date_col].dt.day
        df['dayofweek'] = df[date_col].dt.dayofweek
        df['quarter'] = df[date_col].dt.quarter
        return df
    
    @staticmethod
    def create_lag_features(df, target_col, lags=[1, 7, 14, 30]):
        """Crée des features de lag."""
        df = df.copy()
        for lag in lags:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        return df
    
    @staticmethod
    def create_rolling_features(df, target_col, windows=[7, 14, 30]):
        """Crée des moyennes mobiles."""
        df = df.copy()
        for window in windows:
            df[f'{target_col}_MA_{window}'] = df[target_col].rolling(window=window).mean()
            df[f'{target_col}_Std_{window}'] = df[target_col].rolling(window=window).std()
        return df
```

## 🏭 Factory Pattern

### ModelFactory

```python
class ModelFactory:
    AVAILABLE_MODELS = {
        'maintenance_predictive': {
            'random_forest': MaintenancePredictiveModel,
            'gradient_boosting': MaintenancePredictiveModel,
            'xgboost': XGBoostMaintenanceModel
        },
        'production_forecast': {
            'random_forest': ProductionForecastModel,
            'gradient_boosting': ProductionForecastModel,
            'prophet': ProductionProphetModel,
            'neuralprophet': ProductionProphetModel,
            'xgboost': XGBoostProductionModel
        },
        'water_injection': {
            'random_forest': WaterInjectionOptimizer,
            'gradient_boosting': WaterInjectionOptimizer
        }
    }
    
    @classmethod
    def create_model(cls, model_category: str, algorithm: str):
        """Crée un modèle selon la catégorie et l'algorithme."""
        if model_category not in cls.AVAILABLE_MODELS:
            raise ValueError(f"Catégorie inconnue: {model_category}")
        
        if algorithm not in cls.AVAILABLE_MODELS[model_category]:
            raise ValueError(f"Algorithme non disponible: {algorithm}")
        
        model_class = cls.AVAILABLE_MODELS[model_category][algorithm]
        return model_class(algorithm)
```

## 🎛️ Hyperparamètres

### Configuration par Défaut

```python
def get_default_hyperparameters(algorithm: str, model_type: str) -> Dict[str, Any]:
    """Retourne les hyperparamètres par défaut."""
    defaults = {
        'random_forest': {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2
        },
        'gradient_boosting': {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 6,
            'subsample': 0.8
        },
        'xgboost': {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8
        },
        'prophet': {
            'daily_seasonality': False,
            'weekly_seasonality': True,
            'yearly_seasonality': True,
            'changepoint_prior_scale': 0.05
        }
    }
    
    return defaults.get(algorithm, {})
```

### Optimisation Automatique

```python
def _optimize_hyperparameters(self, X_train, y_train, **kwargs):
    """Optimise les hyperparamètres via GridSearch."""
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 6, 10],
        'learning_rate': [0.01, 0.1, 0.2]
    }
    
    grid_search = GridSearchCV(
        self.model, param_grid, 
        cv=5, scoring='accuracy', n_jobs=-1
    )
    
    grid_search.fit(X_train, y_train)
    return grid_search.best_estimator_
```

## 📈 Performance et Optimisation

### Techniques d'Optimisation

#### 🚀 Parallélisation
```python
# Configuration pour utiliser tous les cœurs
RandomForestClassifier(n_jobs=-1)
GridSearchCV(n_jobs=-1)
```

#### 💾 Gestion Mémoire
```python
# Optimisation XGBoost
xgb.XGBClassifier(
    tree_method='hist',  # Plus rapide
    max_bin=256,         # Réduction mémoire
    subsample=0.8        # Échantillonnage
)
```

#### ⚡ Early Stopping
```python
# Arrêt précoce pour éviter le surapprentissage
self.model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    early_stopping_rounds=10,
    verbose=False
)
```

## 🧪 Tests et Validation

### Tests Unitaires

```python
def test_model_training():
    """Test d'entraînement des modèles."""
    # Données de test
    X, y = make_classification(n_samples=100, n_features=10)
    
    # Test Random Forest
    model = ClassicalModels('random_forest', 'classification')
    results = model.train(pd.DataFrame(X), pd.Series(y))
    
    assert 'training_metrics' in results
    assert 'validation_metrics' in results
    assert model.is_trained
```

### Tests d'Intégration

```python
def test_full_pipeline():
    """Test du pipeline complet."""
    # Chargement des données
    production_df = load_production_data()
    
    # Création du modèle
    model = ModelFactory.create_model('production_forecast', 'random_forest')
    
    # Entraînement
    X, y = model.prepare_data(production_df, 'Production journaliere d\'huile bbl')
    results = model.train(X, y)
    
    # Prédiction
    predictions = model.predict(X.head(10))
    
    assert len(predictions) == 10
    assert all(isinstance(p, (int, float)) for p in predictions)
```

## 📚 Bonnes Pratiques

### ✅ Recommandations

1. **Validation croisée** systématique
2. **Feature engineering** métier
3. **Hyperparameter tuning** automatisé
4. **Monitoring** des performances
5. **Documentation** des expériences

### ❌ À Éviter

1. Surapprentissage sur données d'entraînement
2. Fuite de données (data leakage)
3. Validation sur données futures
4. Ignorer la distribution des données
5. Modèles non interprétables en production

## 🔍 Dépannage

### Problèmes Courants

#### 🚨 "Modèle ne converge pas"
- **Cause** : Learning rate trop élevé
- **Solution** : Réduire learning_rate, augmenter epochs

#### 🚨 "Performance dégradée"
- **Cause** : Surapprentissage ou données de mauvaise qualité
- **Solution** : Régularisation, nettoyage des données

#### 🚨 "Prédictions incohérentes"
- **Cause** : Features non normalisées ou outliers
- **Solution** : Standardisation, détection d'outliers

## 📞 Support

Pour assistance sur les modèles prédictifs :
- **Documentation** : Ce guide complet
- **Code source** : `src/models/`
- **Tests** : `tests/test_models.py`
- **Support** : Équipe Data Science

---

*Documentation technique complète des modèles ML. Version 2.0*