from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score, confusion_matrix
)
import warnings
warnings.filterwarnings('ignore')

class BaseModel(ABC):
    """Classe de base abstraite pour tous les modèles de prédiction."""
    
    def __init__(self, model_name: str, model_type: str):
        """
        Initialise le modèle de base.
        
        Args:
            model_name: Nom du modèle
            model_type: Type de modèle ('classification', 'regression', 'timeseries')
        """
        self.model_name = model_name
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        self.feature_names = None
        self.target_name = None
        self.scaler = None
        self.training_metrics = {}
        self.validation_metrics = {}
        
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Fait des prédictions.
        
        Args:
            X: Features pour la prédiction
            
        Returns:
            Array des prédictions
        """
        pass
    
    def predict_proba(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Fait des prédictions de probabilité (pour les modèles de classification).
        
        Args:
            X: Features pour la prédiction
            
        Returns:
            Array des probabilités ou None si non applicable
        """
        if self.model_type != 'classification':
            return None
        
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        return None
    
    def evaluate_classification(self, y_true: np.ndarray, y_pred: np.ndarray, 
                              y_prob: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Évalue un modèle de classification.
        
        Args:
            y_true: Vraies valeurs
            y_pred: Prédictions
            y_prob: Probabilités (optionnel)
            
        Returns:
            Dictionnaire des métriques
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }
        
        # AUC-ROC pour classification binaire
        if y_prob is not None and len(np.unique(y_true)) == 2:
            try:
                if y_prob.ndim > 1:
                    y_prob = y_prob[:, 1]  # Probabilité de la classe positive
                metrics['auc_roc'] = roc_auc_score(y_true, y_prob)
            except Exception:
                metrics['auc_roc'] = 0.0
        
        # Matrice de confusion
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        return metrics
    
    def evaluate_regression(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Évalue un modèle de régression.
        
        Args:
            y_true: Vraies valeurs
            y_pred: Prédictions
            
        Returns:
            Dictionnaire des métriques
        """
        metrics = {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }
        
        # MAPE (Mean Absolute Percentage Error)
        try:
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            metrics['mape'] = mape if not np.isnan(mape) and not np.isinf(mape) else 0.0
        except:
            metrics['mape'] = 0.0
            
        return metrics
    
    def evaluate_timeseries(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Évalue un modèle de série temporelle.
        
        Args:
            y_true: Vraies valeurs
            y_pred: Prédictions
            
        Returns:
            Dictionnaire des métriques
        """
        metrics = self.evaluate_regression(y_true, y_pred)
        
        # Métriques spécifiques aux séries temporelles
        try:
            # Directional Accuracy
            if len(y_true) > 1:
                true_direction = np.diff(y_true) > 0
                pred_direction = np.diff(y_pred) > 0
                directional_accuracy = np.mean(true_direction == pred_direction)
                metrics['directional_accuracy'] = directional_accuracy
            
            # Theil's U statistic
            if np.sum(y_true**2) > 0:
                theil_u = np.sqrt(np.mean((y_pred - y_true)**2)) / np.sqrt(np.mean(y_true**2))
                metrics['theil_u'] = theil_u if not np.isnan(theil_u) else 0.0
                
        except Exception:
            pass
            
        return metrics
    
    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Retourne l'importance des features si disponible.
        
        Returns:
            DataFrame avec l'importance des features ou None
        """
        if not self.is_trained or self.feature_names is None:
            return None
            
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            return importance_df
        elif hasattr(self.model, 'coef_'):
            # Pour les modèles linéaires
            coef = self.model.coef_
            if coef.ndim > 1:
                coef = np.abs(coef).mean(axis=0)
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': np.abs(coef)
            }).sort_values('importance', ascending=False)
            return importance_df
            
        return None
    
    def save_model(self, filepath: str) -> None:
        """
        Sauvegarde le modèle.
        
        Args:
            filepath: Chemin de sauvegarde
        """
        import joblib
        
        model_data = {
            'model': self.model,
            'model_name': self.model_name,
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'scaler': self.scaler,
            'training_metrics': self.training_metrics,
            'validation_metrics': self.validation_metrics
        }
        
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str) -> None:
        """
        Charge un modèle sauvegardé.
        
        Args:
            filepath: Chemin du modèle à charger
        """
        import joblib
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.model_name = model_data['model_name']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        self.feature_names = model_data['feature_names']
        self.target_name = model_data['target_name']
        self.scaler = model_data['scaler']
        self.training_metrics = model_data['training_metrics']
        self.validation_metrics = model_data['validation_metrics']
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retourne les informations du modèle.
        
        Returns:
            Dictionnaire avec les informations du modèle
        """
        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'feature_count': len(self.feature_names) if self.feature_names else 0,
            'target_name': self.target_name,
            'training_metrics': self.training_metrics,
            'validation_metrics': self.validation_metrics
        }