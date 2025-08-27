#!/usr/bin/env python3
"""
Utilitaires communs pour les modèles ML
Réduit la duplication de code entre les différents types de modèles
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional, Union
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Configuration du logger
logger = logging.getLogger(__name__)

class DataValidator:
    """Classe utilitaire pour la validation et le nettoyage des données."""
    
    @staticmethod
    def validate_input_data(df: pd.DataFrame, target_col: str, min_samples: int = 10) -> None:
        """Valide les données d'entrée."""
        if df is None or df.empty:
            raise ValueError("Le DataFrame ne peut pas être vide.")
        
        if target_col not in df.columns:
            raise ValueError(f"La colonne cible '{target_col}' n'existe pas dans les données.")
        
        if len(df) < min_samples:
            raise ValueError(f"Données insuffisantes: {len(df)} échantillons (minimum {min_samples} requis).")
    
    @staticmethod
    def clean_nan_values(df: pd.DataFrame, strategy: str = 'median') -> pd.DataFrame:
        """Nettoie les valeurs NaN dans un DataFrame."""
        df_clean = df.copy()
        
        for col in df_clean.columns:
            if df_clean[col].isna().all():
                # Si toute la colonne est NaN
                df_clean[col] = 0
            elif df_clean[col].dtype in ['int64', 'int32', 'int16', 'int8', 'float64', 'float32']:
                # Colonnes numériques
                if strategy == 'median':
                    df_clean[col] = df_clean[col].fillna(df_clean[col].median())
                elif strategy == 'mean':
                    df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
                elif strategy == 'zero':
                    df_clean[col] = df_clean[col].fillna(0)
                else:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            else:
                # Colonnes non-numériques
                df_clean[col] = df_clean[col].fillna(df_clean[col].mode().iloc[0] if not df_clean[col].mode().empty else 'unknown')
        
        return df_clean
    
    @staticmethod
    def convert_to_numeric(df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
        """Convertit les colonnes en types numériques de façon sécurisée."""
        df_converted = df.copy()
        exclude_cols = exclude_cols or []
        
        for col in df_converted.columns:
            if col in exclude_cols:
                continue
                
            if df_converted[col].dtype in ['int64', 'int32', 'int16', 'int8']:
                df_converted[col] = df_converted[col].astype(float)
            elif df_converted[col].dtype == 'object':
                try:
                    df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce').astype(float)
                    # Remplacer les NaN résultants de la conversion
                    df_converted[col] = df_converted[col].fillna(0)
                except:
                    # Si la conversion échoue complètement
                    try:
                        df_converted[col] = df_converted[col].astype(float)
                    except:
                        logger.warning(f"Impossible de convertir la colonne {col} en numérique")
            else:
                df_converted[col] = df_converted[col].astype(float)
        
        return df_converted
    
    @staticmethod
    def remove_outliers(df: pd.DataFrame, columns: list = None, method: str = 'iqr', factor: float = 1.5) -> pd.DataFrame:
        """Supprime les valeurs aberrantes."""
        df_clean = df.copy()
        columns = columns or df_clean.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in columns:
            if method == 'iqr':
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - factor * IQR
                upper_bound = Q3 + factor * IQR
                df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]
            elif method == 'zscore':
                z_scores = np.abs((df_clean[col] - df_clean[col].mean()) / df_clean[col].std())
                df_clean = df_clean[z_scores < factor]
        
        return df_clean

class FeatureEngineer:
    """Classe utilitaire pour l'ingénierie des features."""
    
    @staticmethod
    def create_temporal_features(df: pd.DataFrame, date_col: str = 'Date') -> pd.DataFrame:
        """Crée des features temporelles à partir d'une colonne de date."""
        df_features = df.copy()
        
        if date_col not in df_features.columns:
            return df_features
        
        # Convertir en datetime si nécessaire
        df_features[date_col] = pd.to_datetime(df_features[date_col])
        
        # Features temporelles (conversion directe en float pour éviter les problèmes de casting)
        df_features['Year'] = df_features[date_col].dt.year.astype(float)
        df_features['Month'] = df_features[date_col].dt.month.astype(float)
        df_features['Day'] = df_features[date_col].dt.day.astype(float)
        df_features['DayOfWeek'] = df_features[date_col].dt.dayofweek.astype(float)
        df_features['DayOfYear'] = df_features[date_col].dt.dayofyear.astype(float)
        df_features['Quarter'] = df_features[date_col].dt.quarter.astype(float)
        df_features['WeekOfYear'] = df_features[date_col].dt.isocalendar().week.astype(float)
        
        return df_features
    
    @staticmethod
    def create_lag_features(df: pd.DataFrame, target_col: str, lags: list = [1, 7, 14, 30]) -> pd.DataFrame:
        """Crée des features de lag pour une série temporelle."""
        df_features = df.copy()
        
        for lag in lags:
            lag_col = f'{target_col}_lag_{lag}'
            df_features[lag_col] = df_features[target_col].shift(lag)
            # Remplir les NaN avec la méthode backfill puis la médiane
            df_features[lag_col] = df_features[lag_col].fillna(method='bfill').fillna(df_features[target_col].median())
        
        return df_features
    
    @staticmethod
    def create_rolling_features(df: pd.DataFrame, target_col: str, windows: list = [7, 14, 30]) -> pd.DataFrame:
        """Crée des features de moyennes mobiles et statistiques roulantes."""
        df_features = df.copy()
        
        for window in windows:
            # Moyenne mobile
            ma_col = f'{target_col}_MA_{window}'
            df_features[ma_col] = df_features[target_col].rolling(window=window, min_periods=1).mean()
            df_features[ma_col] = df_features[ma_col].fillna(df_features[target_col].median())
            
            # Écart-type mobile
            std_col = f'{target_col}_Std_{window}'
            df_features[std_col] = df_features[target_col].rolling(window=window, min_periods=1).std()
            df_features[std_col] = df_features[std_col].fillna(0)
            
            # Min et Max mobiles
            min_col = f'{target_col}_Min_{window}'
            max_col = f'{target_col}_Max_{window}'
            df_features[min_col] = df_features[target_col].rolling(window=window, min_periods=1).min()
            df_features[max_col] = df_features[target_col].rolling(window=window, min_periods=1).max()
            df_features[min_col] = df_features[min_col].fillna(df_features[target_col].median())
            df_features[max_col] = df_features[max_col].fillna(df_features[target_col].median())
        
        return df_features
    
    @staticmethod
    def create_trend_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Crée des features de tendance."""
        df_features = df.copy()
        
        # Différence première (changement)
        df_features[f'{target_col}_Diff'] = df_features[target_col].diff().fillna(0)
        
        # Pourcentage de changement
        df_features[f'{target_col}_PctChange'] = df_features[target_col].pct_change().fillna(0)
        
        # Tendance (régression linéaire simple sur une fenêtre)
        window = min(30, len(df_features) // 4)
        if window > 1:
            df_features[f'{target_col}_Trend'] = df_features[target_col].rolling(window=window, min_periods=1).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0, raw=False
            ).fillna(0)
        else:
            df_features[f'{target_col}_Trend'] = 0
        
        return df_features

class ModelTrainer:
    """Classe utilitaire pour l'entraînement des modèles."""
    
    @staticmethod
    def prepare_train_test_split(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, 
                               random_state: int = 42, stratify: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Prépare la division train/test avec validation."""
        # Ajuster test_size si trop peu de données
        min_test_samples = 2
        if len(X) * test_size < min_test_samples:
            test_size = min_test_samples / len(X)
            test_size = min(test_size, 0.5)  # Maximum 50%
        
        # Stratification pour la classification si demandée
        stratify_param = y if stratify and len(np.unique(y)) > 1 else None
        
        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=stratify_param)
    
    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, model_type: str = 'regression') -> Dict[str, float]:
        """Calcule les métriques appropriées selon le type de modèle."""
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        metrics = {}
        
        if model_type == 'regression':
            metrics['mse'] = mean_squared_error(y_true, y_pred)
            metrics['rmse'] = np.sqrt(metrics['mse'])
            metrics['mae'] = mean_absolute_error(y_true, y_pred)
            metrics['r2'] = r2_score(y_true, y_pred)
        else:  # classification
            metrics['accuracy'] = accuracy_score(y_true, y_pred)
            metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['f1_score'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        return metrics

class PredictionValidator:
    """Classe utilitaire pour la validation des prédictions."""
    
    @staticmethod
    def validate_prediction_input(X: Union[pd.DataFrame, np.ndarray], feature_names: list = None) -> pd.DataFrame:
        """Valide et nettoie les données d'entrée pour la prédiction."""
        # Validation de base
        if X is None or len(X) == 0:
            raise ValueError("Les données de prédiction ne peuvent pas être vides.")
        
        # Conversion en DataFrame si nécessaire
        if not isinstance(X, pd.DataFrame):
            if hasattr(X, 'shape') and len(X.shape) == 1:
                # Convertir un array 1D en DataFrame
                feature_names = feature_names or [f'feature_{i}' for i in range(len(X))]
                X = pd.DataFrame([X], columns=feature_names)
            else:
                X = pd.DataFrame(X)
        
        # Vérifier les dimensions
        if X.shape[1] == 0:
            raise ValueError("Les données de prédiction n'ont aucune feature.")
        
        return X
    
    @staticmethod
    def clean_prediction_data(X: pd.DataFrame) -> pd.DataFrame:
        """Nettoie les données pour la prédiction."""
        X_clean = X.copy()
        
        # Nettoyer les valeurs NaN
        X_clean = DataValidator.clean_nan_values(X_clean, strategy='median')
        
        # Convertir en types numériques
        X_clean = DataValidator.convert_to_numeric(X_clean)
        
        # Vérification finale
        if np.any(np.isnan(X_clean.values)):
            logger.warning("Des NaN persistent après nettoyage, remplacement par 0")
            X_clean = X_clean.fillna(0)
        
        return X_clean

# Fonctions utilitaires globales
def log_model_info(model_name: str, data_shape: tuple, duration: float, metrics: Dict[str, float]) -> None:
    """Log les informations d'entraînement d'un modèle."""
    logger.info(f"Modèle {model_name} entraîné:")
    logger.info(f"  - Données: {data_shape}")
    logger.info(f"  - Durée: {duration:.2f}s")
    for metric, value in metrics.items():
        logger.info(f"  - {metric.upper()}: {value:.4f}")

def validate_model_requirements(model_type: str, algorithm: str) -> None:
    """Valide que les requirements pour un modèle sont satisfaits."""
    if algorithm == 'xgboost':
        try:
            import xgboost
        except ImportError:
            raise ImportError("XGBoost n'est pas installé. Installez-le avec: pip install xgboost")
    
    elif algorithm in ['prophet', 'neuralprophet']:
        try:
            import prophet
        except ImportError:
            raise ImportError("Prophet n'est pas installé. Installez-le avec: pip install prophet")
        
        if algorithm == 'neuralprophet':
            try:
                import neuralprophet
            except ImportError:
                raise ImportError("NeuralProphet n'est pas installé. Installez-le avec: pip install neuralprophet")

def get_default_hyperparameters(algorithm: str, model_type: str) -> Dict[str, Any]:
    """Retourne les hyperparamètres par défaut pour un algorithme."""
    defaults = {
        'random_forest': {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'random_state': 42
        },
        'gradient_boosting': {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 3,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'random_state': 42
        },
        'xgboost': {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 1.0,
            'colsample_bytree': 1.0,
            'reg_alpha': 0,
            'reg_lambda': 1,
            'random_state': 42,
            'n_jobs': -1
        }
    }
    
    return defaults.get(algorithm, {})