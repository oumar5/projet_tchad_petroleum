import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from .base_model import BaseModel
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None

class XGBoostModels(BaseModel):
    """Implémentation des modèles XGBoost pour classification et régression."""
    
    def __init__(self, model_type: str = 'regression'):
        """
        Initialise le modèle XGBoost.
        
        Args:
            model_type: Type de modèle ('classification' ou 'regression')
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost n'est pas installé. Installez-le avec: pip install xgboost")
        
        model_name = f"xgboost_{model_type}"
        super().__init__(model_name, model_type)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder() if model_type == 'classification' else None
        self.feature_importance_df = None
        
    def _get_model(self, **kwargs):
        """Retourne le modèle XGBoost approprié selon le type."""
        if self.model_type == 'classification':
            return xgb.XGBClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                subsample=kwargs.get('subsample', 1.0),
                colsample_bytree=kwargs.get('colsample_bytree', 1.0),
                reg_alpha=kwargs.get('reg_alpha', 0),
                reg_lambda=kwargs.get('reg_lambda', 1),
                random_state=kwargs.get('random_state', 42),
                n_jobs=kwargs.get('n_jobs', -1),
                eval_metric=kwargs.get('eval_metric', 'logloss'),
                use_label_encoder=False
            )
        else:
            return xgb.XGBRegressor(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                subsample=kwargs.get('subsample', 1.0),
                colsample_bytree=kwargs.get('colsample_bytree', 1.0),
                reg_alpha=kwargs.get('reg_alpha', 0),
                reg_lambda=kwargs.get('reg_lambda', 1),
                random_state=kwargs.get('random_state', 42),
                n_jobs=kwargs.get('n_jobs', -1),
                eval_metric=kwargs.get('eval_metric', 'rmse')
            )
    
    def prepare_data(self, df: pd.DataFrame, target_col: str, **kwargs) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prépare les données pour XGBoost.
        
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
        
        # Sélectionner uniquement les colonnes numériques
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        
        # Gérer les valeurs manquantes (XGBoost peut gérer les NaN nativement)
        # Mais on peut choisir de les remplir
        if kwargs.get('fill_missing', True):
            X = X.fillna(X.median())
            if self.model_type == 'regression':
                y = y.fillna(y.median())
            else:
                y = y.fillna(y.mode()[0] if not y.mode().empty else 0)
        
        # Encoder la cible pour la classification
        if self.model_type == 'classification' and self.label_encoder is not None:
            y = pd.Series(self.label_encoder.fit_transform(y), index=y.index)
        
        # Sauvegarder les noms des features
        self.feature_names = X.columns.tolist()
        self.target_name = target_col
        
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Entraîne le modèle XGBoost.
        
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
        
        # Normalisation optionnelle (XGBoost n'en a pas forcément besoin)
        if kwargs.get('scale_features', False):
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            X_train = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
            X_test = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
        
        # Créer le modèle
        self.model = self._get_model(**kwargs)
        
        # Configuration de l'early stopping
        early_stopping_rounds = kwargs.get('early_stopping_rounds', 10)
        eval_set = [(X_train, y_train), (X_test, y_test)]
        
        # Optimisation des hyperparamètres si demandée
        if kwargs.get('optimize_hyperparameters', False):
            self.model = self._optimize_hyperparameters(X_train, y_train, **kwargs)
        else:
            # Entraînement avec early stopping
            self.model.fit(
                X_train, y_train,
                eval_set=eval_set,
                early_stopping_rounds=early_stopping_rounds,
                verbose=kwargs.get('verbose', False)
            )
        
        # Prédictions
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        # Évaluation
        if self.model_type == 'classification':
            y_prob_train = self.model.predict_proba(X_train) if hasattr(self.model, 'predict_proba') else None
            y_prob_test = self.model.predict_proba(X_test) if hasattr(self.model, 'predict_proba') else None
            
            self.training_metrics = self.evaluate_classification(
                y_train, y_pred_train, 
                y_prob_train[:, 1] if y_prob_train is not None and y_prob_train.shape[1] > 1 else None
            )
            self.validation_metrics = self.evaluate_classification(
                y_test, y_pred_test,
                y_prob_test[:, 1] if y_prob_test is not None and y_prob_test.shape[1] > 1 else None
            )
        else:
            self.training_metrics = self.evaluate_regression(y_train, y_pred_train)
            self.validation_metrics = self.evaluate_regression(y_test, y_pred_test)
        
        # Importance des features
        self.feature_importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.is_trained = True
        
        return {
            'training_metrics': self.training_metrics,
            'validation_metrics': self.validation_metrics,
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': y_pred_test,
            'y_prob': y_prob_test[:, 1] if self.model_type == 'classification' and y_prob_test is not None and y_prob_test.shape[1] > 1 else None,
            'feature_importance': self.feature_importance_df,
            'training_history': self.model.evals_result_ if hasattr(self.model, 'evals_result_') else None
        }
    
    def _optimize_hyperparameters(self, X_train, y_train, **kwargs):
        """Optimise les hyperparamètres du modèle XGBoost."""
        param_grid = {
            'n_estimators': kwargs.get('n_estimators_grid', [100, 200, 300]),
            'max_depth': kwargs.get('max_depth_grid', [3, 6, 9]),
            'learning_rate': kwargs.get('learning_rate_grid', [0.01, 0.1, 0.2]),
            'subsample': kwargs.get('subsample_grid', [0.8, 0.9, 1.0]),
            'colsample_bytree': kwargs.get('colsample_bytree_grid', [0.8, 0.9, 1.0])
        }
        
        base_model = self._get_model(**kwargs)
        
        # Utiliser une recherche plus efficace pour XGBoost
        grid_search = GridSearchCV(
            base_model, param_grid,
            cv=kwargs.get('cv_folds', 3),
            scoring=kwargs.get('scoring', 'accuracy' if self.model_type == 'classification' else 'r2'),
            n_jobs=kwargs.get('n_jobs', -1),
            verbose=kwargs.get('verbose', 0)
        )
        
        grid_search.fit(X_train, y_train)
        return grid_search.best_estimator_
    
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
        
        # Normaliser si nécessaire
        if hasattr(self.scaler, 'mean_'):
            X_scaled = self.scaler.transform(X)
            X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        
        # Prédictions
        predictions = self.model.predict(X)
        
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
        
        # Normaliser si nécessaire
        if hasattr(self.scaler, 'mean_'):
            X_scaled = self.scaler.transform(X)
            X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Retourne l'importance des features.
        
        Returns:
            DataFrame avec l'importance des features
        """
        return self.feature_importance_df
    
    def plot_importance(self, max_num_features: int = 20, importance_type: str = 'weight'):
        """
        Crée un graphique d'importance des features.
        
        Args:
            max_num_features: Nombre maximum de features à afficher
            importance_type: Type d'importance ('weight', 'gain', 'cover')
            
        Returns:
            Figure matplotlib
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de créer des graphiques.")
        
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(10, 8))
        xgb.plot_importance(
            self.model, 
            ax=ax, 
            max_num_features=max_num_features,
            importance_type=importance_type
        )
        plt.tight_layout()
        return fig
    
    def plot_tree(self, num_trees: int = 0, **kwargs):
        """
        Visualise un arbre spécifique du modèle.
        
        Args:
            num_trees: Numéro de l'arbre à visualiser
            **kwargs: Arguments supplémentaires pour plot_tree
            
        Returns:
            Figure matplotlib
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de créer des graphiques.")
        
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(20, 10))
        xgb.plot_tree(self.model, num_trees=num_trees, ax=ax, **kwargs)
        plt.tight_layout()
        return fig
    
    def get_training_history(self) -> Optional[Dict]:
        """
        Retourne l'historique d'entraînement si disponible.
        
        Returns:
            Dictionnaire avec l'historique d'entraînement
        """
        if hasattr(self.model, 'evals_result_'):
            return self.model.evals_result_
        return None
    
    def plot_training_history(self):
        """
        Crée un graphique de l'historique d'entraînement.
        
        Returns:
            Figure matplotlib
        """
        history = self.get_training_history()
        if history is None:
            raise ValueError("Aucun historique d'entraînement disponible.")
        
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Tracer les métriques d'entraînement et de validation
        for dataset_name, metrics in history.items():
            for metric_name, values in metrics.items():
                ax.plot(values, label=f'{dataset_name}_{metric_name}')
        
        ax.set_xlabel('Iterations')
        ax.set_ylabel('Metric Value')
        ax.set_title('Training History')
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        return fig
    
    def explain_prediction(self, X: pd.DataFrame, sample_idx: int = 0):
        """
        Explique une prédiction spécifique (nécessite SHAP).
        
        Args:
            X: Features
            sample_idx: Index de l'échantillon à expliquer
            
        Returns:
            Valeurs SHAP si SHAP est disponible
        """
        try:
            import shap
            
            if not self.is_trained:
                raise ValueError("Le modèle doit être entraîné avant d'expliquer les prédictions.")
            
            # Créer l'explainer
            explainer = shap.TreeExplainer(self.model)
            
            # Calculer les valeurs SHAP
            shap_values = explainer.shap_values(X)
            
            # Retourner les valeurs pour l'échantillon spécifié
            if isinstance(shap_values, list):  # Classification multi-classe
                return shap_values[1][sample_idx] if len(shap_values) > 1 else shap_values[0][sample_idx]
            else:
                return shap_values[sample_idx]
                
        except ImportError:
            raise ImportError("SHAP n'est pas installé. Installez-le avec: pip install shap")

class XGBoostMaintenanceModel(XGBoostModels):
    """Modèle XGBoost spécialisé pour la maintenance prédictive."""
    
    def __init__(self):
        super().__init__('classification')
        self.prediction_horizon = 7
    
    def prepare_maintenance_features(self, production_df: pd.DataFrame, failures_df: pd.DataFrame) -> pd.DataFrame:
        """Prépare les features spécifiques à la maintenance prédictive avec XGBoost."""
        # Utiliser la même logique que les modèles classiques mais optimisée pour XGBoost
        features_data = production_df.copy()
        features_data['Date'] = pd.to_datetime(features_data['Date'])
        features_data = features_data.sort_values('Date')
        
        # Features avancées pour XGBoost
        # Moyennes mobiles multiples
        for window in [3, 7, 14, 30, 60]:
            features_data[f'Production_MA_{window}'] = features_data["Production journaliere d'huile bbl"].rolling(window=window).mean()
            features_data[f'Production_Std_{window}'] = features_data["Production journaliere d'huile bbl"].rolling(window=window).std()
            features_data[f'Watercut_MA_{window}'] = features_data["Teneur en eau (Watercut)"].rolling(window=window).mean()
        
        # Features de tendance
        for lag in [1, 3, 7, 14, 30]:
            features_data[f'Production_Lag_{lag}'] = features_data["Production journaliere d'huile bbl"].shift(lag)
            features_data[f'Production_Diff_{lag}'] = features_data["Production journaliere d'huile bbl"].diff(lag)
        
        # Features cycliques (jour de la semaine, mois)
        features_data['DayOfWeek'] = features_data['Date'].dt.dayofweek
        features_data['Month'] = features_data['Date'].dt.month
        features_data['Quarter'] = features_data['Date'].dt.quarter
        
        # Features d'interaction
        features_data['Production_Watercut_Ratio'] = features_data["Production journaliere d'huile bbl"] / (features_data["Teneur en eau (Watercut)"] + 1)
        features_data['Wells_Production_Ratio'] = features_data["Production journaliere d'huile bbl"] / (features_data["Nombre des puits actifs"] + 1)
        
        # Créer les labels de pannes
        if not failures_df.empty:
            failures_df['Date de notification d\'endomagement de la pompe'] = pd.to_datetime(
                failures_df['Date de notification d\'endomagement de la pompe']
            )
            failure_dates = set(failures_df['Date de notification d\'endomagement de la pompe'].dt.date)
            
            features_data['Failure_Next_Days'] = 0
            for i, row in features_data.iterrows():
                current_date = row['Date'].date()
                for j in range(1, self.prediction_horizon + 1):
                    future_date = current_date + pd.Timedelta(days=j)
                    if future_date in failure_dates:
                        features_data.loc[i, 'Failure_Next_Days'] = 1
                        break
        else:
            features_data['Failure_Next_Days'] = 0
        
        # Supprimer les lignes avec trop de NaN
        features_data = features_data.dropna(thresh=len(features_data.columns) * 0.7)
        
        return features_data

class XGBoostProductionModel(XGBoostModels):
    """Modèle XGBoost spécialisé pour la prévision de production."""
    
    def __init__(self):
        super().__init__('regression')
    
    def prepare_production_features(self, df: pd.DataFrame, target_col: str = "Production journaliere d'huile bbl") -> pd.DataFrame:
        """Prépare les features spécifiques à la prévision de production avec XGBoost."""
        data = df.copy()
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.sort_values('Date')
        
        # Features temporelles détaillées
        data['Year'] = data['Date'].dt.year
        data['Month'] = data['Date'].dt.month
        data['Day'] = data['Date'].dt.day
        data['DayOfWeek'] = data['Date'].dt.dayofweek
        data['DayOfYear'] = data['Date'].dt.dayofyear
        data['WeekOfYear'] = data['Date'].dt.isocalendar().week
        data['Quarter'] = data['Date'].dt.quarter
        
        # Features cycliques (sin/cos pour capturer la cyclicité)
        data['Month_sin'] = np.sin(2 * np.pi * data['Month'] / 12)
        data['Month_cos'] = np.cos(2 * np.pi * data['Month'] / 12)
        data['DayOfWeek_sin'] = np.sin(2 * np.pi * data['DayOfWeek'] / 7)
        data['DayOfWeek_cos'] = np.cos(2 * np.pi * data['DayOfWeek'] / 7)
        
        # Features de lag étendues
        for lag in [1, 2, 3, 7, 14, 21, 30, 60, 90]:
            data[f'{target_col}_lag_{lag}'] = data[target_col].shift(lag)
        
        # Moyennes mobiles multiples
        for window in [3, 7, 14, 21, 30, 60, 90]:
            data[f'{target_col}_MA_{window}'] = data[target_col].rolling(window=window).mean()
            data[f'{target_col}_Std_{window}'] = data[target_col].rolling(window=window).std()
            data[f'{target_col}_Min_{window}'] = data[target_col].rolling(window=window).min()
            data[f'{target_col}_Max_{window}'] = data[target_col].rolling(window=window).max()
        
        # Features de tendance
        for period in [7, 14, 30, 60]:
            data[f'{target_col}_Trend_{period}'] = data[target_col].diff(period)
            data[f'{target_col}_PctChange_{period}'] = data[target_col].pct_change(period)
        
        # Features d'accélération (dérivée seconde)
        data[f'{target_col}_Acceleration_7'] = data[f'{target_col}_Trend_7'].diff()
        data[f'{target_col}_Acceleration_30'] = data[f'{target_col}_Trend_30'].diff()
        
        # Supprimer les lignes avec trop de NaN
        data = data.dropna(thresh=len(data.columns) * 0.6)
        
        return data