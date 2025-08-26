# Documentation des Modèles de Machine Learning

## Vue d'ensemble

Ce document détaille tous les modèles de machine learning disponibles dans le système de modélisation prédictive de Tchad Petroleum Company.

## Classification des Modèles

### Par Catégorie

1. **Modèles Classiques** : Random Forest, Gradient Boosting, Régression
2. **Modèles XGBoost** : XGBClassifier, XGBRegressor
3. **Modèles de Séries Temporelles** : Prophet, NeuralProphet

### Par Type de Problème

1. **Classification** : Maintenance prédictive
2. **Régression** : Prévision de production, optimisation injection
3. **Séries Temporelles** : Prévision avec saisonnalité

## Modèles Classiques

### Random Forest

#### Description
Ensemble d'arbres de décision utilisant le bagging et la sélection aléatoire de features.

#### Avantages
- **Robuste au surapprentissage**
- **Gestion native des valeurs manquantes**
- **Importance des features intégrée**
- **Parallélisable**
- **Interprétable**

#### Inconvénients
- **Peut être biaisé vers les features catégorielles**
- **Moins performant sur les données très déséquilibrées**
- **Mémoire importante pour de gros ensembles**

#### Hyperparamètres Clés
```python
{
    'n_estimators': [50, 100, 200],      # Nombre d'arbres
    'max_depth': [None, 10, 20],         # Profondeur maximale
    'min_samples_split': [2, 5, 10],     # Échantillons min pour split
    'min_samples_leaf': [1, 2, 4]        # Échantillons min par feuille
}
```

#### Cas d'Usage Recommandés
- **Maintenance prédictive** : Classification binaire des pannes
- **Données tabulaires** : Features mixtes (numériques/catégorielles)
- **Besoin d'interprétabilité** : Importance des features

### Gradient Boosting

#### Description
Ensemble séquentiel d'arbres faibles, chaque arbre corrigeant les erreurs du précédent.

#### Avantages
- **Très haute performance**
- **Gestion des interactions complexes**
- **Robuste aux outliers**
- **Flexible (différentes fonctions de perte)**

#### Inconvénients
- **Sensible au surapprentissage**
- **Plus lent à entraîner**
- **Hyperparamètres sensibles**
- **Moins parallélisable**

#### Hyperparamètres Clés
```python
{
    'n_estimators': [50, 100, 200],      # Nombre d'estimateurs
    'learning_rate': [0.01, 0.1, 0.2],   # Taux d'apprentissage
    'max_depth': [3, 5, 7],              # Profondeur des arbres
    'subsample': [0.8, 0.9, 1.0]         # Fraction d'échantillons
}
```

#### Cas d'Usage Recommandés
- **Prévision de production** : Régression avec tendances complexes
- **Optimisation** : Relations non-linéaires
- **Compétitions ML** : Performance maximale

## Modèles XGBoost

### XGBoost Classifier/Regressor

#### Description
Implémentation optimisée du gradient boosting avec régularisation avancée.

#### Avantages
- **Performance state-of-the-art**
- **Régularisation intégrée (L1/L2)**
- **Gestion native des valeurs manquantes**
- **Parallélisation efficace**
- **Early stopping automatique**
- **Importance des features multiple**

#### Inconvénients
- **Complexité des hyperparamètres**
- **Temps d'entraînement variable**
- **Mémoire importante**
- **Dépendance externe**

#### Hyperparamètres Avancés
```python
{
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 6, 9],
    'learning_rate': [0.01, 0.1, 0.2],
    'subsample': [0.8, 0.9, 1.0],
    'colsample_bytree': [0.8, 0.9, 1.0],
    'reg_alpha': [0, 0.1, 1],            # Régularisation L1
    'reg_lambda': [1, 1.5, 2],           # Régularisation L2
    'gamma': [0, 0.1, 0.2],              # Complexité minimale
    'min_child_weight': [1, 3, 5]        # Poids minimal des feuilles
}
```

#### Features Spécialisées

##### Maintenance Prédictive
```python
# Features engineering avancé
features = [
    # Moyennes mobiles multiples
    'Production_MA_3', 'Production_MA_7', 'Production_MA_14', 'Production_MA_30', 'Production_MA_60',
    
    # Écarts-types mobiles
    'Production_Std_3', 'Production_Std_7', 'Production_Std_14', 'Production_Std_30',
    
    # Features de lag
    'Production_Lag_1', 'Production_Lag_3', 'Production_Lag_7', 'Production_Lag_14', 'Production_Lag_30',
    
    # Différences
    'Production_Diff_1', 'Production_Diff_3', 'Production_Diff_7', 'Production_Diff_14', 'Production_Diff_30',
    
    # Features cycliques
    'DayOfWeek', 'Month', 'Quarter',
    
    # Features d'interaction
    'Production_Watercut_Ratio', 'Wells_Production_Ratio'
]
```

##### Prévision de Production
```python
# Features temporelles étendues
features = [
    # Temporelles de base
    'Year', 'Month', 'Day', 'DayOfWeek', 'DayOfYear', 'WeekOfYear', 'Quarter',
    
    # Cycliques (sin/cos)
    'Month_sin', 'Month_cos', 'DayOfWeek_sin', 'DayOfWeek_cos',
    
    # Lags étendus
    'Production_lag_1', 'Production_lag_2', 'Production_lag_3', 'Production_lag_7',
    'Production_lag_14', 'Production_lag_21', 'Production_lag_30', 'Production_lag_60', 'Production_lag_90',
    
    # Statistiques mobiles
    'Production_MA_3', 'Production_MA_7', 'Production_MA_14', 'Production_MA_21',
    'Production_MA_30', 'Production_MA_60', 'Production_MA_90',
    
    'Production_Std_3', 'Production_Std_7', 'Production_Std_14', 'Production_Std_21',
    'Production_Std_30', 'Production_Std_60', 'Production_Std_90',
    
    'Production_Min_7', 'Production_Min_14', 'Production_Min_30',
    'Production_Max_7', 'Production_Max_14', 'Production_Max_30',
    
    # Tendances et accélérations
    'Production_Trend_7', 'Production_Trend_14', 'Production_Trend_30', 'Production_Trend_60',
    'Production_PctChange_7', 'Production_PctChange_14', 'Production_PctChange_30', 'Production_PctChange_60',
    'Production_Acceleration_7', 'Production_Acceleration_30'
]
```

#### Cas d'Usage Recommandés
- **Tous les cas d'usage** : Performance maximale
- **Gros datasets** : >10,000 échantillons
- **Features complexes** : Interactions non-linéaires
- **Compétitions** : Benchmarking

## Modèles de Séries Temporelles

### Prophet

#### Description
Modèle additif pour séries temporelles développé par Facebook, optimisé pour les données business.

#### Composantes du Modèle
```
y(t) = g(t) + s(t) + h(t) + ε(t)
```
- **g(t)** : Tendance (linéaire ou logistique)
- **s(t)** : Saisonnalité (Fourier)
- **h(t)** : Effets des jours fériés
- **ε(t)** : Terme d'erreur

#### Avantages
- **Gestion automatique de la saisonnalité**
- **Robuste aux valeurs manquantes**
- **Interprétabilité des composantes**
- **Intervalles de confiance**
- **Gestion des jours fériés**
- **Détection de points de changement**

#### Inconvénients
- **Limité aux séries univariées**
- **Hypothèse d'additivité**
- **Moins flexible que les modèles ML**
- **Performance variable selon les données**

#### Configuration pour Production Pétrolière
```python
model = Prophet(
    growth='linear',                    # Tendance linéaire
    yearly_seasonality=True,           # Saisonnalité annuelle
    weekly_seasonality=True,           # Saisonnalité hebdomadaire
    daily_seasonality=False,           # Pas de saisonnalité journalière
    seasonality_mode='additive',       # Mode additif
    changepoint_range=0.8,             # 80% des données pour changepoints
    changepoint_prior_scale=0.05,      # Flexibilité des changepoints
    seasonality_prior_scale=10.0,      # Force de la saisonnalité
    holidays_prior_scale=10.0,         # Force des jours fériés
    interval_width=0.80                # Intervalle de confiance 80%
)

# Ajouter des régresseurs externes
model.add_regressor('active_wells')    # Nombre de puits actifs
model.add_regressor('watercut')        # Teneur en eau
model.add_regressor('water_production') # Production d'eau

# Saisonnalités personnalisées
model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
model.add_seasonality(name='quarterly', period=91.25, fourier_order=3)
```

#### Cas d'Usage Recommandés
- **Prévision de production** : Données avec saisonnalité claire
- **Planification long terme** : Horizons >6 mois
- **Analyse de tendances** : Décomposition des composantes
- **Détection d'anomalies** : Écarts aux prédictions

### NeuralProphet

#### Description
Version neuronale de Prophet utilisant PyTorch, combinant les avantages de Prophet avec la flexibilité des réseaux de neurones.

#### Avantages par rapport à Prophet
- **Réseaux de neurones** : Modélisation non-linéaire
- **Autoregression** : Utilisation des valeurs passées
- **Régresseurs laggés** : Features avec retards
- **Validation croisée intégrée**
- **Régularisation avancée**

#### Configuration Avancée
```python
model = NeuralProphet(
    growth='linear',
    n_changepoints=10,                 # Points de changement
    changepoints_range=0.8,
    trend_reg=0,                       # Régularisation de tendance
    yearly_seasonality='auto',
    weekly_seasonality='auto',
    daily_seasonality=False,
    seasonality_mode='additive',
    seasonality_reg=0,                 # Régularisation saisonnalité
    n_forecasts=1,                     # Horizon de prévision
    n_lags=30,                         # Nombre de lags autorégressifs
    num_hidden_layers=0,               # Couches cachées
    d_hidden=None,                     # Taille des couches cachées
    learning_rate=None,                # Taux d'apprentissage auto
    epochs=None,                       # Époques auto
    batch_size=None,                   # Taille de batch auto
    loss_func='Huber',                 # Fonction de perte robuste
    normalize='auto',                  # Normalisation automatique
    impute_missing=True                # Imputation des valeurs manquantes
)
```

#### Cas d'Usage Recommandés
- **Séries complexes** : Relations non-linéaires
- **Gros datasets** : >1000 points temporels
- **Prévision court terme** : Horizons <3 mois
- **Features multiples** : Régresseurs externes

## Métriques d'Évaluation

### Classification (Maintenance Prédictive)

#### Métriques Principales
```python
metrics = {
    'accuracy': accuracy_score(y_true, y_pred),
    'precision': precision_score(y_true, y_pred, average='weighted'),
    'recall': recall_score(y_true, y_pred, average='weighted'),
    'f1_score': f1_score(y_true, y_pred, average='weighted'),
    'roc_auc': roc_auc_score(y_true, y_prob)  # Pour classification binaire
}
```

#### Interprétation
- **Accuracy** : Pourcentage de prédictions correctes
- **Precision** : Parmi les pannes prédites, combien sont vraies
- **Recall** : Parmi les vraies pannes, combien sont détectées
- **F1-Score** : Moyenne harmonique de precision et recall
- **ROC-AUC** : Capacité de discrimination (0.5 = aléatoire, 1.0 = parfait)

#### Seuils Recommandés
- **Accuracy** : >0.85
- **Precision** : >0.80 (éviter les fausses alarmes)
- **Recall** : >0.90 (détecter toutes les pannes)
- **F1-Score** : >0.85
- **ROC-AUC** : >0.80

### Régression (Prévision de Production)

#### Métriques Principales
```python
metrics = {
    'mse': mean_squared_error(y_true, y_pred),
    'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
    'mae': mean_absolute_error(y_true, y_pred),
    'r2': r2_score(y_true, y_pred),
    'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
}
```

#### Interprétation
- **MSE** : Erreur quadratique moyenne (pénalise les gros écarts)
- **RMSE** : Racine de MSE (même unité que la cible)
- **MAE** : Erreur absolue moyenne (robuste aux outliers)
- **R²** : Coefficient de détermination (0 = modèle constant, 1 = parfait)
- **MAPE** : Erreur absolue moyenne en pourcentage

#### Seuils Recommandés (Production)
- **R²** : >0.80
- **MAPE** : <15%
- **RMSE** : <10% de la moyenne de production

### Séries Temporelles

#### Métriques Spécifiques
```python
metrics = {
    # Métriques de régression standard
    'rmse': rmse,
    'mae': mae,
    'mape': mape,
    'r2': r2,
    
    # Métriques spécifiques aux séries temporelles
    'directional_accuracy': directional_accuracy,  # Prédiction de direction
    'theil_u': theil_u,                           # Statistique de Theil
    'mase': mase                                   # Mean Absolute Scaled Error
}
```

#### Directional Accuracy
```python
# Mesure si le modèle prédit correctement la direction du changement
true_direction = np.diff(y_true) > 0
pred_direction = np.diff(y_pred) > 0
directional_accuracy = np.mean(true_direction == pred_direction)
```

#### Theil's U Statistic
```python
# Compare la performance à un modèle naïf
theil_u = np.sqrt(np.mean((y_pred - y_true)**2)) / np.sqrt(np.mean(y_true**2))
# U < 1 : meilleur que naïf, U = 1 : équivalent, U > 1 : pire
```

#### MASE (Mean Absolute Scaled Error)
```python
# Normalise l'erreur par rapport à un modèle saisonnier naïf
naive_forecast_error = np.mean(np.abs(np.diff(y_true)))
mase = np.mean(np.abs(y_true - y_pred)) / naive_forecast_error
# MASE < 1 : meilleur que naïf
```

## Sélection de Modèles

### Arbre de Décision

```
Type de problème ?
├── Classification (Maintenance)
│   ├── Dataset < 1000 → Random Forest
│   ├── Dataset 1000-10000 → Gradient Boosting
│   └── Dataset > 10000 → XGBoost
│
├── Régression (Production)
│   ├── Saisonnalité forte ?
│   │   ├── Oui → Prophet/NeuralProphet
│   │   └── Non → XGBoost/Gradient Boosting
│   └── Dataset < 1000 → Random Forest
│
└── Série Temporelle
    ├── Saisonnalité claire → Prophet
    ├── Relations complexes → NeuralProphet
    └── Features multiples → XGBoost avec features temporelles
```

### Recommandations par Contexte

#### Maintenance Prédictive
1. **XGBoost** (recommandé) : Performance maximale
2. **Random Forest** : Interprétabilité
3. **Gradient Boosting** : Équilibre performance/complexité

#### Prévision de Production
1. **Prophet** : Saisonnalité forte, interprétabilité
2. **XGBoost** : Performance, features complexes
3. **NeuralProphet** : Relations non-linéaires
4. **Gradient Boosting** : Équilibre général

#### Optimisation Injection d'Eau
1. **XGBoost** : Relations complexes
2. **Gradient Boosting** : Performance élevée
3. **Random Forest** : Robustesse

## Bonnes Pratiques

### Préparation des Données

1. **Validation temporelle** : Split chronologique
2. **Feature engineering** : Moyennes mobiles, lags, tendances
3. **Gestion des outliers** : Détection et traitement
4. **Normalisation** : Selon le modèle (XGBoost n'en a pas besoin)

### Entraînement

1. **Validation croisée** : Temporelle pour les séries
2. **Early stopping** : Éviter le surapprentissage
3. **Hyperparameter tuning** : GridSearch ou Bayesian
4. **Ensemble methods** : Combiner plusieurs modèles

### Évaluation

1. **Métriques multiples** : Ne pas se fier à une seule
2. **Validation sur données récentes** : Test de robustesse
3. **Analyse des résidus** : Détecter les biais
4. **Feature importance** : Comprendre les drivers

### Déploiement

1. **Monitoring continu** : Dérive des performances
2. **Réentraînement périodique** : Données fraîches
3. **A/B testing** : Comparer les versions
4. **Fallback** : Modèle de secours

## Troubleshooting

### Problèmes Courants

#### Surapprentissage
**Symptômes** : Performance train >> test
**Solutions** :
- Réduire la complexité du modèle
- Augmenter la régularisation
- Plus de données d'entraînement
- Early stopping

#### Sous-apprentissage
**Symptômes** : Performance train et test faibles
**Solutions** :
- Augmenter la complexité du modèle
- Plus de features
- Réduire la régularisation
- Plus d'époques d'entraînement

#### Déséquilibre des Classes
**Symptômes** : Precision/Recall déséquilibrés
**Solutions** :
- Rééchantillonnage (SMOTE)
- Pondération des classes
- Métriques adaptées (F1, AUC)
- Seuil de décision optimisé

#### Dérive des Données
**Symptômes** : Performance dégradée en production
**Solutions** :
- Monitoring des distributions
- Réentraînement régulier
- Détection d'anomalies
- Adaptation du modèle

### Diagnostics

#### Courbes d'Apprentissage
```python
# Analyser la convergence
plt.plot(train_scores, label='Train')
plt.plot(val_scores, label='Validation')
plt.legend()
```

#### Analyse des Résidus
```python
# Vérifier les hypothèses du modèle
residuals = y_pred - y_true
plt.scatter(y_pred, residuals)
plt.axhline(y=0, color='r', linestyle='--')
```

#### Distribution des Erreurs
```python
# Vérifier la normalité des erreurs
plt.hist(residuals, bins=50)
stats.normaltest(residuals)  # Test de normalité
```