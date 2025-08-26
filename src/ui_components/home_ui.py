import streamlit as st
import pandas as pd
from src.models.model_factory import ModelFactory
from src.plotting import plot_production_components

class HomeUI:
    """Composant UI pour la page d'accueil de la modélisation prédictive."""
    
    @staticmethod
    def render(production_df: pd.DataFrame, failures_df: pd.DataFrame, interventions_df: pd.DataFrame):
        """Affiche la page d'accueil."""
        st.header("🚀 Système de Modélisation Prédictive Avancé")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            HomeUI._render_data_overview(production_df, failures_df)
            HomeUI._render_production_overview(production_df)
        
        with col2:
            HomeUI._render_algorithms_status()
            HomeUI._render_use_cases()
        
        HomeUI._render_global_configuration()
    
    @staticmethod
    def _render_data_overview(production_df: pd.DataFrame, failures_df: pd.DataFrame):
        """Affiche l'aperçu des données."""
        st.subheader("📊 Aperçu des Données")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("📈 Enregistrements de production", len(production_df))
        with col_b:
            st.metric("🔧 Pannes enregistrées", len(failures_df) if not failures_df.empty else 0)
        with col_c:
            if not production_df.empty:
                date_range = production_df['Date'].max() - production_df['Date'].min()
                st.metric("📅 Période couverte (jours)", date_range.days)
    
    @staticmethod
    def _render_production_overview(production_df: pd.DataFrame):
        """Affiche le graphique de vue d'ensemble de la production."""
        st.subheader("📈 Vue d'Ensemble de la Production")
        if not production_df.empty:
            fig = plot_production_components(production_df)
            st.pyplot(fig)
    
    @staticmethod
    def _render_algorithms_status():
        """Affiche le statut des algorithmes disponibles."""
        st.subheader("🤖 Algorithmes Disponibles")
        
        # Vérification des dépendances
        dependencies = ModelFactory.check_dependencies()
        
        st.write("**📦 Statut des Dépendances :**")
        for lib, available in dependencies.items():
            status = "✅" if available else "❌"
            st.write(f"{status} {lib.title()}")
        
        # Avertissements pour les dépendances manquantes
        if not dependencies['xgboost']:
            st.warning("⚠️ XGBoost non disponible. Installez avec: `pip install xgboost`")
        if not dependencies['prophet']:
            st.warning("⚠️ Prophet non disponible. Installez avec: `pip install prophet`")
        if not dependencies['neuralprophet']:
            st.warning("⚠️ NeuralProphet non disponible. Installez avec: `pip install neuralprophet`")
    
    @staticmethod
    def _render_use_cases():
        """Affiche les cas d'usage disponibles."""
        st.subheader("🎯 Cas d'Usage")
        
        st.info("""
        **🔧 Maintenance Prédictive**
        - Random Forest, Gradient Boosting, XGBoost
        - Prédiction des pannes de pompes
        - Alertes automatiques
        """)
        
        st.info("""
        **📈 Prévision de Production**
        - Prophet, NeuralProphet, XGBoost
        - Prédiction de production d'huile
        - Analyse de saisonnalité
        """)
        
        st.info("""
        **💧 Optimisation Injection d'Eau**
        - Modèles de régression avancés
        - Maximisation de l'efficacité
        - Recommandations automatiques
        """)
    
    @staticmethod
    def _render_global_configuration():
        """Affiche la configuration globale."""
        st.subheader("⚙️ Configuration Globale")
        
        col1, col2 = st.columns(2)
        with col1:
            validation_years = st.slider(
                "Années pour validation :",
                min_value=1, max_value=5, value=2,
                help="Les N dernières années seront utilisées pour valider les modèles"
            )
            st.session_state['validation_years'] = validation_years
        
        with col2:
            auto_optimize = st.checkbox(
                "Optimisation automatique des hyperparamètres",
                value=False,
                help="Active l'optimisation automatique (plus lent mais meilleure performance)"
            )
            st.session_state['auto_optimize'] = auto_optimize
        
        st.success(f"✅ Configuration sauvegardée : {validation_years} années pour validation, optimisation {'activée' if auto_optimize else 'désactivée'}")