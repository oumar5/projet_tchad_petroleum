import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .base_model import BaseModel
import warnings
warnings.filterwarnings('ignore')

class ModelEnsemble:
    """Classe pour gérer un ensemble de modèles."""
    
    def __init__(self, models: List[tuple], use_case: str):
        """
        Initialise l'ensemble de modèles.
        
        Args:
            models: Liste de tuples (nom_algorithme, instance_modèle)
            use_case: Cas d'usage
        """
        self.models = dict(models)
        self.use_case = use_case
        self.is_trained = False
        self.ensemble_metrics = {}
        self.best_model = None
    
    def train_all(self, X, y, **kwargs) -> Dict[str, Dict]:
        """
        Entraîne tous les modèles de l'ensemble.
        
        Args:
            X: Features d'entraînement
            y: Cible d'entraînement
            **kwargs: Arguments supplémentaires
            
        Returns:
            Dictionnaire avec les résultats de tous les modèles
        """
        results = {}
        
        for name, model in self.models.items():
            try:
                print(f"Entraînement du modèle {name}...")
                result = model.train(X, y, **kwargs)
                results[name] = result
                
                # Stocker les métriques
                self.ensemble_metrics[name] = result['validation_metrics']
                
            except Exception as e:
                print(f"Erreur lors de l'entraînement de {name}: {e}")
                results[name] = {'error': str(e)}
        
        # Déterminer le meilleur modèle
        self._find_best_model()
        self.is_trained = True
        
        return results
    
    def _find_best_model(self):
        """Détermine le meilleur modèle basé sur les métriques de validation."""
        if not self.ensemble_metrics:
            return
        
        best_score = float('-inf')
        best_name = None
        
        # Choisir la métrique selon le type de modèle
        metric_key = 'f1_score' if self.use_case == 'maintenance_predictive' else 'r2'
        
        for name, metrics in self.ensemble_metrics.items():
            if metric_key in metrics:
                score = metrics[metric_key]
                if score > best_score:
                    best_score = score
                    best_name = name
        
        if best_name:
            self.best_model = best_name
    
    def predict(self, X, use_best: bool = True, method: str = 'average'):
        """
        Fait des prédictions avec l'ensemble.
        
        Args:
            X: Features pour la prédiction
            use_best: Utiliser seulement le meilleur modèle
            method: Méthode d'agrégation ('average', 'voting', 'weighted')
            
        Returns:
            Prédictions agrégées
        """
        if not self.is_trained:
            raise ValueError("L'ensemble doit être entraîné avant de faire des prédictions.")
        
        if use_best and self.best_model:
            return self.models[self.best_model].predict(X)
        
        # Prédictions de tous les modèles
        predictions = {}
        for name, model in self.models.items():
            if model.is_trained:
                try:
                    predictions[name] = model.predict(X)
                except Exception as e:
                    print(f"Erreur de prédiction pour {name}: {e}")
        
        if not predictions:
            raise ValueError("Aucun modèle n'a pu faire de prédictions.")
        
        # Agrégation
        if method == 'average':
            return np.mean(list(predictions.values()), axis=0)
        elif method == 'voting':
            # Pour la classification, vote majoritaire
            from scipy import stats
            return stats.mode(list(predictions.values()), axis=0)[0][0]
        elif method == 'weighted':
            # Pondération basée sur les performances
            weights = []
            pred_values = []
            metric_key = 'f1_score' if self.use_case == 'maintenance_predictive' else 'r2'
            
            for name, pred in predictions.items():
                if name in self.ensemble_metrics and metric_key in self.ensemble_metrics[name]:
                    weight = self.ensemble_metrics[name][metric_key]
                    weights.append(weight)
                    pred_values.append(pred)
            
            if weights:
                weights = np.array(weights)
                weights = weights / weights.sum()  # Normaliser
                return np.average(pred_values, axis=0, weights=weights)
            else:
                return np.mean(list(predictions.values()), axis=0)
        
        return np.mean(list(predictions.values()), axis=0)
    
    def predict_proba(self, X, use_best: bool = True, method: str = 'average'):
        """
        Fait des prédictions de probabilité avec l'ensemble.
        
        Args:
            X: Features pour la prédiction
            use_best: Utiliser seulement le meilleur modèle
            method: Méthode d'agrégation
            
        Returns:
            Probabilités agrégées
        """
        if not self.is_trained:
            raise ValueError("L'ensemble doit être entraîné avant de faire des prédictions.")
        
        if use_best and self.best_model:
            return self.models[self.best_model].predict_proba(X)
        
        # Prédictions de probabilité de tous les modèles
        probabilities = {}
        for name, model in self.models.items():
            if model.is_trained and hasattr(model, 'predict_proba'):
                try:
                    prob = model.predict_proba(X)
                    if prob is not None:
                        probabilities[name] = prob
                except Exception as e:
                    print(f"Erreur de prédiction de probabilité pour {name}: {e}")
        
        if not probabilities:
            return None
        
        # Agrégation des probabilités
        if method == 'average':
            return np.mean(list(probabilities.values()), axis=0)
        elif method == 'weighted':
            weights = []
            prob_values = []
            metric_key = 'f1_score' if self.use_case == 'maintenance_predictive' else 'r2'
            
            for name, prob in probabilities.items():
                if name in self.ensemble_metrics and metric_key in self.ensemble_metrics[name]:
                    weight = self.ensemble_metrics[name][metric_key]
                    weights.append(weight)
                    prob_values.append(prob)
            
            if weights:
                weights = np.array(weights)
                weights = weights / weights.sum()
                return np.average(prob_values, axis=0, weights=weights)
            else:
                return np.mean(list(probabilities.values()), axis=0)
        
        return np.mean(list(probabilities.values()), axis=0)
    
    def get_model_comparison(self) -> Dict[str, Dict]:
        """
        Retourne une comparaison des performances de tous les modèles.
        
        Returns:
            Dictionnaire avec les métriques de tous les modèles
        """
        return self.ensemble_metrics.copy()
    
    def get_best_model(self) -> Optional[BaseModel]:
        """
        Retourne le meilleur modèle.
        
        Returns:
            Instance du meilleur modèle ou None
        """
        if self.best_model:
            return self.models[self.best_model]
        return None
    
    def get_best_model_name(self) -> Optional[str]:
        """
        Retourne le nom du meilleur modèle.
        
        Returns:
            Nom du meilleur modèle ou None
        """
        return self.best_model
    
    def get_model_names(self) -> List[str]:
        """
        Retourne la liste des noms de modèles dans l'ensemble.
        
        Returns:
            Liste des noms de modèles
        """
        return list(self.models.keys())
    
    def get_model(self, name: str) -> Optional[BaseModel]:
        """
        Retourne un modèle spécifique par son nom.
        
        Args:
            name: Nom du modèle
            
        Returns:
            Instance du modèle ou None
        """
        return self.models.get(name)
    
    def remove_model(self, name: str) -> bool:
        """
        Supprime un modèle de l'ensemble.
        
        Args:
            name: Nom du modèle à supprimer
            
        Returns:
            True si le modèle a été supprimé, False sinon
        """
        if name in self.models:
            del self.models[name]
            if name in self.ensemble_metrics:
                del self.ensemble_metrics[name]
            
            # Recalculer le meilleur modèle si nécessaire
            if self.best_model == name:
                self._find_best_model()
            
            return True
        return False
    
    def add_model(self, name: str, model: BaseModel) -> bool:
        """
        Ajoute un modèle à l'ensemble.
        
        Args:
            name: Nom du modèle
            model: Instance du modèle
            
        Returns:
            True si le modèle a été ajouté, False si le nom existe déjà
        """
        if name not in self.models:
            self.models[name] = model
            return True
        return False
    
    def get_ensemble_info(self) -> Dict[str, Any]:
        """
        Retourne des informations sur l'ensemble.
        
        Returns:
            Dictionnaire avec les informations de l'ensemble
        """
        return {
            'use_case': self.use_case,
            'model_count': len(self.models),
            'model_names': list(self.models.keys()),
            'is_trained': self.is_trained,
            'best_model': self.best_model,
            'has_metrics': bool(self.ensemble_metrics)
        }
    
    def save_ensemble(self, filepath: str):
        """
        Sauvegarde l'ensemble de modèles.
        
        Args:
            filepath: Chemin de sauvegarde
        """
        import joblib
        
        ensemble_data = {
            'models': self.models,
            'use_case': self.use_case,
            'ensemble_metrics': self.ensemble_metrics,
            'best_model': self.best_model,
            'is_trained': self.is_trained
        }
        
        joblib.dump(ensemble_data, filepath)
    
    @classmethod
    def load_ensemble(cls, filepath: str) -> 'ModelEnsemble':
        """
        Charge un ensemble de modèles depuis un fichier.
        
        Args:
            filepath: Chemin du fichier
            
        Returns:
            Instance de ModelEnsemble
        """
        import joblib
        
        ensemble_data = joblib.load(filepath)
        
        # Reconstruire l'ensemble
        models_list = [(name, model) for name, model in ensemble_data['models'].items()]
        ensemble = cls(models_list, ensemble_data['use_case'])
        
        ensemble.ensemble_metrics = ensemble_data['ensemble_metrics']
        ensemble.best_model = ensemble_data['best_model']
        ensemble.is_trained = ensemble_data['is_trained']
        
        return ensemble
    
    def cross_validate(self, X, y, cv: int = 5, **kwargs) -> Dict[str, Dict]:
        """
        Effectue une validation croisée sur tous les modèles de l'ensemble.
        
        Args:
            X: Features
            y: Cible
            cv: Nombre de folds
            **kwargs: Arguments supplémentaires
            
        Returns:
            Dictionnaire avec les résultats de validation croisée
        """
        from sklearn.model_selection import cross_val_score
        
        cv_results = {}
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'model') and model.model is not None:
                    # Utiliser le modèle sklearn sous-jacent
                    scoring = 'f1_weighted' if self.use_case == 'maintenance_predictive' else 'r2'
                    scores = cross_val_score(model.model, X, y, cv=cv, scoring=scoring)
                    
                    cv_results[name] = {
                        'scores': scores,
                        'mean': scores.mean(),
                        'std': scores.std(),
                        'min': scores.min(),
                        'max': scores.max()
                    }
                else:
                    cv_results[name] = {'error': 'Modèle non entraîné ou non compatible'}
                    
            except Exception as e:
                cv_results[name] = {'error': str(e)}
        
        return cv_results