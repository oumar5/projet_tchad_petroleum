#!/usr/bin/env python3
"""
Tests pour les modèles ML
Vérifie l'entraînement, les métriques et la qualité des prédictions
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

class TestModels(unittest.TestCase):
    """Tests pour les modèles ML."""
    
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
            self.train_data = pd.DataFrame()
        
        self.evaluator = ModelEvaluator()
    
    def _test_model_safe(self, algorithm):
        """Teste un modèle de façon sécurisée."""
        if self.train_data.empty:
            self.skipTest(f"Pas de données pour tester {algorithm}")
        
        print(f"\n🧪 Test {algorithm.upper()}...")
        
        try:
            # Création du modèle
            model = ModelFactory.create_model('production_forecast', algorithm)
            self.assertIsNotNone(model, f"Le modèle {algorithm} doit être créé")
            
            # Préparation des features
            if hasattr(model, 'prepare_time_series_features'):
                prepared_data = model.prepare_time_series_features(self.train_data, self.target_col)
            elif hasattr(model, 'prepare_production_features'):
                prepared_data = model.prepare_production_features(self.train_data, self.target_col)
            else:
                prepared_data = self.train_data.copy()
            
            self.assertFalse(prepared_data.empty, f"Les données préparées ne doivent pas être vides pour {algorithm}")
            print(f"   📊 Features préparées: {prepared_data.shape}")
            
            # Préparation X, y
            X, y = model.prepare_data(prepared_data, self.target_col)
            
            # Vérifications de base
            self.assertIsInstance(X, pd.DataFrame, "X doit être un DataFrame")
            self.assertIsInstance(y, pd.Series, "y doit être une Series")
            self.assertEqual(len(X), len(y), "X et y doivent avoir la même longueur")
            self.assertGreater(len(X), 10, f"Pas assez de données pour {algorithm}")
            
            print(f"   📊 Données finales: X{X.shape}, y{y.shape}")
            
            # Vérification des NaN
            nan_x = X.isnull().sum().sum()
            nan_y = y.isnull().sum()
            self.assertEqual(nan_x, 0, f"X ne doit pas contenir de NaN pour {algorithm}")
            self.assertEqual(nan_y, 0, f"y ne doit pas contenir de NaN pour {algorithm}")
            
            # Vérification des valeurs infinies
            inf_x = np.isinf(X.select_dtypes(include=[np.number])).sum().sum()
            inf_y = np.isinf(y).sum()
            self.assertEqual(inf_x, 0, f"X ne doit pas contenir de valeurs infinies pour {algorithm}")
            self.assertEqual(inf_y, 0, f"y ne doit pas contenir de valeurs infinies pour {algorithm}")
            
            print(f"   ✅ Données validées (0 NaN, 0 Inf)")
            
            # Entraînement
            start_time = datetime.now()
            train_results = model.train(X, y, test_size=0.2)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Vérifications des résultats d'entraînement
            self.assertIsInstance(train_results, dict, "train_results doit être un dictionnaire")
            self.assertIn('X_test', train_results, "train_results doit contenir X_test")
            self.assertIn('y_test', train_results, "train_results doit contenir y_test")
            self.assertIn('y_pred', train_results, "train_results doit contenir y_pred")
            
            X_test = train_results['X_test']
            y_test = train_results['y_test']
            y_pred = train_results['y_pred']
            
            # Vérifications des prédictions
            self.assertIsNotNone(y_pred, "Les prédictions ne doivent pas être None")
            self.assertGreater(len(y_pred), 0, "Les prédictions ne doivent pas être vides")
            self.assertEqual(len(y_test), len(y_pred), "y_test et y_pred doivent avoir la même longueur")
            
            # Vérifier que les prédictions ne sont pas toutes identiques
            unique_predictions = len(np.unique(y_pred))
            self.assertGreater(unique_predictions, 1, f"Les prédictions de {algorithm} ne doivent pas être toutes identiques")
            
            print(f"   🚀 Entraînement réussi en {duration:.2f}s")
            print(f"   🎯 Prédictions uniques: {unique_predictions}")
            
            # Évaluation
            metrics = self.evaluator.evaluate_model(model, X_test, y_test, algorithm)
            
            # Vérifications des métriques
            self.assertIsInstance(metrics, dict, "Les métriques doivent être un dictionnaire")
            self.assertIn('mse', metrics, "Les métriques doivent contenir MSE")
            self.assertIn('rmse', metrics, "Les métriques doivent contenir RMSE")
            self.assertIn('mae', metrics, "Les métriques doivent contenir MAE")
            self.assertIn('r2', metrics, "Les métriques doivent contenir R²")
            
            mse = metrics['mse']
            rmse = metrics['rmse']
            mae = metrics['mae']
            r2 = metrics['r2']
            
            # Vérifications de cohérence des métriques
            self.assertGreaterEqual(mse, 0, "MSE doit être positif")
            self.assertGreaterEqual(rmse, 0, "RMSE doit être positif")
            self.assertGreaterEqual(mae, 0, "MAE doit être positif")
            self.assertAlmostEqual(rmse, np.sqrt(mse), places=2, msg="RMSE doit être la racine de MSE")
            
            # Vérifications de plausibilité
            y_mean = np.mean(y_test)
            y_std = np.std(y_test)
            
            # RMSE ne doit pas être excessivement grand par rapport à l'écart-type
            rmse_ratio = rmse / y_std if y_std > 0 else float('inf')
            self.assertLess(rmse_ratio, 10, f"RMSE trop élevé pour {algorithm} (ratio: {rmse_ratio:.2f})")
            
            # MAE ne doit pas être plus grand que RMSE
            self.assertLessEqual(mae, rmse, "MAE doit être <= RMSE")
            
            print(f"   📈 MSE: {mse:.2f}")
            print(f"   📈 RMSE: {rmse:.2f}")
            print(f"   📈 MAE: {mae:.2f}")
            print(f"   📈 R²: {r2:.4f}")
            
            # Évaluation de la qualité
            if r2 > 0.7:
                quality = "EXCELLENT"
            elif r2 > 0.5:
                quality = "BON"
            elif r2 > 0.2:
                quality = "ACCEPTABLE"
            elif r2 > 0:
                quality = "FAIBLE"
            else:
                quality = "SURAPPRENTISSAGE"
            
            print(f"   🎯 Qualité: {quality}")
            
            # Test de prédiction sur nouvelles données
            if len(X) > len(X_test):
                # Prendre quelques échantillons pour test
                sample_X = X.head(5)
                predictions = model.predict(sample_X)
                
                self.assertIsNotNone(predictions, "Les prédictions sur nouvelles données ne doivent pas être None")
                self.assertEqual(len(predictions), len(sample_X), "Nombre de prédictions incorrect")
                
                # Vérifier que les prédictions sont des nombres valides
                self.assertFalse(np.any(np.isnan(predictions)), "Les prédictions ne doivent pas contenir de NaN")
                self.assertFalse(np.any(np.isinf(predictions)), "Les prédictions ne doivent pas contenir d'infinis")
                
                print(f"   🔮 Test prédiction: ✅ ({len(predictions)} prédictions)")
            
            return {
                'model': model,
                'metrics': metrics,
                'duration': duration,
                'quality': quality,
                'data_shape': X.shape
            }
            
        except Exception as e:
            self.fail(f"Erreur lors du test de {algorithm}: {str(e)}")
    
    def test_random_forest(self):
        """Test du modèle Random Forest."""
        result = self._test_model_safe('random_forest')
        self.assertIsNotNone(result, "Random Forest doit s'entraîner avec succès")
    
    def test_gradient_boosting(self):
        """Test du modèle Gradient Boosting."""
        result = self._test_model_safe('gradient_boosting')
        self.assertIsNotNone(result, "Gradient Boosting doit s'entraîner avec succès")
    
    def test_model_factory(self):
        """Test de la factory de modèles."""
        print("\n🧪 Test ModelFactory...")
        
        # Test de création de modèles valides
        valid_algorithms = ['random_forest', 'gradient_boosting']
        
        for algorithm in valid_algorithms:
            try:
                model = ModelFactory.create_model('production_forecast', algorithm)
                self.assertIsNotNone(model, f"ModelFactory doit créer {algorithm}")
                print(f"   ✅ {algorithm}: Créé avec succès")
            except Exception as e:
                self.fail(f"Erreur création {algorithm}: {e}")
        
        # Test de création avec algorithme invalide
        with self.assertRaises((ValueError, KeyError)):
            ModelFactory.create_model('production_forecast', 'algorithme_inexistant')
        
        print(f"   ✅ Gestion d'erreur pour algorithme invalide: OK")
    
    def test_model_evaluator(self):
        """Test de l'évaluateur de modèles."""
        print("\n🧪 Test ModelEvaluator...")
        
        if self.train_data.empty:
            self.skipTest("Pas de données pour tester l'évaluateur")
        
        # Créer des données de test simples
        n_samples = 100
        y_true = np.random.normal(1000, 200, n_samples)
        y_pred = y_true + np.random.normal(0, 50, n_samples)  # Prédictions avec un peu de bruit
        
        # Créer un modèle factice
        model = ModelFactory.create_model('production_forecast', 'random_forest')
        
        # Tester l'évaluation
        metrics = self.evaluator.evaluate_model(model, None, y_true, 'test_model', y_pred=y_pred)
        
        # Vérifications
        self.assertIsInstance(metrics, dict, "Les métriques doivent être un dictionnaire")
        
        required_metrics = ['mse', 'rmse', 'mae', 'r2']
        for metric in required_metrics:
            self.assertIn(metric, metrics, f"Métrique {metric} manquante")
            self.assertIsInstance(metrics[metric], (int, float), f"Métrique {metric} doit être numérique")
        
        # Vérifier la cohérence
        self.assertAlmostEqual(metrics['rmse'], np.sqrt(metrics['mse']), places=2)
        self.assertGreaterEqual(metrics['r2'], 0, "R² doit être positif pour des prédictions correctes")
        
        print(f"   ✅ Métriques calculées correctement")
        print(f"   📊 R² test: {metrics['r2']:.4f}")

def run_model_tests():
    """Lance tous les tests de modèles."""
    print("="*60)
    print("🧪 TESTS DES MODÈLES ML")
    print("="*60)
    
    # Créer une suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestModels)
    
    # Lancer les tests avec un runner personnalisé
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("📋 RÉSUMÉ DES TESTS MODÈLES")
    print("="*60)
    
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
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_model_tests()
    sys.exit(0 if success else 1)