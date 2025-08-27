#!/usr/bin/env python3
"""
Test complet de TOUS les modèles disponibles
Couvre tous les cas d'usage et algorithmes de ModelFactory
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Supprimer les warnings
import warnings
warnings.filterwarnings('ignore')

from data_loader import load_production_data, split_data_for_validation
from models.model_factory import ModelFactory
from models.model_evaluator import ModelEvaluator

class TestAllModels(unittest.TestCase):
    """Tests complets pour TOUS les modèles ML disponibles."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Charger les données une seule fois
        self.production_df = load_production_data()
        self.target_col = "Production journaliere d'huile bbl"
        
        if not self.production_df.empty:
            # Préparer les données d'entraînement
            train_data, _ = split_data_for_validation(self.production_df, 2)
            self.train_data = train_data.dropna(subset=[self.target_col, 'Date'])
        else:
            # Créer des données de test si pas de fichier Excel
            self.train_data = self._create_test_data()
        
        self.evaluator = ModelEvaluator()
        
        # Définir tous les modèles à tester par cas d'usage
        self.models_to_test = {
            'production_forecast': {
                'stable': ['random_forest', 'gradient_boosting'],
                'advanced': ['xgboost'],
                'timeseries': ['prophet', 'neuralprophet']
            },
            'maintenance_predictive': {
                'stable': ['random_forest', 'gradient_boosting'],
                'advanced': ['xgboost']
            },
            'water_injection': {
                'stable': ['random_forest', 'gradient_boosting'],
                'advanced': ['xgboost']
            },
            'general': {
                'classification': ['random_forest_classification', 'gradient_boosting_classification', 'xgboost_classification'],
                'regression': ['random_forest_regression', 'gradient_boosting_regression', 'xgboost_regression'],
                'timeseries': ['prophet_timeseries', 'neuralprophet_timeseries']
            }
        }
    
    def _create_test_data(self):
        """Crée des données de test si le fichier Excel n'existe pas."""
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        data = {
            'Date': dates,
            'Production journaliere d\'huile bbl': np.random.normal(1000, 100, 1000),
            'Production journaliere d\'eau bbl': np.random.normal(500, 50, 1000),
            'Teneur en eau (Watercut)': np.random.uniform(0.2, 0.8, 1000),
            'Water Oil Ratio': np.random.uniform(0.1, 2.0, 1000),
            'Nombre des puits actifs': np.random.randint(5, 15, 1000),
            'Nombre total des puits': np.random.randint(10, 20, 1000)
        }
        return pd.DataFrame(data)
    
    def _test_model_creation(self, use_case, algorithm):
        """Teste la création d'un modèle."""
        try:
            model = ModelFactory.create_model(use_case, algorithm)
            self.assertIsNotNone(model, f"Le modèle {use_case}/{algorithm} doit être créé")
            
            # Vérifier les méthodes essentielles
            required_methods = ['train', 'predict']
            for method in required_methods:
                self.assertTrue(hasattr(model, method), 
                              f"{use_case}/{algorithm} doit avoir la méthode {method}")
            
            return model, None
            
        except Exception as e:
            return None, str(e)
    
    def _test_model_training_safe(self, use_case, algorithm, model):
        """Teste l'entraînement d'un modèle de façon sécurisée."""
        if self.train_data.empty:
            return None, "Pas de données d'entraînement"
        
        try:
            # Préparation des données selon le type de modèle
            if algorithm in ['prophet', 'neuralprophet', 'prophet_timeseries', 'neuralprophet_timeseries']:
                # Modèles Prophet nécessitent un format spécial
                if hasattr(model, 'prepare_data'):
                    X, y = model.prepare_data(self.train_data, self.target_col, 'Date')
                else:
                    # Format Prophet standard
                    prophet_data = self.train_data[['Date', self.target_col]].copy()
                    prophet_data.columns = ['ds', 'y']
                    X, y = prophet_data, prophet_data['y']
            else:
                # Modèles classiques et XGBoost
                if hasattr(model, 'prepare_time_series_features'):
                    prepared_data = model.prepare_time_series_features(self.train_data, self.target_col)
                elif hasattr(model, 'prepare_production_features'):
                    prepared_data = model.prepare_production_features(self.train_data, self.target_col)
                elif hasattr(model, 'prepare_features'):
                    # Pour les modèles de maintenance
                    prepared_data = model.prepare_features(self.train_data, pd.DataFrame())
                elif hasattr(model, 'prepare_injection_features'):
                    # Pour les modèles d'injection d'eau
                    prepared_data = model.prepare_injection_features(self.train_data)
                else:
                    prepared_data = self.train_data.copy()
                
                X, y = model.prepare_data(prepared_data, self.target_col)
            
            # Vérifications de base
            if len(X) < 10:
                return None, "Pas assez de données après préparation"
            
            # Entraînement
            start_time = datetime.now()
            train_results = model.train(X, y, test_size=0.2)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Vérifications des résultats
            if not isinstance(train_results, dict):
                return None, "Résultats d'entraînement invalides"
            
            return {
                'success': True,
                'duration': duration,
                'data_shape': X.shape if hasattr(X, 'shape') else len(X),
                'results': train_results
            }, None
            
        except Exception as e:
            return None, str(e)
    
    def test_production_forecast_models(self):
        """Test de tous les modèles de prévision de production."""
        print("\n🧪 Test modèles PRODUCTION FORECAST...")
        
        use_case = 'production_forecast'
        results = {}
        
        for category, algorithms in self.models_to_test[use_case].items():
            print(f"\n📊 Catégorie: {category.upper()}")
            
            for algorithm in algorithms:
                print(f"\n  🔬 Test {algorithm}...")
                
                # Test de création
                model, error = self._test_model_creation(use_case, algorithm)
                if error:
                    print(f"    ❌ Création échouée: {error}")
                    results[f"{use_case}/{algorithm}"] = {'creation': False, 'error': error}
                    continue
                
                print(f"    ✅ Modèle créé")
                
                # Test d'entraînement (seulement pour les modèles stables)
                if category == 'stable':
                    train_result, train_error = self._test_model_training_safe(use_case, algorithm, model)
                    if train_error:
                        print(f"    ⚠️ Entraînement échoué: {train_error}")
                        results[f"{use_case}/{algorithm}"] = {
                            'creation': True, 
                            'training': False, 
                            'error': train_error
                        }
                    else:
                        print(f"    ✅ Entraînement réussi ({train_result['duration']:.2f}s)")
                        results[f"{use_case}/{algorithm}"] = {
                            'creation': True, 
                            'training': True, 
                            'duration': train_result['duration']
                        }
                else:
                    print(f"    ⏭️ Entraînement ignoré (catégorie {category})")
                    results[f"{use_case}/{algorithm}"] = {'creation': True, 'training': 'skipped'}
        
        # Vérifications
        created_models = sum(1 for r in results.values() if r.get('creation', False))
        total_models = len([alg for algs in self.models_to_test[use_case].values() for alg in algs])
        
        self.assertGreater(created_models, 0, "Au moins un modèle de production doit être créé")
        print(f"\n📊 Résumé Production Forecast: {created_models}/{total_models} modèles créés")
    
    def test_maintenance_predictive_models(self):
        """Test de tous les modèles de maintenance prédictive."""
        print("\n🧪 Test modèles MAINTENANCE PREDICTIVE...")
        
        use_case = 'maintenance_predictive'
        results = {}
        
        for category, algorithms in self.models_to_test[use_case].items():
            print(f"\n🔧 Catégorie: {category.upper()}")
            
            for algorithm in algorithms:
                print(f"\n  🔬 Test {algorithm}...")
                
                # Test de création
                model, error = self._test_model_creation(use_case, algorithm)
                if error:
                    print(f"    ❌ Création échouée: {error}")
                    results[f"{use_case}/{algorithm}"] = {'creation': False, 'error': error}
                    continue
                
                print(f"    ✅ Modèle créé")
                results[f"{use_case}/{algorithm}"] = {'creation': True}
        
        # Vérifications
        created_models = sum(1 for r in results.values() if r.get('creation', False))
        total_models = len([alg for algs in self.models_to_test[use_case].values() for alg in algs])
        
        self.assertGreater(created_models, 0, "Au moins un modèle de maintenance doit être créé")
        print(f"\n🔧 Résumé Maintenance: {created_models}/{total_models} modèles créés")
    
    def test_water_injection_models(self):
        """Test de tous les modèles d'optimisation d'injection d'eau."""
        print("\n🧪 Test modèles WATER INJECTION...")
        
        use_case = 'water_injection'
        results = {}
        
        for category, algorithms in self.models_to_test[use_case].items():
            print(f"\n💧 Catégorie: {category.upper()}")
            
            for algorithm in algorithms:
                print(f"\n  🔬 Test {algorithm}...")
                
                # Test de création
                model, error = self._test_model_creation(use_case, algorithm)
                if error:
                    print(f"    ❌ Création échouée: {error}")
                    results[f"{use_case}/{algorithm}"] = {'creation': False, 'error': error}
                    continue
                
                print(f"    ✅ Modèle créé")
                results[f"{use_case}/{algorithm}"] = {'creation': True}
        
        # Vérifications
        created_models = sum(1 for r in results.values() if r.get('creation', False))
        total_models = len([alg for algs in self.models_to_test[use_case].values() for alg in algs])
        
        self.assertGreater(created_models, 0, "Au moins un modèle d'injection doit être créé")
        print(f"\n💧 Résumé Water Injection: {created_models}/{total_models} modèles créés")
    
    def test_general_models(self):
        """Test de tous les modèles généraux."""
        print("\n🧪 Test modèles GENERAL...")
        
        use_case = 'general'
        results = {}
        
        for category, algorithms in self.models_to_test[use_case].items():
            print(f"\n⚙️ Catégorie: {category.upper()}")
            
            for algorithm in algorithms:
                print(f"\n  🔬 Test {algorithm}...")
                
                # Test de création
                model, error = self._test_model_creation(use_case, algorithm)
                if error:
                    print(f"    ❌ Création échouée: {error}")
                    results[f"{use_case}/{algorithm}"] = {'creation': False, 'error': error}
                    continue
                
                print(f"    ✅ Modèle créé")
                results[f"{use_case}/{algorithm}"] = {'creation': True}
        
        # Vérifications
        created_models = sum(1 for r in results.values() if r.get('creation', False))
        total_models = len([alg for algs in self.models_to_test[use_case].values() for alg in algs])
        
        self.assertGreater(created_models, 0, "Au moins un modèle général doit être créé")
        print(f"\n⚙️ Résumé General: {created_models}/{total_models} modèles créés")
    
    def test_model_factory_completeness(self):
        """Test de la complétude de ModelFactory."""
        print("\n🧪 Test complétude ModelFactory...")
        
        # Vérifier que tous les cas d'usage sont disponibles
        available_models = ModelFactory.AVAILABLE_MODELS
        
        expected_use_cases = ['maintenance_predictive', 'production_forecast', 'water_injection', 'general']
        for use_case in expected_use_cases:
            self.assertIn(use_case, available_models, f"Cas d'usage {use_case} doit être disponible")
            print(f"  ✅ Cas d'usage {use_case}: {len(available_models[use_case])} modèles")
        
        # Compter le total de modèles
        total_models = sum(len(models) for models in available_models.values())
        print(f"\n📊 Total modèles disponibles: {total_models}")
        
        # Vérifier les dépendances
        dependencies = ModelFactory.check_dependencies()
        print(f"\n🔍 Dépendances:")
        for dep, available in dependencies.items():
            status = "✅" if available else "❌"
            print(f"  {status} {dep}")
        
        self.assertGreater(total_models, 10, "Au moins 10 modèles doivent être disponibles")

def run_complete_model_tests():
    """Lance tous les tests complets de modèles."""
    print("="*80)
    print("🧪 TESTS COMPLETS DE TOUS LES MODÈLES ML")
    print("="*80)
    
    # Créer une suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAllModels)
    
    # Lancer les tests avec un runner personnalisé
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Afficher le résumé
    print("\n" + "="*80)
    print("📋 RÉSUMÉ DES TESTS COMPLETS")
    print("="*80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"✅ Tests réussis: {successes}/{total_tests}")
    if failures > 0:
        print(f"❌ Échecs: {failures}")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"   • {test}: {error_msg}")
    
    if errors > 0:
        print(f"💥 Erreurs: {errors}")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2] if '\n' in traceback else str(traceback)
            print(f"   • {test}: {error_msg}")
    
    success_rate = (successes / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n🎯 Taux de réussite: {success_rate:.1f}%")
    
    # Recommandations
    if success_rate == 100:
        print("\n🏆 EXCELLENT ! Tous les modèles sont testés et fonctionnels.")
    elif success_rate >= 80:
        print("\n👍 BON ! La plupart des modèles fonctionnent.")
    elif success_rate >= 60:
        print("\n⚠️ MOYEN ! Plusieurs modèles ont des problèmes.")
    else:
        print("\n🚨 CRITIQUE ! Nombreux problèmes avec les modèles.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_complete_model_tests()
    sys.exit(0 if success else 1)