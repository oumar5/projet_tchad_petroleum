# 🧹 Guide de Nettoyage et Préparation des Données

## Vue d'Ensemble

Ce document détaille les processus de nettoyage, validation et préparation des données pétrolières pour la modélisation prédictive.

## 🎯 Objectifs du Nettoyage

- **Qualité** : Éliminer les erreurs et incohérences
- **Cohérence** : Standardiser les formats et unités
- **Complétude** : Traiter les valeurs manquantes
- **Fiabilité** : Détecter et corriger les anomalies
- **Préparation** : Optimiser pour les algorithmes ML

## 🔄 Pipeline de Nettoyage

### Étape 1 : Validation Initiale

#### 📊 Contrôles de Base
```python
# Validation des types de données
def validate_input_data(df: pd.DataFrame, target_col: str, min_samples: int = 10):
    """Valide les données d'entrée."""
    if df.empty:
        raise ValueError("DataFrame vide fourni")
    
    if len(df) < min_samples:
        raise ValueError(f"Pas assez d'échantillons: {len(df)} < {min_samples}")
    
    if target_col not in df.columns:
        raise ValueError(f"Colonne cible '{target_col}' non trouvée")
```

#### 🔍 Détection des Problèmes
- **Données manquantes** : Identification des NaN
- **Types incorrects** : Validation des formats
- **Doublons** : Détection des lignes dupliquées
- **Valeurs aberrantes** : Identification des outliers

### Étape 2 : Nettoyage des Valeurs Manquantes

#### 🛠️ Stratégies de Traitement

```python
def clean_nan_values(df: pd.DataFrame, strategy: str = 'median') -> pd.DataFrame:
    """Nettoie les valeurs NaN selon la stratégie choisie."""
    df_clean = df.copy()
    
    for col in df_clean.columns:
        if df_clean[col].dtype in ['float64', 'int64']:
            if strategy == 'median':
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            elif strategy == 'mean':
                df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
            elif strategy == 'zero':
                df_clean[col] = df_clean[col].fillna(0)
            elif strategy == 'forward':
                df_clean[col] = df_clean[col].fillna(method='ffill')
    
    return df_clean
```

#### 📋 Méthodes par Type de Données

| Type de Donnée | Méthode Recommandée | Alternative |
|----------------|---------------------|-------------|
| Production (bbl) | Médiane | Interpolation linéaire |
| Nombre de puits | Mode | Valeur précédente |
| Watercut (%) | Médiane | Moyenne mobile |
| Dates | Interpolation | Suppression ligne |
| Ratios | Calcul dérivé | Médiane |

### Étape 3 : Conversion et Standardisation

#### 🔢 Conversion des Types

```python
def convert_to_numeric(df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
    """Convertit les colonnes en types numériques."""
    df_converted = df.copy()
    exclude_cols = exclude_cols or ['Date']
    
    for col in df_converted.columns:
        if col not in exclude_cols:
            if df_converted[col].dtype == 'object':
                # Tentative de conversion numérique
                df_converted[col] = pd.to_numeric(
                    df_converted[col], errors='coerce'
                )
            
            # Conversion int64 vers float pour éviter les erreurs
            if df_converted[col].dtype == 'int64':
                df_converted[col] = df_converted[col].astype('float64')
    
    return df_converted
```

#### 📅 Traitement des Dates

```python
def standardize_dates(df: pd.DataFrame, date_col: str = 'Date') -> pd.DataFrame:
    """Standardise le format des dates."""
    df_clean = df.copy()
    
    # Conversion en datetime
    df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
    
    # Suppression des dates invalides
    invalid_dates = df_clean[date_col].isnull()
    if invalid_dates.any():
        print(f"Suppression de {invalid_dates.sum()} dates invalides")
        df_clean = df_clean[~invalid_dates]
    
    # Tri chronologique
    df_clean = df_clean.sort_values(date_col).reset_index(drop=True)
    
    return df_clean
```

### Étape 4 : Détection et Traitement des Outliers

#### 📊 Méthodes de Détection

```python
def remove_outliers(df: pd.DataFrame, columns: list = None, 
                   method: str = 'iqr', factor: float = 1.5) -> pd.DataFrame:
    """Supprime les valeurs aberrantes."""
    df_clean = df.copy()
    columns = columns or df.select_dtypes(include=[np.number]).columns
    
    for col in columns:
        if method == 'iqr':
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - factor * IQR
            upper_bound = Q3 + factor * IQR
            
            # Suppression des outliers
            mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
            df_clean = df_clean[mask]
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(df_clean[col]))
            df_clean = df_clean[z_scores < factor]
    
    return df_clean
```

#### 🎯 Seuils par Variable

| Variable | Méthode | Seuil | Justification |
|----------|---------|-------|---------------|
| Production huile | IQR | 1.5 | Variations naturelles |
| Production eau | IQR | 2.0 | Plus de variabilité |
| Watercut | Z-score | 3.0 | Distribution normale |
| Nombre puits | Logique | Min/Max | Contraintes physiques |

## 🔧 Fonctions Utilitaires

### DataValidator Class

```python
class DataValidator:
    """Classe utilitaire pour la validation des données."""
    
    @staticmethod
    def validate_input_data(df: pd.DataFrame, target_col: str, min_samples: int = 10):
        """Validation complète des données d'entrée."""
        # Vérifications de base
        if df.empty:
            raise ValueError("DataFrame vide")
        
        if len(df) < min_samples:
            raise ValueError(f"Échantillons insuffisants: {len(df)}")
        
        if target_col not in df.columns:
            raise ValueError(f"Colonne cible manquante: {target_col}")
    
    @staticmethod
    def clean_nan_values(df: pd.DataFrame, strategy: str = 'median'):
        """Nettoyage intelligent des valeurs manquantes."""
        # Implémentation détaillée...
        pass
    
    @staticmethod
    def convert_to_numeric(df: pd.DataFrame, exclude_cols: list = None):
        """Conversion sécurisée vers types numériques."""
        # Implémentation détaillée...
        pass
```

### PredictionValidator Class

```python
class PredictionValidator:
    """Validation spécifique pour les prédictions."""
    
    @staticmethod
    def validate_prediction_input(X, feature_names: list = None):
        """Valide les données pour prédiction."""
        if X is None or (hasattr(X, 'empty') and X.empty):
            raise ValueError("Données de prédiction vides")
        
        # Conversion en DataFrame si nécessaire
        if not isinstance(X, pd.DataFrame):
            if feature_names:
                X = pd.DataFrame(X, columns=feature_names)
            else:
                X = pd.DataFrame(X)
        
        return X
    
    @staticmethod
    def clean_prediction_data(X: pd.DataFrame):
        """Nettoyage pour données de prédiction."""
        X_clean = X.copy()
        
        # Remplacement des NaN
        for col in X_clean.columns:
            if X_clean[col].dtype in ['float64', 'int64']:
                median_val = X_clean[col].median()
                if pd.isna(median_val):
                    median_val = 0
                X_clean[col] = X_clean[col].fillna(median_val)
        
        # Conversion des types
        X_clean = X_clean.astype('float64', errors='ignore')
        
        return X_clean
```

## 📊 Métriques de Qualité

### Indicateurs de Nettoyage

```python
def calculate_cleaning_metrics(df_original: pd.DataFrame, 
                             df_cleaned: pd.DataFrame) -> dict:
    """Calcule les métriques de qualité du nettoyage."""
    return {
        'rows_removed': len(df_original) - len(df_cleaned),
        'removal_rate': (len(df_original) - len(df_cleaned)) / len(df_original) * 100,
        'missing_before': df_original.isnull().sum().sum(),
        'missing_after': df_cleaned.isnull().sum().sum(),
        'completeness': (1 - df_cleaned.isnull().sum().sum() / df_cleaned.size) * 100,
        'data_types_fixed': sum(df_original.dtypes != df_cleaned.dtypes)
    }
```

### Dashboard de Qualité

| Métrique | Avant Nettoyage | Après Nettoyage | Amélioration |
|----------|-----------------|-----------------|---------------|
| Lignes totales | 3,500 | 3,420 | -2.3% |
| Valeurs manquantes | 245 | 0 | -100% |
| Types incorrects | 8 | 0 | -100% |
| Outliers détectés | 67 | 0 | -100% |
| Complétude | 92.1% | 100% | +7.9% |

## 🔄 Processus Spécialisés

### Nettoyage pour Maintenance Prédictive

```python
def prepare_maintenance_data(production_df: pd.DataFrame, 
                           failures_df: pd.DataFrame) -> pd.DataFrame:
    """Préparation spécifique pour maintenance prédictive."""
    # Fusion des données
    merged_df = production_df.merge(
        failures_df, on='Date', how='left'
    )
    
    # Création de la variable cible
    merged_df['failure_risk'] = merged_df['failure_occurred'].fillna(0)
    
    # Features engineering
    merged_df = create_maintenance_features(merged_df)
    
    return merged_df
```

### Nettoyage pour Prévision de Production

```python
def prepare_forecast_data(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Préparation pour prévision de production."""
    df_clean = df.copy()
    
    # Tri chronologique
    df_clean = df_clean.sort_values('Date')
    
    # Interpolation des valeurs manquantes
    df_clean[target_col] = df_clean[target_col].interpolate(method='linear')
    
    # Lissage des valeurs aberrantes
    df_clean[target_col] = smooth_outliers(df_clean[target_col])
    
    return df_clean
```

## 🚨 Gestion des Erreurs

### Types d'Erreurs Communes

#### 📁 Erreurs de Format
```python
try:
    df = pd.read_excel(file_path)
except Exception as e:
    logger.error(f"Erreur lecture fichier: {e}")
    raise ValueError(f"Format de fichier invalide: {e}")
```

#### 🔢 Erreurs de Conversion
```python
try:
    df[col] = pd.to_numeric(df[col])
except ValueError as e:
    logger.warning(f"Conversion impossible pour {col}: {e}")
    # Stratégie de fallback
    df[col] = df[col].fillna(0)
```

#### 📊 Erreurs de Validation
```python
if df[target_col].isnull().all():
    raise ValueError(f"Colonne cible {target_col} entièrement vide")

if len(df) == 0:
    raise ValueError("Aucune donnée valide après nettoyage")
```

## 📈 Optimisations Performance

### Techniques d'Optimisation

#### 🚀 Vectorisation
```python
# Au lieu de boucles
for i, row in df.iterrows():
    df.loc[i, 'new_col'] = calculate_value(row)

# Utiliser la vectorisation
df['new_col'] = df.apply(calculate_value, axis=1)
# Ou mieux encore
df['new_col'] = vectorized_calculate(df)
```

#### 💾 Gestion Mémoire
```python
# Optimisation des types de données
def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Optimise les types de données pour réduire la mémoire."""
    for col in df.columns:
        if df[col].dtype == 'int64':
            if df[col].min() >= 0 and df[col].max() < 255:
                df[col] = df[col].astype('uint8')
            elif df[col].min() >= -128 and df[col].max() < 127:
                df[col] = df[col].astype('int8')
    
    return df
```

## 🧪 Tests de Validation

### Tests Unitaires

```python
import pytest

def test_data_cleaning():
    """Test du processus de nettoyage."""
    # Données de test avec problèmes connus
    test_data = pd.DataFrame({
        'Date': ['2023-01-01', '2023-01-02', None],
        'Production': [1000, None, 1500],
        'Watercut': [20.5, 25.0, 150.0]  # Outlier
    })
    
    # Nettoyage
    cleaned_data = clean_data_pipeline(test_data)
    
    # Assertions
    assert cleaned_data['Production'].isnull().sum() == 0
    assert cleaned_data['Watercut'].max() <= 100  # Pas d'outlier
    assert len(cleaned_data) >= 2  # Au moins 2 lignes valides
```

### Tests d'Intégration

```python
def test_full_pipeline():
    """Test du pipeline complet."""
    # Chargement des données réelles
    df = load_production_data()
    
    # Pipeline complet
    df_clean = full_cleaning_pipeline(df)
    
    # Validations
    assert df_clean.isnull().sum().sum() == 0
    assert len(df_clean) > 0
    assert all(df_clean.dtypes != 'object')  # Sauf dates
```

## 📚 Bonnes Pratiques

### ✅ Recommandations

1. **Sauvegarde** des données originales
2. **Documentation** de chaque transformation
3. **Validation** après chaque étape
4. **Tests** automatisés du pipeline
5. **Monitoring** de la qualité en continu

### ❌ À Éviter

1. Suppression massive de données sans analyse
2. Remplacement aveugle des valeurs manquantes
3. Modification des données sources
4. Nettoyage sans validation des résultats
5. Pipeline non reproductible

## 🔍 Dépannage

### Problèmes Fréquents

#### 🚨 "DataFrame vide après nettoyage"
- **Cause** : Critères de nettoyage trop stricts
- **Solution** : Assouplir les seuils de détection d'outliers

#### 🚨 "Erreur de conversion de type"
- **Cause** : Données non numériques dans colonnes numériques
- **Solution** : Utiliser `errors='coerce'` dans `pd.to_numeric()`

#### 🚨 "Performance dégradée"
- **Cause** : Opérations non vectorisées
- **Solution** : Remplacer les boucles par des opérations pandas

## 📞 Support

Pour assistance sur le nettoyage des données :
- **Documentation** : Ce guide complet
- **Code source** : `src/models/model_utils.py`
- **Tests** : `tests/test_data_cleaning.py`
- **Support** : Équipe technique

---

*Document mis à jour avec les dernières optimisations. Version 2.0*