#!/usr/bin/env python3
"""
Script principal pour lancer tous les tests
Génère un rapport complet de l'état du système
"""

import sys
import os
import time
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Supprimer les warnings pour une sortie propre
import warnings
warnings.filterwarnings('ignore')

# Imports des modules de test
from test_data_loader import run_data_tests
from test_models import run_model_tests
from test_ui_components import run_ui_tests

def print_header():
    """Affiche l'en-tête du rapport de tests."""
    print("="*80)
    print("🧪 SUITE COMPLÈTE DE TESTS - TCHAD PETROLEUM ML")
    print("="*80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️ Système: {os.name}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print("="*80)

def print_separator(title):
    """Affiche un séparateur avec titre."""
    print("\n" + "="*80)
    print(f"📋 {title}")
    print("="*80)

def run_test_suite(test_name, test_function):
    """Lance une suite de tests et mesure le temps d'exécution."""
    print(f"\n🚀 Lancement des tests {test_name}...")
    start_time = time.time()
    
    try:
        success = test_function()
        duration = time.time() - start_time
        
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"\n⏱️ Durée: {duration:.2f}s")
        print(f"🎯 Statut: {status}")
        
        return success, duration
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n💥 ERREUR FATALE: {e}")
        print(f"⏱️ Durée: {duration:.2f}s")
        print(f"🎯 Statut: ❌ ERREUR")
        
        return False, duration

def generate_system_info():
    """Génère des informations système."""
    print_separator("INFORMATIONS SYSTÈME")
    
    try:
        import pandas as pd
        print(f"📊 Pandas: {pd.__version__}")
    except ImportError:
        print("📊 Pandas: ❌ Non installé")
    
    try:
        import numpy as np
        print(f"🔢 NumPy: {np.__version__}")
    except ImportError:
        print("🔢 NumPy: ❌ Non installé")
    
    try:
        import sklearn
        print(f"🤖 Scikit-learn: {sklearn.__version__}")
    except ImportError:
        print("🤖 Scikit-learn: ❌ Non installé")
    
    try:
        import xgboost
        print(f"🚀 XGBoost: {xgboost.__version__}")
    except ImportError:
        print("🚀 XGBoost: ❌ Non installé")
    
    try:
        import streamlit
        try:
            version = streamlit.__version__
            print(f"🌐 Streamlit: {version}")
        except AttributeError:
            print("🌐 Streamlit: ✅ Installé (version inconnue)")
    except ImportError:
        print("🌐 Streamlit: ❌ Non installé")
    
    # Vérifier les fichiers de données
    data_file = os.path.join('data', 'Données de production Rev.xlsx')
    if os.path.exists(data_file):
        file_size = os.path.getsize(data_file) / (1024 * 1024)  # MB
        print(f"📁 Fichier de données: ✅ ({file_size:.1f} MB)")
    else:
        print(f"📁 Fichier de données: ❌ Manquant")
    
    # Vérifier la structure des dossiers
    required_dirs = ['src', 'src/models', 'src/ui_components', 'tests']
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if f.endswith('.py')])
            print(f"📂 {dir_path}: ✅ ({file_count} fichiers Python)")
        else:
            print(f"📂 {dir_path}: ❌ Manquant")

def generate_recommendations(results):
    """Génère des recommandations basées sur les résultats des tests."""
    print_separator("RECOMMANDATIONS")
    
    total_tests = len(results)
    successful_tests = sum(1 for success, _ in results.values() if success)
    
    if successful_tests == total_tests:
        print("🎉 EXCELLENT ! Tous les tests passent.")
        print("\n✅ Actions recommandées:")
        print("   • Le système est prêt pour la production")
        print("   • Continuer le monitoring des performances")
        print("   • Envisager l'ajout de nouveaux modèles")
    
    elif successful_tests >= total_tests * 0.8:
        print("👍 BON ! La plupart des tests passent.")
        print("\n⚠️ Actions recommandées:")
        print("   • Corriger les tests en échec")
        print("   • Vérifier les dépendances manquantes")
        print("   • Tester en environnement de staging")
    
    elif successful_tests >= total_tests * 0.5:
        print("⚠️ MOYEN ! Plusieurs problèmes détectés.")
        print("\n🔧 Actions recommandées:")
        print("   • Corriger les erreurs critiques")
        print("   • Vérifier la configuration")
        print("   • Revoir l'architecture des données")
    
    else:
        print("🚨 CRITIQUE ! Nombreux échecs détectés.")
        print("\n🆘 Actions urgentes:")
        print("   • Arrêter le déploiement")
        print("   • Corriger les erreurs fondamentales")
        print("   • Revoir l'installation des dépendances")
        print("   • Vérifier l'intégrité des données")
    
    # Recommandations spécifiques par module
    if 'Data Loader' in results and not results['Data Loader'][0]:
        print("\n📊 Problème Data Loader:")
        print("   • Vérifier le fichier Excel dans data/")
        print("   • Contrôler les colonnes et formats")
        print("   • Tester le chargement manuel")
    
    if 'Modèles ML' in results and not results['Modèles ML'][0]:
        print("\n🤖 Problème Modèles ML:")
        print("   • Vérifier scikit-learn et dépendances")
        print("   • Contrôler la qualité des données")
        print("   • Ajuster les hyperparamètres")
        print("   • Réduire la complexité des features")
    
    if 'Composants UI' in results and not results['Composants UI'][0]:
        print("\n🌐 Problème Interface:")
        print("   • Vérifier Streamlit et imports")
        print("   • Contrôler les mocks de test")
        print("   • Tester l'interface manuellement")

def main():
    """Fonction principale qui lance tous les tests."""
    print_header()
    
    # Informations système
    generate_system_info()
    
    # Définir les suites de tests
    test_suites = [
        ("Data Loader", run_data_tests),
        ("Modèles ML", run_model_tests),
        ("Composants UI", run_ui_tests)
    ]
    
    # Lancer tous les tests
    results = {}
    total_duration = 0
    
    for test_name, test_function in test_suites:
        print_separator(f"TESTS {test_name.upper()}")
        success, duration = run_test_suite(test_name, test_function)
        results[test_name] = (success, duration)
        total_duration += duration
    
    # Rapport final
    print_separator("RAPPORT FINAL")
    
    successful_suites = sum(1 for success, _ in results.values() if success)
    total_suites = len(results)
    
    print(f"📊 Suites de tests: {successful_suites}/{total_suites} réussies")
    print(f"⏱️ Durée totale: {total_duration:.2f}s")
    
    print("\n📋 Détail par suite:")
    for test_name, (success, duration) in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {test_name:15} | {duration:6.2f}s")
    
    # Calcul du score global
    success_rate = (successful_suites / total_suites) * 100
    print(f"\n🎯 Score global: {success_rate:.1f}%")
    
    if success_rate == 100:
        grade = "🏆 EXCELLENT"
    elif success_rate >= 80:
        grade = "👍 BON"
    elif success_rate >= 60:
        grade = "⚠️ MOYEN"
    else:
        grade = "🚨 CRITIQUE"
    
    print(f"📈 Évaluation: {grade}")
    
    # Générer les recommandations
    generate_recommendations(results)
    
    # Footer
    print("\n" + "="*80)
    print("🏁 FIN DES TESTS")
    print("="*80)
    
    # Code de sortie
    return 0 if successful_suites == total_suites else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erreur fatale: {e}")
        sys.exit(1)