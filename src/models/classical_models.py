import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from .base_model import BaseModel
import warnings
warnings.filterwarnings('ignore')

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
        # Copier le DataFrame
        data = df.copy()
        
        # Séparer les features et la cible
        y = data[target_col]
        X = data.drop(columns=[target_col])
        
        # Sélectionner uniquement les colonnes numériques pour les features
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        
        # Gérer les valeurs manquantes
        X = X.fillna(X.mean())
        y = y.fillna(y.mean() if self.model_type == 'regression' else y.mode()[0])
        
        # Encoder la cible pour la classification
        if self.model_type == 'classification' and self.label_encoder is not None:
            y = pd.Series(self.label_encoder.fit_transform(y), index=y.index)
        
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
        # Diviser les données
        test_size = kwargs.get('test_size', 0.2)
        random_state = kwargs.get('random_state', 42)
        
        if self.model_type == 'classification':
            stratify = y if len(np.unique(y)) > 1 else None
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=stratify
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
        
        # Normaliser les features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Créer et entraîner le modèle
        self.model = self._get_model(**kwargs)
        
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
        Fait des prédictions.
        
        Args:
            X: Features pour la prédiction
            
        Returns:
            Array des prédictions
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions.")
        
        # Normaliser les features
        X_scaled = self.scaler.transform(X)
        
        # Prédictions
        predictions = self.model.predict(X_scaled)
        
        # Décoder les prédictions pour la classification
        if self.model_type == 'classification' and self.label_encoder is not None:
            predictions = self.label_encoder.inverse_transform(predictions)
        
        return predictions
    
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
        # Copier les données
        features_data = production_df.copy()
        features_data['Date'] = pd.to_datetime(features_data['Date'])
        features_data = features_data.sort_values('Date')
        
        # Features dérivées
        features_data['Production_MA_7'] = features_data["Production journaliere d'huile bbl"].rolling(window=7).mean()
        features_data['Production_MA_30'] = features_data["Production journaliere d'huile bbl"].rolling(window=30).mean()
        features_data['Production_Std_7'] = features_data["Production journaliere d'huile bbl"].rolling(window=7).std()
        features_data['Watercut_MA_7'] = features_data["Teneur en eau (Watercut)"].rolling(window=7).mean()
        features_data['Production_Trend'] = features_data["Production journaliere d'huile bbl"].diff()
        features_data['Days_Since_Start'] = (features_data['Date'] - features_data['Date'].min()).dt.days
        
        # Créer les labels de pannes
        if not failures_df.empty:
            failures_df['Date de notification d\'endomagement de la pompe'] = pd.to_datetime(
                failures_df['Date de notification d\'endomagement de la pompe']
            )
            failure_dates = set(failures_df['Date de notification d\'endomagement de la pompe'].dt.date)
            
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
            # Si pas de données de pannes, créer des labels factices
            features_data['Failure_Next_Days'] = 0
        
        # Supprimer les lignes avec des NaN
        features_data = features_data.dropna()
        
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
        
        # Features temporelles
        data['Year'] = data['Date'].dt.year
        data['Month'] = data['Date'].dt.month
        data['Day'] = data['Date'].dt.day
        data['DayOfWeek'] = data['Date'].dt.dayofweek
        data['DayOfYear'] = data['Date'].dt.dayofyear
        
        # Features de lag
        for lag in [1, 7, 14, 30]:
            data[f'{target_col}_lag_{lag}'] = data[target_col].shift(lag)
        
        # Moyennes mobiles
        for window in [7, 14, 30]:
            data[f'{target_col}_MA_{window}'] = data[target_col].rolling(window=window).mean()
            data[f'{target_col}_Std_{window}'] = data[target_col].rolling(window=window).std()
        
        # Tendances
        data[f'{target_col}_Trend_7'] = data[target_col].diff(7)
        data[f'{target_col}_Trend_30'] = data[target_col].diff(30)
        
        # Supprimer les NaN
        data = data.dropna()
        
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