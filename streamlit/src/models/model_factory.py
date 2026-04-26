from typing import Dict, Any, List, Optional, Type
from .base_model import BaseModel
from .classical_models import ClassicalModels, MaintenancePredictiveModel, ProductionForecastModel, WaterInjectionOptimizer
from .prophet_models import ProphetModels, ProductionProphetModel
from .xgboost_models import XGBoostModels, XGBoostMaintenanceModel, XGBoostProductionModel
from .model_ensemble import ModelEnsemble
import warnings
warnings.filterwarnings('ignore')

class ModelFactory:
    """Factory pour créer et gérer les différents types de modèles."""
    
    # Registre des modèles disponibles
    AVAILABLE_MODELS = {
        'maintenance_predictive': {
            'random_forest': {
                'class': MaintenancePredictiveModel,
                'params': {'algorithm': 'random_forest'},
                'description': 'Random Forest pour maintenance prédictive',
                'type': 'classification',
                'category': 'classical'
            },
            'gradient_boosting': {
                'class': MaintenancePredictiveModel,
                'params': {'algorithm': 'gradient_boosting'},
                'description': 'Gradient Boosting pour maintenance prédictive',
                'type': 'classification',
                'category': 'classical'
            },
            'xgboost': {
                'class': XGBoostMaintenanceModel,
                'params': {},
                'description': 'XGBoost pour maintenance prédictive',
                'type': 'classification',
                'category': 'xgboost'
            }
        },
        'production_forecast': {
            'random_forest': {
                'class': ProductionForecastModel,
                'params': {'algorithm': 'random_forest'},
                'description': 'Random Forest pour prévision de production',
                'type': 'regression',
                'category': 'classical'
            },
            'gradient_boosting': {
                'class': ProductionForecastModel,
                'params': {'algorithm': 'gradient_boosting'},
                'description': 'Gradient Boosting pour prévision de production',
                'type': 'regression',
                'category': 'classical'
            },
            'xgboost': {
                'class': XGBoostProductionModel,
                'params': {},
                'description': 'XGBoost pour prévision de production',
                'type': 'regression',
                'category': 'xgboost'
            },
            'prophet': {
                'class': ProductionProphetModel,
                'params': {'algorithm': 'prophet'},
                'description': 'Prophet pour prévision de production',
                'type': 'timeseries',
                'category': 'prophet'
            },
            'neuralprophet': {
                'class': ProductionProphetModel,
                'params': {'algorithm': 'neuralprophet'},
                'description': 'NeuralProphet pour prévision de production',
                'type': 'timeseries',
                'category': 'prophet'
            }
        },
        'water_injection': {
            'random_forest': {
                'class': WaterInjectionOptimizer,
                'params': {'algorithm': 'random_forest'},
                'description': 'Random Forest pour optimisation injection d\'eau',
                'type': 'regression',
                'category': 'classical'
            },
            'gradient_boosting': {
                'class': WaterInjectionOptimizer,
                'params': {'algorithm': 'gradient_boosting'},
                'description': 'Gradient Boosting pour optimisation injection d\'eau',
                'type': 'regression',
                'category': 'classical'
            },
            'xgboost': {
                'class': XGBoostModels,
                'params': {'model_type': 'regression'},
                'description': 'XGBoost pour optimisation injection d\'eau',
                'type': 'regression',
                'category': 'xgboost'
            }
        },
        'general': {
            'random_forest_classification': {
                'class': ClassicalModels,
                'params': {'algorithm': 'random_forest', 'model_type': 'classification'},
                'description': 'Random Forest Classification',
                'type': 'classification',
                'category': 'classical'
            },
            'random_forest_regression': {
                'class': ClassicalModels,
                'params': {'algorithm': 'random_forest', 'model_type': 'regression'},
                'description': 'Random Forest Regression',
                'type': 'regression',
                'category': 'classical'
            },
            'gradient_boosting_classification': {
                'class': ClassicalModels,
                'params': {'algorithm': 'gradient_boosting', 'model_type': 'classification'},
                'description': 'Gradient Boosting Classification',
                'type': 'classification',
                'category': 'classical'
            },
            'gradient_boosting_regression': {
                'class': ClassicalModels,
                'params': {'algorithm': 'gradient_boosting', 'model_type': 'regression'},
                'description': 'Gradient Boosting Regression',
                'type': 'regression',
                'category': 'classical'
            },
            'xgboost_classification': {
                'class': XGBoostModels,
                'params': {'model_type': 'classification'},
                'description': 'XGBoost Classification',
                'type': 'classification',
                'category': 'xgboost'
            },
            'xgboost_regression': {
                'class': XGBoostModels,
                'params': {'model_type': 'regression'},
                'description': 'XGBoost Regression',
                'type': 'regression',
                'category': 'xgboost'
            },
            'prophet_timeseries': {
                'class': ProphetModels,
                'params': {'algorithm': 'prophet'},
                'description': 'Prophet Time Series',
                'type': 'timeseries',
                'category': 'prophet'
            },
            'neuralprophet_timeseries': {
                'class': ProphetModels,
                'params': {'algorithm': 'neuralprophet'},
                'description': 'NeuralProphet Time Series',
                'type': 'timeseries',
                'category': 'prophet'
            }
        }
    }
    
    @classmethod
    def create_model(cls, use_case: str, algorithm: str, **kwargs) -> BaseModel:
        """
        Crée un modèle selon le cas d'usage et l'algorithme spécifiés.
        
        Args:
            use_case: Cas d'usage ('maintenance_predictive', 'production_forecast', 'water_injection', 'general')
            algorithm: Algorithme à utiliser
            **kwargs: Arguments supplémentaires pour le modèle
            
        Returns:
            Instance du modèle
            
        Raises:
            ValueError: Si le cas d'usage ou l'algorithme n'est pas supporté
        """
        if use_case not in cls.AVAILABLE_MODELS:
            raise ValueError(f"Cas d'usage non supporté: {use_case}. Disponibles: {list(cls.AVAILABLE_MODELS.keys())}")
        
        use_case_models = cls.AVAILABLE_MODELS[use_case]
        
        if algorithm not in use_case_models:
            raise ValueError(f"Algorithme non supporté pour {use_case}: {algorithm}. Disponibles: {list(use_case_models.keys())}")
        
        model_config = use_case_models[algorithm]
        model_class = model_config['class']
        model_params = model_config['params'].copy()
        model_params.update(kwargs)
        
        try:
            return model_class(**model_params)
        except Exception as e:
            # Vérifier si c'est un problème de dépendance manquante
            if "not installed" in str(e) or "ImportError" in str(type(e).__name__):
                raise ImportError(f"Dépendance manquante pour {algorithm}: {str(e)}")
            else:
                raise ValueError(f"Erreur lors de la création du modèle {algorithm}: {str(e)}")
    
    @classmethod
    def get_available_models(cls, use_case: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Dict]:
        """
        Retourne la liste des modèles disponibles.
        
        Args:
            use_case: Filtrer par cas d'usage (optionnel)
            category: Filtrer par catégorie ('classical', 'xgboost', 'prophet') (optionnel)
            
        Returns:
            Dictionnaire des modèles disponibles
        """
        if use_case is not None:
            if use_case not in cls.AVAILABLE_MODELS:
                return {}
            models = {use_case: cls.AVAILABLE_MODELS[use_case]}
        else:
            models = cls.AVAILABLE_MODELS.copy()
        
        if category is not None:
            filtered_models = {}
            for uc, uc_models in models.items():
                filtered_uc_models = {
                    alg: config for alg, config in uc_models.items()
                    if config['category'] == category
                }
                if filtered_uc_models:
                    filtered_models[uc] = filtered_uc_models
            models = filtered_models
        
        return models
    
    @classmethod
    def get_model_info(cls, use_case: str, algorithm: str) -> Dict[str, Any]:
        """
        Retourne les informations d'un modèle spécifique.
        
        Args:
            use_case: Cas d'usage
            algorithm: Algorithme
            
        Returns:
            Dictionnaire avec les informations du modèle
        """
        if use_case not in cls.AVAILABLE_MODELS:
            raise ValueError(f"Cas d'usage non supporté: {use_case}")
        
        if algorithm not in cls.AVAILABLE_MODELS[use_case]:
            raise ValueError(f"Algorithme non supporté: {algorithm}")
        
        return cls.AVAILABLE_MODELS[use_case][algorithm].copy()
    
    @classmethod
    def check_dependencies(cls) -> Dict[str, bool]:
        """
        Vérifie la disponibilité des dépendances pour chaque catégorie de modèles.
        
        Returns:
            Dictionnaire indiquant la disponibilité de chaque catégorie
        """
        dependencies = {
            'classical': True,  # sklearn est toujours disponible
            'xgboost': False,
            'prophet': False,
            'neuralprophet': False
        }
        
        # Vérifier XGBoost
        try:
            import xgboost
            dependencies['xgboost'] = True
        except ImportError:
            pass
        
        # Vérifier Prophet
        try:
            from prophet import Prophet
            dependencies['prophet'] = True
        except ImportError:
            pass
        
        # Vérifier NeuralProphet
        try:
            from neuralprophet import NeuralProphet
            dependencies['neuralprophet'] = True
        except ImportError:
            pass
        
        return dependencies
    
    @classmethod
    def get_recommendations(cls, use_case: str, data_size: int, has_seasonality: bool = False, 
                          needs_interpretability: bool = False) -> List[str]:
        """
        Recommande des algorithmes selon le contexte.
        
        Args:
            use_case: Cas d'usage
            data_size: Taille du dataset
            has_seasonality: Si les données ont de la saisonnalité
            needs_interpretability: Si l'interprétabilité est importante
            
        Returns:
            Liste des algorithmes recommandés par ordre de préférence
        """
        if use_case not in cls.AVAILABLE_MODELS:
            return []
        
        recommendations = []
        dependencies = cls.check_dependencies()
        
        # Recommandations basées sur le cas d'usage
        if use_case == 'maintenance_predictive':
            if data_size > 10000 and dependencies['xgboost']:
                recommendations.append('xgboost')
            if needs_interpretability:
                recommendations.append('random_forest')
            recommendations.append('gradient_boosting')
            if 'random_forest' not in recommendations:
                recommendations.append('random_forest')
        
        elif use_case == 'production_forecast':
            if has_seasonality:
                if dependencies['prophet']:
                    recommendations.append('prophet')
                if dependencies['neuralprophet']:
                    recommendations.append('neuralprophet')
            
            if data_size > 5000 and dependencies['xgboost']:
                recommendations.append('xgboost')
            
            recommendations.extend(['gradient_boosting', 'random_forest'])
        
        elif use_case == 'water_injection':
            if data_size > 5000 and dependencies['xgboost']:
                recommendations.append('xgboost')
            recommendations.extend(['gradient_boosting', 'random_forest'])
        
        # Filtrer les doublons tout en préservant l'ordre
        seen = set()
        filtered_recommendations = []
        for rec in recommendations:
            if rec not in seen and rec in cls.AVAILABLE_MODELS[use_case]:
                seen.add(rec)
                filtered_recommendations.append(rec)
        
        return filtered_recommendations
    
    @classmethod
    def create_ensemble(cls, use_case: str, algorithms: List[str], **kwargs) -> 'ModelEnsemble':
        """
        Crée un ensemble de modèles.
        
        Args:
            use_case: Cas d'usage
            algorithms: Liste des algorithmes à utiliser
            **kwargs: Arguments supplémentaires
            
        Returns:
            Instance de ModelEnsemble
        """
        models = []
        for algorithm in algorithms:
            try:
                model = cls.create_model(use_case, algorithm, **kwargs)
                models.append((algorithm, model))
            except Exception as e:
                print(f"Impossible de créer le modèle {algorithm}: {e}")
        
        if not models:
            raise ValueError("Aucun modèle n'a pu être créé pour l'ensemble.")
        
        return ModelEnsemble(models, use_case)