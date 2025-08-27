import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import GridSearchCV
from .base_model import BaseModel
from .model_utils import (
    DataValidator, FeatureEngineer, ModelTrainer, PredictionValidator,
    log_model_info, validate_model_requirements, get_default_hyperparameters
)
import warnings
warnings.filterwarnings('ignore')

# Configuration du logger
logger = logging.getLogger(__name__)

class ClassicalModels(BaseModel):
    """Implémentation des modèles classiques de machine learning."""
    
    def __init__(self, algorithm: str, model_type: str):
        """
        Initialise le modèle classique.
        
        Args:
            algorithm: Type d'algorithme ('random_forest', 'gradient_boosting', 'linear')
            model_type: Type de modèle ('classification', 'regression')
        """
        model_name = f"{algorithm}_{model_type}"
        super().__init__(model_name, model_type)
        self.algorithm = algorithm
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder() if model_type == 'classification' else None
        
    def _get_model(self, **kwargs):
        """Retourne le modèle approprié selon l'algorithme et le type."""
        if self.algorithm == 'random_forest':
            if self.model_type == 'classification':
                return RandomForestClassifier(
                    n_estimators=kwargs.get('n_estimators', 100),
                    max_depth=kwargs.get('max_depth', None),
                    min_samples_split=kwargs.get('min_samples_split', 2),
                    min_samples_leaf=kwargs.get('min_samples_leaf', 1),
                    random_state=kwargs.get('random_state', 42)
                )
            else:
                return RandomForestRegressor(
                    n_estimators=kwargs.get('n_estimators', 100),
                    max_depth=kwargs.get('max_depth', None),
                    min_samples_split=kwargs.get('min_samples_split', 2),
                    min_samples_leaf=kwargs.get('min_samples_leaf', 1),
                    random_state=kwargs.get('random_state', 42)
                )
        
        elif self.algorithm == 'gradient_boosting':
            if self.model_type == 'classification':
                return GradientBoostingClassifier(
                    n_estimators=kwargs.get('n_estimators', 100),
                    learning_rate=kwargs.get('learning_rate', 0.1),
                    max_depth=kwargs.get('max_depth', 3),
                    random_state=kwargs.get('random_state', 42)
                )
            else:
                return GradientBoostingRegressor(
                    n_estimators=kwargs.get('n_estimators', 100),
                    learning_rate=kwargs.get('learning_rate', 0.1),
                    max_depth=kwargs.get('max_depth', 3),
                    random_state=kwargs.get('random_state', 42)
                )
        
        elif self.algorithm == 'linear':
            if self.model_type == 'classification':
                return LogisticRegression(
                    random_state=kwargs.get('random_state', 42),
                    max_iter=kwargs.get('max_iter', 1000)
                )
            else:
                return LinearRegression()
        
        else:
            raise ValueError(f"Algorithme non supporté: {self.algorithm}")
    
    def prepare_data(self, df: pd.DataFrame, target_col: str, **kwargs) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prépare les données pour l'entraînement.
        
        Args:
            df: DataFrame contenant les données
            target_col: Nom de la colonne cible
            **kwargs: Arguments supplémentaires
            
        Returns:
            Tuple contenant les features (X) et la cible (y)
        """
        # Validation des données d'entrée
        DataValidator.validate_input_data(df, target_col)
        
        # Copier et séparer les features et la cible
        data = df.copy()
        y = data[target_col]
        X = data.drop(columns=[target_col])
        
        # Sélectionner uniquement les colonnes numériques
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        
        # Nettoyer les valeurs NaN
        X = DataValidator.clean_nan_values(X, strategy='median')
        
        # Gérer la cible selon le type de modèle
        if self.model_type == 'classification':
            # Encoder les labels si nécessaire
            if y.dtype == 'object' or y.dtype.name == 'category':
                y = y.astype(str)
                non_null_mask = y.notna()
                if non_null_mask.sum() == 0:
                    raise ValueError("Toutes les valeurs cibles sont NaN.")
                
                y_encoded = pd.Series(index=y.index, dtype=int)
                y_encoded[non_null_mask] = self.label_encoder.fit_transform(y[non_null_mask])
                y_encoded[~non_null_mask] = -1
                y = y_encoded
                
                # Supprimer les lignes avec des NaN dans y
                valid_mask = y != -1
                X = X[valid_mask]
                y = y[valid_mask]
            else:
                valid_mask = y.notna()
                X = X[valid_mask]
                y = y[valid_mask]
        else:
            # Régression
            if y.isna().all():
                raise ValueError("Toutes les valeurs cibles sont NaN.")
            y = y.fillna(y.median())
        
        # Supprimer les lignes avec trop de NaN (plus de 40%)
        initial_length = len(X)
        X = X.dropna(thresh=len(X.columns) * 0.6)
        y = y.loc[X.index]
        
        # Vérifications finales
        if len(X) < 10:
            raise ValueError("Données insuffisantes après nettoyage.")
        
        # Conversion en types numériques
        X = DataValidator.convert_to_numeric(X)
        if self.model_type == 'regression':
            y = DataValidator.convert_to_numeric(pd.DataFrame({'target': y}))['target']
        
        # Reset des index
        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)
        
        # Log du nettoyage
        removed_rows = initial_length - len(X)
        if removed_rows > 0:
            logger.warning(f"{removed_rows} lignes supprimées à cause de valeurs NaN persistantes.")
        
        # Sauvegarder les noms des features
        self.feature_names = X.columns.tolist()
        self.target_name = target_col
        
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Entraîne le modèle.
        
        Args:
            X: Features d'entraînement
            y: Cible d'entraînement
            **kwargs: Arguments supplémentaires
            
        Returns:
            Dictionnaire contenant les métriques d'entraînement
        """
        # Validation des données
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Aucune donnée disponible pour l'entraînement.")
        
        if len(X) < 10:
            raise ValueError(f"Données insuffisantes pour l'entraînement: {len(X)} échantillons. Minimum requis: 10.")
        
        # Vérifier qu'il n'y a pas que des NaN
        if X.isna().all().all():
            raise ValueError("Toutes les features sont NaN. Impossible d'entraîner le modèle.")
        
        # Diviser les données
        test_size = kwargs.get('test_size', 0.2)
        random_state = kwargs.get('random_state', 42)
        stratify = self.model_type == 'classification'
        
        X_train, X_test, y_train, y_test = ModelTrainer.prepare_train_test_split(
            X, y, test_size, random_state, stratify
        )
        
        # Préparation pour la normalisation
        # Gérer les colonnes avec variance nulle
        zero_var_cols = X_train.columns[X_train.var() == 0]
        if len(zero_var_cols) > 0:
            # Ajouter un petit bruit pour éviter la variance nulle
            for col in zero_var_cols:
                X_train[col] = X_train[col] + np.random.normal(0, 1e-8, len(X_train))
                X_test[col] = X_test[col] + np.random.normal(0, 1e-8, len(X_test))
        
        # Gérer les valeurs infinies
        X_train = X_train.replace([np.inf, -np.inf], np.nan)
        X_test = X_test.replace([np.inf, -np.inf], np.nan)
        
        # Remplir les NaN avec la médiane
        X_train = X_train.fillna(X_train.median()).fillna(0)
        X_test = X_test.fillna(X_train.median()).fillna(0)  # Utiliser la médiane du train
        
        # Normaliser les features
        try:
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
        except Exception as e:
            raise ValueError(f"Erreur lors de la normalisation: {e}")
        
        # Vérifier s'il reste des NaN après normalisation
        if np.isnan(X_train_scaled).any():
            # Remplacer les NaN par 0
            X_train_scaled = np.nan_to_num(X_train_scaled, nan=0.0, posinf=0.0, neginf=0.0)
            X_test_scaled = np.nan_to_num(X_test_scaled, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Créer et entraîner le modèle
        self.model = self._get_model(**kwargs)
        
        # Validation finale avant entraînement
        # Vérifier si y_train est un scalaire ou contient des NaN
        if hasattr(y_train, 'values'):
            y_values = y_train.values
        else:
            y_values = y_train
            
        if np.isscalar(y_values) or (hasattr(y_values, 'size') and y_values.size == 1):
            raise ValueError(f"y_train est un scalaire: {y_values}")
            
        if np.any(np.isnan(y_values)):
            nan_indices = np.where(np.isnan(y_values))[0]
            raise ValueError(f"y_train contient des NaN aux indices: {nan_indices[:10]}")
        
        # Vérification finale des données normalisées
        if np.any(np.isnan(X_train_scaled)) or np.any(np.isinf(X_train_scaled)):
            raise ValueError("X_train_scaled contient des NaN ou des valeurs infinies")
        
        # Optimisation des hyperparamètres si demandée
        if kwargs.get('optimize_hyperparameters', False):
            self.model = self._optimize_hyperparameters(X_train_scaled, y_train, **kwargs)
        else:
            self.model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Évaluation
        if self.model_type == 'classification':
            y_prob_train = self.model.predict_proba(X_train_scaled) if hasattr(self.model, 'predict_proba') else None
            y_prob_test = self.model.predict_proba(X_test_scaled) if hasattr(self.model, 'predict_proba') else None
            
            self.training_metrics = self.evaluate_classification(y_train, y_pred_train, 
                                                                 y_prob_train[:, 1] if y_prob_train is not None and y_prob_train.shape[1] > 1 else None)
            self.validation_metrics = self.evaluate_classification(y_test, y_pred_test,
                                                                  y_prob_test[:, 1] if y_prob_test is not None and y_prob_test.shape[1] > 1 else None)
        else:
            self.training_metrics = self.evaluate_regression(y_train, y_pred_train)
            self.validation_metrics = self.evaluate_regression(y_test, y_pred_test)
        
        self.is_trained = True
        
        # Retourner les données de test pour visualisation
        return {
            'training_metrics': self.training_metrics,
            'validation_metrics': self.validation_metrics,
            'X_test': pd.DataFrame(X_test_scaled, columns=self.feature_names),
            'y_test': y_test,
            'y_pred': y_pred_test,
            'y_prob': y_prob_test[:, 1] if self.model_type == 'classification' and y_prob_test is not None and y_prob_test.shape[1] > 1 else None
        }
    
    def _optimize_hyperparameters(self, X_train, y_train, **kwargs):
        """Optimise les hyperparamètres du modèle."""
        param_grids = {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20],
                'min_samples_split': [2, 5, 10]
            },
            'gradient_boosting': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            },
            'linear': {}
        }
        
        param_grid = param_grids.get(self.algorithm, {})
        
        if param_grid:
            base_model = self._get_model(**kwargs)
            grid_search = GridSearchCV(
                base_model, param_grid, 
                cv=kwargs.get('cv_folds', 3),
                scoring=kwargs.get('scoring', 'accuracy' if self.model_type == 'classification' else 'r2'),
                n_jobs=kwargs.get('n_jobs', -1)
            )
            grid_search.fit(X_train, y_train)
            return grid_search.best_estimator_
        else:
            model = self._get_model(**kwargs)
            model.fit(X_train, y_train)
            return model
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Fait des prédictions sur de nouvelles données.
        
        Args:
            X: Features pour la prédiction
            
        Returns:
            Array des prédictions
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions.")
        
        # Validation et nettoyage des données d'entrée
        X_validated = PredictionValidator.validate_prediction_input(
            X, getattr(self, 'feature_names', None)
        )
        X_clean = PredictionValidator.clean_prediction_data(X_validated)
        
        try:
            # Normaliser les features
            X_scaled = self.scaler.transform(X_clean)
            
            # Prédictions
            predictions = self.model.predict(X_scaled)
            
            # Décoder les prédictions pour la classification
            if self.model_type == 'classification' and self.label_encoder is not None and hasattr(self.label_encoder, 'classes_'):
                predictions = self.label_encoder.inverse_transform(predictions)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {e}")
            logger.error(f"Shape de X_clean: {X_clean.shape}")
            logger.error(f"Colonnes de X_clean: {X_clean.columns.tolist()}")
            raise ValueError(f"Erreur lors de la prédiction: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Fait des prédictions de probabilité.
        
        Args:
            X: Features pour la prédiction
            
        Returns:
            Array des probabilités ou None si non applicable
        """
        if self.model_type != 'classification' or not self.is_trained:
            return None
        
        if hasattr(self.model, 'predict_proba'):
            X_scaled = self.scaler.transform(X)
            return self.model.predict_proba(X_scaled)
        
        return None

class MaintenancePredictiveModel(ClassicalModels):
    """Modèle spécialisé pour la maintenance prédictive."""
    
    def __init__(self, algorithm: str = 'random_forest'):
        super().__init__(algorithm, 'classification')
        self.prediction_horizon = 7  # jours
    
    def prepare_features(self, production_df: pd.DataFrame, failures_df: pd.DataFrame) -> pd.DataFrame:
        """Prépare les features spécifiques à la maintenance prédictive."""
        # Vérifier qu'il y a des données
        if production_df.empty:
            raise ValueError("Aucune donnée de production disponible pour créer les features.")
        
        # Copier les données
        features_data = production_df.copy()
        features_data['Date'] = pd.to_datetime(features_data['Date'])
        features_data = features_data.sort_values('Date')
        
        # Vérifier les colonnes nécessaires
        required_cols = ["Production journaliere d'huile bbl", "Teneur en eau (Watercut)"]
        missing_cols = [col for col in required_cols if col not in features_data.columns]
        if missing_cols:
            raise ValueError(f"Colonnes manquantes dans les données: {missing_cols}")
        
        # Features dérivées avec gestion des fenêtres adaptatives
        data_length = len(features_data)
        
        # Ajuster les fenêtres selon la quantité de données disponibles
        window_7 = min(7, max(1, data_length // 4))
        window_30 = min(30, max(1, data_length // 2))
        
        features_data['Production_MA_7'] = features_data["Production journaliere d'huile bbl"].rolling(window=window_7, min_periods=1).mean()
        features_data['Production_MA_30'] = features_data["Production journaliere d'huile bbl"].rolling(window=window_30, min_periods=1).mean()
        features_data['Production_Std_7'] = features_data["Production journaliere d'huile bbl"].rolling(window=window_7, min_periods=1).std()
        features_data['Watercut_MA_7'] = features_data["Teneur en eau (Watercut)"].rolling(window=window_7, min_periods=1).mean()
        features_data['Production_Trend'] = features_data["Production journaliere d'huile bbl"].diff().fillna(0)
        features_data['Days_Since_Start'] = (features_data['Date'] - features_data['Date'].min()).dt.days
        
        # Créer les labels de pannes
        if not failures_df.empty and 'Date de notification d\'endomagement de la pompe' in failures_df.columns:
            try:
                failures_df_copy = failures_df.copy()
                failures_df_copy['Date de notification d\'endomagement de la pompe'] = pd.to_datetime(
                    failures_df_copy['Date de notification d\'endomagement de la pompe'], errors='coerce'
                )
                # Supprimer les dates invalides
                failures_df_copy = failures_df_copy.dropna(subset=['Date de notification d\'endomagement de la pompe'])
                
                if not failures_df_copy.empty:
                    failure_dates = set(failures_df_copy['Date de notification d\'endomagement de la pompe'].dt.date)
                    
                    # Label binaire (1 si panne dans les N prochains jours, 0 sinon)
                    features_data['Failure_Next_Days'] = 0
                    for i, row in features_data.iterrows():
                        current_date = row['Date'].date()
                        for j in range(1, self.prediction_horizon + 1):
                            future_date = current_date + pd.Timedelta(days=j)
                            if future_date in failure_dates:
                                features_data.loc[i, 'Failure_Next_Days'] = 1
                                break
                else:
                    # Pas de dates de pannes valides
                    features_data['Failure_Next_Days'] = 0
            except Exception as e:
                # En cas d'erreur, créer des labels par défaut
                features_data['Failure_Next_Days'] = 0
        else:
            # Si pas de données de pannes, créer des labels factices avec un peu de variabilité
            # pour éviter un dataset complètement déséquilibré
            np.random.seed(42)
            features_data['Failure_Next_Days'] = np.random.choice([0, 1], size=len(features_data), p=[0.9, 0.1])
        
        # Remplacer les NaN restants par des valeurs par défaut
        features_data = features_data.fillna({
            'Production_MA_7': features_data["Production journaliere d'huile bbl"].median(),
            'Production_MA_30': features_data["Production journaliere d'huile bbl"].median(),
            'Production_Std_7': 0,
            'Watercut_MA_7': features_data["Teneur en eau (Watercut)"].median(),
            'Production_Trend': 0
        })
        
        # Supprimer les lignes avec des NaN dans les colonnes critiques
        critical_cols = ["Production journaliere d'huile bbl", "Teneur en eau (Watercut)"]
        features_data = features_data.dropna(subset=critical_cols)
        
        # Vérifier qu'il reste des données
        if features_data.empty:
            raise ValueError("Aucune donnée valide après le nettoyage. Vérifiez la qualité des données d'entrée.")
        
        if len(features_data) < 5:
            raise ValueError(f"Données insuffisantes après nettoyage: {len(features_data)} échantillons. Minimum requis: 5.")
        
        return features_data

class ProductionForecastModel(ClassicalModels):
    """Modèle spécialisé pour la prévision de production."""
    
    def __init__(self, algorithm: str = 'gradient_boosting'):
        super().__init__(algorithm, 'regression')
    
    def prepare_time_series_features(self, df: pd.DataFrame, target_col: str, lookback_days: int = 30) -> pd.DataFrame:
        """Prépare les features pour la prévision de série temporelle."""
        data = df.copy()
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.sort_values('Date')
        
        # Vérifier qu'il y a assez de données
        if len(data) < 60:
            raise ValueError(f"Données insuffisantes pour créer des features temporelles: {len(data)} points (minimum 60)")
        
        # Créer les features temporelles
        data = FeatureEngineer.create_temporal_features(data, 'Date')
        
        # Créer les features de lag
        data = FeatureEngineer.create_lag_features(data, target_col, [1, 7, 14])
        
        # Créer les features de moyennes mobiles
        data = FeatureEngineer.create_rolling_features(data, target_col, [7, 14])
        
        # Créer les features de tendance
        data = FeatureEngineer.create_trend_features(data, target_col)
        
        # Nettoyage final
        initial_length = len(data)
        data = data.dropna(thresh=len(data.columns) * 0.6)
        
        if len(data) < 10:
            raise ValueError(f"Données insuffisantes après nettoyage: {len(data)} points (minimum 10)")
        
        # Log du nettoyage
        removed_rows = initial_length - len(data)
        if removed_rows > 0:
            logger.warning(f"{removed_rows} lignes supprimées à cause de trop de valeurs NaN.")
        
        return data

class WaterInjectionOptimizer(ClassicalModels):
    """Modèle spécialisé pour l'optimisation de l'injection d'eau."""
    
    def __init__(self, algorithm: str = 'random_forest'):
        super().__init__(algorithm, 'regression')
    
    def prepare_injection_features(self, production_df: pd.DataFrame) -> pd.DataFrame:
        """Prépare les features pour l'optimisation de l'injection d'eau."""
        df = production_df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Calculer l'efficacité de l'injection (production d'huile / production d'eau)
        df['Oil_Water_Efficiency'] = df["Production journaliere d'huile bbl"] / (df["Production journaliere d'eau bbl"] + 1)
        
        # Features dérivées
        df['Watercut_Change'] = df["Teneur en eau (Watercut)"].diff()
        df['Production_Change'] = df["Production journaliere d'huile bbl"].diff()
        df['Water_Production_Ratio'] = df["Production journaliere d'eau bbl"] / df["Production journaliere d'huile bbl"]
        
        # Moyennes mobiles
        for col in ["Production journaliere d'huile bbl", "Production journaliere d'eau bbl", "Teneur en eau (Watercut)"]:
            df[f'{col}_MA_7'] = df[col].rolling(window=7).mean()
            df[f'{col}_MA_30'] = df[col].rolling(window=30).mean()
        
        df = df.dropna()
        return df