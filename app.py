import streamlit as st
import warnings
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="Tchad Petroleum - Analyse Prédictive",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports des modules personnalisés
from src.data_loader import (
    load_production_data, load_pump_failures_data, load_interventions_data
)
from src.models.model_factory import ModelFactory
from src.ui_components import (
    HomeUI, MaintenanceUI, ForecastUI, WaterOptimizationUI, 
    ModelComparisonUI, DashboardUI, SidebarUI
)
from src.ui_components.documentation_ui import DocumentationUI
from src.plotting import (
    plot_daily_production, plot_failures_by_block, 
    display_plot_with_download, create_download_section
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

# Vérification des dépendances
@st.cache_data
def check_dependencies():
    return ModelFactory.check_dependencies()

dependencies = check_dependencies()

# Sidebar améliorée
selected_page = SidebarUI.render(production_df, failures_df)

# Actions rapides dans la sidebar
SidebarUI.render_quick_actions()

# Vérification si documentation demandée via bouton
if st.session_state.get('selected_doc_page', False):
    DocumentationUI.render()
    # Bouton pour revenir
    if st.button("← Retour à l'application", key="back_to_app"):
        st.session_state['selected_doc_page'] = False
        st.rerun()

# Routage vers les pages appropriées
elif selected_page == "🏠 Accueil":
    st.title("🏠 Accueil - Tchad Petroleum")
    st.markdown("""
    ## 🛢️ Bienvenue dans le Système d'Analyse Prédictive
    
    Cette application offre une suite complète d'outils d'analyse pour optimiser 
    les opérations pétrolières au Tchad.
    """)
    
    # Vue d'ensemble avec la HomeUI de la modélisation prédictive
    HomeUI.render(production_df, failures_df, interventions_df)

elif selected_page == "📈 Analyse de Production":
    st.title("📈 Analyse de la Production")
    
    if not production_df.empty:
        st.header("Visualisation de la production d'huile")
        
        # Filtres interactifs
        col1, col2 = st.columns(2)
        with col1:
            min_date = production_df['Date'].min().date()
            max_date = production_df['Date'].max().date()
            
            start_date, end_date = st.slider(
                "Sélectionnez une plage de dates",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="DD/MM/YYYY"
            )
        
        with col2:
            show_raw_data = st.checkbox("Afficher les données brutes", value=False)
        
        # Filtrer les données
        mask = (production_df['Date'].dt.date >= start_date) & (production_df['Date'].dt.date <= end_date)
        filtered_df = production_df.loc[mask]
        
        # Métriques rapides
        col1, col2, col3, col4 = st.columns(4)
        
        # Variables pour éviter les backslashes dans les f-strings
        oil_col = "Production journaliere d'huile bbl"
        total_prod = filtered_df[oil_col].sum()
        avg_prod = filtered_df[oil_col].mean()
        max_prod = filtered_df[oil_col].max()
        
        with col1:
            st.metric("Production totale", f"{total_prod:,.0f} bbl")
        with col2:
            st.metric("Production moyenne", f"{avg_prod:.0f} bbl/j")
        with col3:
            st.metric("Production max", f"{max_prod:,.0f} bbl/j")
        with col4:
            st.metric("Nombre de jours", f"{len(filtered_df)} jours")
        
        # Graphique avec téléchargement
        fig = plot_daily_production(filtered_df)
        display_plot_with_download(
            fig, 
            title="Production_Journaliere_Huile",
            key_prefix="prod_analysis"
        )
        
        # Données brutes si demandées
        if show_raw_data:
            st.header("Données de production brutes")
            st.dataframe(filtered_df, use_container_width=True)
    else:
        st.error("❌ Aucune donnée de production disponible.")

elif selected_page == "🔧 Analyse des Pannes":
    st.title("🔧 Analyse des Pannes de Pompes")
    
    if not failures_df.empty:
        # Métriques des pannes
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total des pannes", len(failures_df))
        with col2:
            if 'Bloc Faillé' in failures_df.columns:
                unique_blocks = failures_df['Bloc Faillé'].nunique()
                st.metric("Blocs affectés", unique_blocks)
        with col3:
            if "Date de notification d'endomagement de la pompe" in failures_df.columns:
                date_range = failures_df["Date de notification d'endomagement de la pompe"].max() - failures_df["Date de notification d'endomagement de la pompe"].min()
                st.metric("Période (jours)", date_range.days)
        
        # Graphiques
        st.header("Répartition des pannes par bloc")
        fig_failures = plot_failures_by_block(failures_df)
        display_plot_with_download(
            fig_failures,
            title="Repartition_Pannes_par_Bloc",
            key_prefix="failures_analysis"
        )
        
        # Historique
        st.header("Historique des pannes")
        
        # Options d'affichage
        col1, col2 = st.columns(2)
        with col1:
            show_details = st.checkbox("Afficher les détails", value=True)
        with col2:
            sort_by_date = st.checkbox("Trier par date", value=True)
        
        display_df = failures_df.copy()
        if sort_by_date and "Date de notification d'endomagement de la pompe" in display_df.columns:
            display_df = display_df.sort_values("Date de notification d'endomagement de la pompe", ascending=False)
        
        if show_details:
            st.dataframe(display_df, use_container_width=True)
        else:
             # Vue simplifiée
             date_col = "Date de notification d'endomagement de la pompe"
             simple_cols = [date_col, 'Bloc Faillé'] if 'Bloc Faillé' in display_df.columns else display_df.columns[:3]
             st.dataframe(display_df[simple_cols], use_container_width=True)
    else:
        st.error("❌ Aucune donnée de panne disponible.")

# Pages de modélisation prédictive
elif selected_page == "🔧 Maintenance Prédictive":
    st.title("🔧 Maintenance Prédictive des Pompes")
    MaintenanceUI.render(production_df, failures_df, dependencies)

elif selected_page == "📈 Prévision de Production":
    st.title("📈 Prévision de Production d'Huile")
    ForecastUI.render(production_df, dependencies)

elif selected_page == "💧 Optimisation Injection d'Eau":
    st.title("💧 Optimisation de l'Injection d'Eau")
    WaterOptimizationUI.render(production_df, dependencies)

elif selected_page == "📊 Comparaison de Modèles":
    st.title("📊 Comparaison Avancée de Modèles")
    ModelComparisonUI.render()

elif selected_page == "📋 Dashboard KPIs":
    st.title("📋 Dashboard des Indicateurs de Performance")
    DashboardUI.render(production_df, failures_df)

elif selected_page == "📚 Documentation":
    DocumentationUI.render()

# Footer global
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <h4>🛢️ Tchad Petroleum Company</h4>
    <p>Système d'Analyse Prédictive Avancé • Version 2.0</p>
    <p style='font-size: 12px;'>Architecture Modulaire • Algorithmes Multiples • Interface Intuitive</p>
    <p style='font-size: 10px; margin-top: 10px;'>Développé avec ❤️ pour l'excellence opérationnelle</p>
</div>
""", unsafe_allow_html=True)