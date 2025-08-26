import streamlit as st
import warnings
warnings.filterwarnings('ignore')

# Imports des modules personnalisés
from src.data_loader import (
    load_production_data, load_pump_failures_data, load_interventions_data
)
from src.models.model_factory import ModelFactory
from src.ui_components import (
    HomeUI, MaintenanceUI, ForecastUI, WaterOptimizationUI, 
    ModelComparisonUI, DashboardUI
)

# Configuration de la page
st.set_page_config(page_title="Modélisation Prédictive", layout="wide")
st.title("🔮 Modélisation Prédictive Avancée")

# Sidebar pour la navigation
st.sidebar.title("🎯 Navigation")
model_type = st.sidebar.selectbox(
    "Choisissez le type de modèle :",
    ["🏠 Accueil", "🔧 Maintenance Prédictive", "📈 Prévision de Production", 
     "💧 Optimisation Injection d'Eau", "📊 Comparaison de Modèles", "📋 Dashboard KPIs"]
)

# Chargement des données
@st.cache_data
def load_all_data():
    """Charge toutes les données nécessaires."""
    production_df = load_production_data()
    failures_df = load_pump_failures_data()
    interventions_df = load_interventions_data()
    return production_df, failures_df, interventions_df

production_df, failures_df, interventions_df = load_all_data()

if production_df.empty:
    st.error("❌ Impossible de charger les données de production. Vérifiez le fichier Excel.")
    st.stop()

# Vérification des dépendances
@st.cache_data
def check_dependencies():
    return ModelFactory.check_dependencies()

dependencies = check_dependencies()

# Routage vers les composants UI appropriés
if model_type == "🏠 Accueil":
    HomeUI.render(production_df, failures_df, interventions_df)

elif model_type == "🔧 Maintenance Prédictive":
    MaintenanceUI.render(production_df, failures_df, dependencies)

elif model_type == "📈 Prévision de Production":
    ForecastUI.render(production_df, dependencies)

elif model_type == "💧 Optimisation Injection d'Eau":
    WaterOptimizationUI.render(production_df, dependencies)

elif model_type == "📊 Comparaison de Modèles":
    ModelComparisonUI.render()

elif model_type == "📋 Dashboard KPIs":
    DashboardUI.render(production_df, failures_df)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    🛢️ Tchad Petroleum Company - Système de Modélisation Prédictive Avancé
    <br>Développé avec ❤️ pour l'excellence opérationnelle
    <br>Architecture modulaire • Algorithmes multiples • Évaluation complète
</div>
""", unsafe_allow_html=True)