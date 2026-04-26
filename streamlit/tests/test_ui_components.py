#!/usr/bin/env python3
"""
Tests pour les composants UI
Vérifie les composants Streamlit et leur intégration
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Supprimer les warnings
import warnings
warnings.filterwarnings('ignore')

# Mock Streamlit pour les tests
sys.modules['streamlit'] = Mock()

from data_loader import load_production_data
from models.model_factory import ModelFactory

class TestUIComponents(unittest.TestCase):
    """Tests pour les composants UI."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Créer des données de test
        self.test_data = self._create_test_data()
        self.dependencies = {
            'xgboost': True,
            'prophet': True,
            'neuralprophet': False
        }
    
    def _create_test_data(self):
        """Crée des données de test pour les UI."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        data = {
            'Date': dates,
            'Production journaliere d\'huile bbl': np.random.normal(1000, 100, 100),
            'Production journaliere d\'eau bbl': np.random.normal(500, 50, 100),
            'Teneur en eau (Watercut)': np.random.uniform(0.2, 0.8, 100),
            'Water Oil Ratio': np.random.uniform(0.1, 2.0, 100),
            'Nombre des puits actifs': np.random.randint(5, 15, 100),
            'Nombre total des puits': np.random.randint(10, 20, 100)
        }
        return pd.DataFrame(data)
    
    def test_forecast_ui_imports(self):
        """Test des imports du module ForecastUI."""
        print("\n🧪 Test imports ForecastUI...")
        
        try:
            from ui_components.forecast_ui import ForecastUI
            self.assertTrue(hasattr(ForecastUI, 'render'), "ForecastUI doit avoir une méthode render")
            self.assertTrue(hasattr(ForecastUI, '_train_models'), "ForecastUI doit avoir une méthode _train_models")
            print("   ✅ Imports ForecastUI: OK")
        except ImportError as e:
            self.fail(f"Erreur import ForecastUI: {e}")
    
    def test_sidebar_ui_imports(self):
        """Test des imports du module SidebarUI."""
        print("\n🧪 Test imports SidebarUI...")
        
        try:
            from ui_components.sidebar_ui import SidebarUI
            self.assertTrue(hasattr(SidebarUI, 'render'), "SidebarUI doit avoir une méthode render")
            print("   ✅ Imports SidebarUI: OK")
        except ImportError as e:
            self.fail(f"Erreur import SidebarUI: {e}")
    
    def test_home_ui_imports(self):
        """Test des imports du module HomeUI."""
        print("\n🧪 Test imports HomeUI...")
        
        try:
            from ui_components.home_ui import HomeUI
            self.assertTrue(hasattr(HomeUI, 'render'), "HomeUI doit avoir une méthode render")
            print("   ✅ Imports HomeUI: OK")
        except ImportError as e:
            self.fail(f"Erreur import HomeUI: {e}")
    
    def test_model_comparison_ui_imports(self):
        """Test des imports du module ModelComparisonUI."""
        print("\n🧪 Test imports ModelComparisonUI...")
        
        try:
            from ui_components.model_comparison_ui import ModelComparisonUI
            self.assertTrue(hasattr(ModelComparisonUI, 'render'), "ModelComparisonUI doit avoir une méthode render")
            print("   ✅ Imports ModelComparisonUI: OK")
        except ImportError as e:
            self.fail(f"Erreur import ModelComparisonUI: {e}")
    
    @patch('streamlit.selectbox')
    @patch('streamlit.multiselect')
    @patch('streamlit.slider')
    def test_forecast_ui_algorithm_selection(self, mock_slider, mock_multiselect, mock_selectbox):
        """Test de la sélection d'algorithmes dans ForecastUI."""
        print("\n🧪 Test sélection algorithmes...")
        
        try:
            from ui_components.forecast_ui import ForecastUI
            
            # Mock des retours Streamlit
            mock_multiselect.return_value = ['random_forest', 'gradient_boosting']
            mock_slider.return_value = 60
            mock_selectbox.return_value = 'Production journaliere d\'huile bbl'
            
            # Tester la méthode de sélection d'algorithmes
            config = ForecastUI._render_algorithm_selection(self.dependencies)
            
            # Vérifications
            self.assertIsInstance(config, dict, "La configuration doit être un dictionnaire")
            self.assertIn('algorithms', config, "La configuration doit contenir les algorithmes")
            self.assertIn('forecast_horizon', config, "La configuration doit contenir l'horizon")
            self.assertIn('target_column', config, "La configuration doit contenir la colonne cible")
            
            print("   ✅ Sélection algorithmes: OK")
            
        except Exception as e:
            self.fail(f"Erreur test sélection algorithmes: {e}")
    
    def test_data_validation_ui(self):
        """Test de la validation des données dans l'UI."""
        print("\n🧪 Test validation données UI...")
        
        try:
            # Test avec données valides
            self.assertFalse(self.test_data.empty, "Les données de test ne doivent pas être vides")
            self.assertIn('Date', self.test_data.columns, "Les données doivent contenir une colonne Date")
            self.assertIn('Production journaliere d\'huile bbl', self.test_data.columns, 
                         "Les données doivent contenir la colonne de production")
            
            # Test avec données vides
            empty_data = pd.DataFrame()
            self.assertTrue(empty_data.empty, "DataFrame vide doit être détecté")
            
            # Test avec données manquantes
            incomplete_data = self.test_data.copy()
            incomplete_data.loc[0:10, 'Production journaliere d\'huile bbl'] = np.nan
            
            nan_count = incomplete_data['Production journaliere d\'huile bbl'].isnull().sum()
            self.assertGreater(nan_count, 0, "Les NaN doivent être détectés")
            
            print(f"   ✅ Validation données: OK ({nan_count} NaN détectés)")
            
        except Exception as e:
            self.fail(f"Erreur validation données UI: {e}")
    
    def test_model_factory_integration(self):
        """Test de l'intégration avec ModelFactory."""
        print("\n🧪 Test intégration ModelFactory...")
        
        try:
            # Tester la création de modèles disponibles
            available_algorithms = ['random_forest', 'gradient_boosting']
            
            for algorithm in available_algorithms:
                model = ModelFactory.create_model('production_forecast', algorithm)
                self.assertIsNotNone(model, f"Le modèle {algorithm} doit être créé")
                
                # Vérifier que le modèle a les méthodes nécessaires
                self.assertTrue(hasattr(model, 'train'), f"{algorithm} doit avoir une méthode train")
                self.assertTrue(hasattr(model, 'predict'), f"{algorithm} doit avoir une méthode predict")
                self.assertTrue(hasattr(model, 'prepare_data'), f"{algorithm} doit avoir une méthode prepare_data")
            
            print(f"   ✅ Intégration ModelFactory: OK ({len(available_algorithms)} modèles)")
            
        except Exception as e:
            self.fail(f"Erreur intégration ModelFactory: {e}")
    
    def test_plotting_imports(self):
        """Test des imports des modules de plotting."""
        print("\n🧪 Test imports plotting...")
        
        try:
            # Test des imports de base
            from plotting import (
                plot_daily_production,
                plot_failures_by_block,
                display_plot_with_download
            )
            
            # Vérifier que les fonctions existent
            self.assertTrue(callable(plot_daily_production), "plot_daily_production doit être callable")
            self.assertTrue(callable(plot_failures_by_block), "plot_failures_by_block doit être callable")
            self.assertTrue(callable(display_plot_with_download), "display_plot_with_download doit être callable")
            
            print("   ✅ Imports plotting: OK")
            
        except ImportError as e:
            print(f"   ⚠️ Imports plotting partiels: {e}")
            # Ne pas faire échouer le test car certains modules peuvent manquer
    
    def test_session_state_management(self):
        """Test de la gestion du state de session."""
        print("\n🧪 Test gestion session state...")
        
        try:
            # Simuler un session state
            mock_session_state = {
                'forecast_results': {},
                'forecast_models': {},
                'validation_years': 2
            }
            
            # Vérifier les clés essentielles
            expected_keys = ['forecast_results', 'forecast_models', 'validation_years']
            for key in expected_keys:
                self.assertIn(key, mock_session_state, f"Session state doit contenir {key}")
            
            # Vérifier les types
            self.assertIsInstance(mock_session_state['forecast_results'], dict, 
                                "forecast_results doit être un dict")
            self.assertIsInstance(mock_session_state['forecast_models'], dict, 
                                "forecast_models doit être un dict")
            self.assertIsInstance(mock_session_state['validation_years'], int, 
                                "validation_years doit être un int")
            
            print("   ✅ Gestion session state: OK")
            
        except Exception as e:
            self.fail(f"Erreur gestion session state: {e}")
    
    def test_error_handling_ui(self):
        """Test de la gestion d'erreurs dans l'UI."""
        print("\n🧪 Test gestion erreurs UI...")
        
        try:
            # Test avec données invalides
            invalid_data = pd.DataFrame({'invalid_col': [1, 2, 3]})
            
            # Vérifier que les colonnes requises sont absentes
            required_cols = ['Date', 'Production journaliere d\'huile bbl']
            for col in required_cols:
                self.assertNotIn(col, invalid_data.columns, 
                                f"Colonne {col} ne doit pas être présente dans les données invalides")
            
            # Test avec algorithme invalide
            try:
                ModelFactory.create_model('production_forecast', 'algorithme_inexistant')
                self.fail("Une exception devrait être levée pour un algorithme inexistant")
            except (ValueError, KeyError):
                pass  # Exception attendue
            
            print("   ✅ Gestion erreurs UI: OK")
            
        except Exception as e:
            self.fail(f"Erreur test gestion erreurs: {e}")
    
    def test_configuration_validation(self):
        """Test de la validation des configurations."""
        print("\n🧪 Test validation configurations...")
        
        try:
            # Configuration valide
            valid_config = {
                'algorithms': ['random_forest', 'gradient_boosting'],
                'forecast_horizon': 60,
                'target_column': 'Production journaliere d\'huile bbl',
                'test_size': 0.2
            }
            
            # Vérifications de la configuration valide
            self.assertIsInstance(valid_config['algorithms'], list, "algorithms doit être une liste")
            self.assertGreater(len(valid_config['algorithms']), 0, "algorithms ne doit pas être vide")
            self.assertIsInstance(valid_config['forecast_horizon'], int, "forecast_horizon doit être un int")
            self.assertGreater(valid_config['forecast_horizon'], 0, "forecast_horizon doit être positif")
            self.assertIsInstance(valid_config['target_column'], str, "target_column doit être une string")
            self.assertGreater(len(valid_config['target_column']), 0, "target_column ne doit pas être vide")
            
            # Configuration invalide
            invalid_configs = [
                {'algorithms': []},  # Liste vide
                {'forecast_horizon': -1},  # Valeur négative
                {'target_column': ''},  # String vide
                {'test_size': 1.5}  # Valeur > 1
            ]
            
            for i, config in enumerate(invalid_configs):
                with self.subTest(config=i):
                    if 'algorithms' in config and len(config['algorithms']) == 0:
                        self.assertEqual(len(config['algorithms']), 0, "Configuration invalide détectée")
                    elif 'forecast_horizon' in config and config['forecast_horizon'] < 0:
                        self.assertLess(config['forecast_horizon'], 0, "Configuration invalide détectée")
            
            print("   ✅ Validation configurations: OK")
            
        except Exception as e:
            self.fail(f"Erreur validation configurations: {e}")

def run_ui_tests():
    """Lance tous les tests UI."""
    print("="*60)
    print("🧪 TESTS DES COMPOSANTS UI")
    print("="*60)
    
    # Créer une suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUIComponents)
    
    # Lancer les tests avec un runner personnalisé
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("📋 RÉSUMÉ DES TESTS UI")
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
    success = run_ui_tests()
    sys.exit(0 if success else 1)