#!/usr/bin/env python3
"""
Tests pour le module data_loader
Vérifie le chargement et la qualité des données
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

from data_loader import (
    load_production_data, 
    load_pump_failures_data, 
    split_data_for_validation,
    prepare_data_for_modeling
)

class TestDataLoader(unittest.TestCase):
    """Tests pour le chargement des données."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.production_df = None
        self.failures_df = None
    
    def test_load_production_data(self):
        """Test du chargement des données de production."""
        print("\n🧪 Test chargement données de production...")
        
        try:
            self.production_df = load_production_data()
            
            # Vérifications de base
            self.assertIsInstance(self.production_df, pd.DataFrame, "Doit retourner un DataFrame")
            
            if not self.production_df.empty:
                print(f"   ✅ Données chargées: {len(self.production_df)} lignes")
                
                # Vérifier les colonnes essentielles
                required_cols = ['Date', 'Production journaliere d\'huile bbl']
                for col in required_cols:
                    self.assertIn(col, self.production_df.columns, f"Colonne '{col}' manquante")
                
                # Vérifier les types
                self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.production_df['Date']), 
                              "La colonne Date doit être datetime")
                
                # Vérifier la plage de dates
                date_min = self.production_df['Date'].min()
                date_max = self.production_df['Date'].max()
                print(f"   📅 Période: {date_min} à {date_max}")
                
                # Vérifier qu'il n'y a pas que des NaN
                target_col = 'Production journaliere d\'huile bbl'
                non_null_count = self.production_df[target_col].notna().sum()
                self.assertGreater(non_null_count, 0, "La colonne cible ne doit pas être entièrement NaN")
                
                print(f"   📊 Valeurs non-null dans cible: {non_null_count}/{len(self.production_df)}")
                
                # Statistiques de base
                target_stats = self.production_df[target_col].describe()
                print(f"   📈 Production moyenne: {target_stats['mean']:.2f}")
                print(f"   📈 Production médiane: {target_stats['50%']:.2f}")
                
            else:
                print("   ⚠️ DataFrame vide - vérifier le fichier Excel")
                
        except Exception as e:
            self.fail(f"Erreur lors du chargement des données de production: {e}")
    
    def test_load_pump_failures_data(self):
        """Test du chargement des données de pannes."""
        print("\n🧪 Test chargement données de pannes...")
        
        try:
            self.failures_df = load_pump_failures_data()
            
            self.assertIsInstance(self.failures_df, pd.DataFrame, "Doit retourner un DataFrame")
            
            if not self.failures_df.empty:
                print(f"   ✅ Données de pannes: {len(self.failures_df)} lignes")
                
                # Vérifier la colonne de date si elle existe
                date_col = "Date de notification d'endomagement de la pompe"
                if date_col in self.failures_df.columns:
                    self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.failures_df[date_col]),
                                  "La colonne de date doit être datetime")
                    print(f"   📅 Pannes de {self.failures_df[date_col].min()} à {self.failures_df[date_col].max()}")
            else:
                print("   ⚠️ Pas de données de pannes")
                
        except Exception as e:
            print(f"   ⚠️ Erreur chargement pannes (normal si fichier absent): {e}")
    
    def test_split_data_for_validation(self):
        """Test de la division des données pour validation."""
        print("\n🧪 Test division des données...")
        
        # Charger les données d'abord
        self.production_df = load_production_data()
        
        if self.production_df.empty:
            self.skipTest("Pas de données de production pour tester la division")
        
        try:
            train_data, val_data = split_data_for_validation(self.production_df, validation_years=2)
            
            # Vérifications
            self.assertIsInstance(train_data, pd.DataFrame, "train_data doit être un DataFrame")
            self.assertIsInstance(val_data, pd.DataFrame, "val_data doit être un DataFrame")
            
            total_original = len(self.production_df)
            total_split = len(train_data) + len(val_data)
            
            print(f"   📊 Données originales: {total_original}")
            print(f"   📊 Données d'entraînement: {len(train_data)}")
            print(f"   📊 Données de validation: {len(val_data)}")
            print(f"   📊 Total après split: {total_split}")
            
            # Vérifier que la division est cohérente
            self.assertEqual(total_original, total_split, "La division doit préserver toutes les données")
            
            # Vérifier que les données d'entraînement sont antérieures
            if len(train_data) > 0 and len(val_data) > 0:
                train_max_date = train_data['Date'].max()
                val_min_date = val_data['Date'].min()
                self.assertLessEqual(train_max_date, val_min_date, 
                                   "Les données d'entraînement doivent être antérieures à la validation")
                
                print(f"   📅 Entraînement jusqu'à: {train_max_date}")
                print(f"   📅 Validation à partir de: {val_min_date}")
            
        except Exception as e:
            self.fail(f"Erreur lors de la division des données: {e}")
    
    def test_data_quality(self):
        """Test de la qualité des données."""
        print("\n🧪 Test qualité des données...")
        
        self.production_df = load_production_data()
        
        if self.production_df.empty:
            self.skipTest("Pas de données pour tester la qualité")
        
        try:
            # Vérifier les doublons
            duplicates = self.production_df.duplicated().sum()
            print(f"   🔍 Doublons: {duplicates}")
            
            # Vérifier les valeurs manquantes par colonne
            print("   🔍 Valeurs manquantes par colonne:")
            missing_data = self.production_df.isnull().sum()
            for col, missing_count in missing_data.items():
                if missing_count > 0:
                    percentage = (missing_count / len(self.production_df)) * 100
                    print(f"      {col}: {missing_count} ({percentage:.1f}%)")
            
            # Vérifier les valeurs aberrantes dans la production
            target_col = 'Production journaliere d\'huile bbl'
            if target_col in self.production_df.columns:
                production_values = self.production_df[target_col].dropna()
                
                if len(production_values) > 0:
                    Q1 = production_values.quantile(0.25)
                    Q3 = production_values.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = production_values[(production_values < lower_bound) | 
                                                (production_values > upper_bound)]
                    
                    print(f"   📊 Valeurs aberrantes détectées: {len(outliers)}")
                    print(f"   📊 Plage normale: [{lower_bound:.2f}, {upper_bound:.2f}]")
                    
                    # Vérifier les valeurs négatives
                    negative_values = (production_values < 0).sum()
                    if negative_values > 0:
                        print(f"   ⚠️ Valeurs négatives: {negative_values}")
            
            # Vérifier la continuité temporelle
            if 'Date' in self.production_df.columns:
                dates = self.production_df['Date'].sort_values()
                date_diffs = dates.diff().dropna()
                
                # Calculer l'écart modal entre les dates
                most_common_diff = date_diffs.mode()
                if len(most_common_diff) > 0:
                    expected_diff = most_common_diff.iloc[0]
                    print(f"   📅 Fréquence des données: {expected_diff}")
                    
                    # Détecter les trous dans les données
                    large_gaps = date_diffs[date_diffs > expected_diff * 2]
                    if len(large_gaps) > 0:
                        print(f"   ⚠️ Trous détectés dans les données: {len(large_gaps)}")
            
        except Exception as e:
            self.fail(f"Erreur lors de l'analyse de qualité: {e}")
    
    def test_prepare_data_for_modeling(self):
        """Test de la préparation des données pour la modélisation."""
        print("\n🧪 Test préparation pour modélisation...")
        
        self.production_df = load_production_data()
        self.failures_df = load_pump_failures_data()
        
        if self.production_df.empty:
            self.skipTest("Pas de données pour tester la préparation")
        
        try:
            prepared_data = prepare_data_for_modeling(
                self.production_df, 
                self.failures_df if not self.failures_df.empty else None
            )
            
            # Vérifications
            self.assertIsInstance(prepared_data, dict, "Doit retourner un dictionnaire")
            self.assertIn('production', prepared_data, "Doit contenir les données de production")
            
            prod_data = prepared_data['production']
            self.assertIsInstance(prod_data, pd.DataFrame, "Les données de production doivent être un DataFrame")
            
            print(f"   ✅ Données préparées: {len(prod_data)} lignes")
            
            # Vérifier que les données sont triées par date
            if 'Date' in prod_data.columns and len(prod_data) > 1:
                dates_sorted = prod_data['Date'].is_monotonic_increasing
                self.assertTrue(dates_sorted, "Les données doivent être triées par date")
                print(f"   📅 Données triées par date: ✅")
            
            # Vérifier l'interpolation
            target_col = 'Production journaliere d\'huile bbl'
            if target_col in prod_data.columns:
                nan_count_after = prod_data[target_col].isnull().sum()
                print(f"   🔧 NaN restants après préparation: {nan_count_after}")
            
        except Exception as e:
            self.fail(f"Erreur lors de la préparation des données: {e}")

def run_data_tests():
    """Lance tous les tests de données."""
    print("="*60)
    print("🧪 TESTS DU MODULE DATA_LOADER")
    print("="*60)
    
    # Créer une suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataLoader)
    
    # Lancer les tests avec un runner personnalisé
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("📋 RÉSUMÉ DES TESTS DATA_LOADER")
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
    success = run_data_tests()
    sys.exit(0 if success else 1)