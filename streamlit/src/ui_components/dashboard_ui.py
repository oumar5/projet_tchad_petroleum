import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from src.data_loader import calculate_production_kpis, calculate_failure_kpis
from src.plotting import plot_kpi_dashboard, display_plot_with_download

class DashboardUI:
    """Composant UI pour le dashboard des KPIs."""
    
    @staticmethod
    def render(production_df: pd.DataFrame, failures_df: pd.DataFrame):
        """Affiche le dashboard des indicateurs de performance."""
        # Calculer les KPIs
        production_kpis = calculate_production_kpis(production_df)
        failure_kpis = calculate_failure_kpis(failures_df)
        
        # Affichage du dashboard principal
        DashboardUI._render_main_dashboard(production_kpis, failure_kpis)
        
        # KPIs détaillés
        DashboardUI._render_detailed_kpis(production_kpis, failure_kpis)
        
        # Analyse automatique
        DashboardUI._render_automatic_analysis(production_kpis, failure_kpis)
        
        # Tendances historiques
        DashboardUI._render_historical_trends(production_df)
    
    @staticmethod
    def _render_main_dashboard(production_kpis: dict, failure_kpis: dict):
        """Affiche le dashboard principal."""
        if production_kpis or failure_kpis:
            fig = plot_kpi_dashboard(production_kpis, failure_kpis)
            display_plot_with_download(
                fig,
                title="Dashboard_KPIs_Principal",
                key_prefix="main_dashboard"
            )
    
    @staticmethod
    def _render_detailed_kpis(production_kpis: dict, failure_kpis: dict):
        """Affiche les KPIs détaillés en colonnes."""
        col1, col2 = st.columns(2)
        
        with col1:
            DashboardUI._render_production_kpis(production_kpis)
        
        with col2:
            DashboardUI._render_maintenance_kpis(failure_kpis)
    
    @staticmethod
    def _render_production_kpis(production_kpis: dict):
        """Affiche les KPIs de production."""
        st.subheader("📈 KPIs de Production")
        
        if 'oil_production' in production_kpis:
            oil_kpis = production_kpis['oil_production']
            
            # Métriques principales
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Production totale", f"{oil_kpis['total']:,.0f} bbl")
                st.metric("Production max/jour", f"{oil_kpis['max_daily']:,.0f} bbl")
            with col_b:
                st.metric("Production moyenne/jour", f"{oil_kpis['average_daily']:.0f} bbl")
                st.metric("Écart-type", f"{oil_kpis['std_daily']:.0f} bbl")
        
        if 'watercut' in production_kpis:
            wc_kpis = production_kpis['watercut']
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Watercut actuel", f"{wc_kpis['current']:.1f}%")
            with col_b:
                st.metric("Watercut moyen", f"{wc_kpis['average']:.1f}%")
    
    @staticmethod
    def _render_maintenance_kpis(failure_kpis: dict):
        """Affiche les KPIs de maintenance."""
        st.subheader("🔧 KPIs de Maintenance")
        
        if failure_kpis:
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Pannes totales", failure_kpis.get('total_failures', 0))
            with col_b:
                if 'mtbf_days' in failure_kpis:
                    st.metric("MTBF (jours)", f"{failure_kpis['mtbf_days']:.0f}")
            
            if 'failures_by_block' in failure_kpis:
                st.write("**Pannes par bloc :**")
                for block, count in failure_kpis['failures_by_block'].items():
                    st.write(f"- {block}: {count} pannes")
    
    @staticmethod
    def _render_automatic_analysis(production_kpis: dict, failure_kpis: dict):
        """Affiche l'analyse automatique."""
        st.subheader("📊 Analyse Automatique")
        
        if st.button("🤖 Générer Analyse Intelligente"):
            st.write("### 🧠 Analyse Automatique des Performances")
            
            analysis_results = DashboardUI._perform_analysis(production_kpis, failure_kpis)
            
            # Afficher les résultats
            for status, message, level in analysis_results:
                if level == "error":
                    st.error(f"{status}: {message}")
                elif level == "warning":
                    st.warning(f"{status}: {message}")
                else:
                    st.success(f"{status}: {message}")
            
            # Recommandations
            DashboardUI._render_recommendations(analysis_results)
    
    @staticmethod
    def _perform_analysis(production_kpis: dict, failure_kpis: dict):
        """Effectue l'analyse automatique des performances."""
        analysis_results = []
        
        # Analyse de la production
        if 'oil_production' in production_kpis:
            oil_kpis = production_kpis['oil_production']
            cv = oil_kpis['std_daily'] / oil_kpis['average_daily']
            
            if cv > 0.3:
                analysis_results.append(("⚠️ ATTENTION", f"Variabilité élevée de la production (CV = {cv:.2f})", "warning"))
            else:
                analysis_results.append(("✅ POSITIF", f"Production stable (CV = {cv:.2f})", "success"))
        
        # Analyse du watercut
        if 'watercut' in production_kpis:
            wc_kpis = production_kpis['watercut']
            if wc_kpis['current'] > 80:
                analysis_results.append(("🚨 CRITIQUE", "Watercut critique - Intervention urgente recommandée", "error"))
            elif wc_kpis['current'] > 60:
                analysis_results.append(("⚠️ ATTENTION", "Watercut élevé - Surveillance renforcée", "warning"))
            else:
                analysis_results.append(("✅ POSITIF", "Watercut acceptable", "success"))
        
        # Analyse des pannes
        if 'mtbf_days' in failure_kpis:
            mtbf = failure_kpis['mtbf_days']
            if mtbf < 30:
                analysis_results.append(("🚨 CRITIQUE", f"MTBF critique ({mtbf:.0f} jours) - Maintenance préventive urgente", "error"))
            elif mtbf < 90:
                analysis_results.append(("⚠️ ATTENTION", f"MTBF faible ({mtbf:.0f} jours) - Améliorer la maintenance", "warning"))
            else:
                analysis_results.append(("✅ POSITIF", f"MTBF acceptable ({mtbf:.0f} jours)", "success"))
        
        return analysis_results
    
    @staticmethod
    def _render_recommendations(analysis_results: list):
        """Affiche les recommandations automatiques."""
        st.subheader("💡 Recommandations Automatiques")
        
        recommendations = []
        
        if any("CRITIQUE" in result[0] for result in analysis_results):
            recommendations.append("🚨 **Action immédiate requise** : Planifier une intervention d'urgence")
        
        if any("Watercut" in result[1] and "élevé" in result[1] for result in analysis_results):
            recommendations.append("💧 **Optimiser l'injection d'eau** : Revoir les paramètres d'injection")
        
        if any("MTBF" in result[1] and "faible" in result[1] for result in analysis_results):
            recommendations.append("🔧 **Renforcer la maintenance préventive** : Augmenter la fréquence des inspections")
        
        if any("Variabilité" in result[1] for result in analysis_results):
            recommendations.append("📊 **Stabiliser la production** : Analyser les causes de variabilité")
        
        if not recommendations:
            recommendations.append("✅ **Situation stable** : Maintenir les opérations actuelles et surveiller les tendances")
        
        for rec in recommendations:
            st.write(rec)
    
    @staticmethod
    def _render_historical_trends(production_df: pd.DataFrame):
        """Affiche les tendances historiques."""
        st.subheader("📈 Tendances Historiques")
        
        if not production_df.empty:
            # Graphique de tendance de production
            fig, axes = plt.subplots(2, 1, figsize=(15, 10))
            
            # Production d'huile
            axes[0].plot(production_df['Date'], production_df["Production journaliere d'huile bbl"], 
                        color='green', linewidth=2)
            axes[0].set_title('Tendance de Production d\'Huile')
            axes[0].set_ylabel('Barils/jour')
            axes[0].grid(True)
            
            # Watercut
            axes[1].plot(production_df['Date'], production_df["Teneur en eau (Watercut)"], 
                        color='red', linewidth=2)
            axes[1].set_title('Évolution du Watercut')
            axes[1].set_ylabel('%')
            axes[1].set_xlabel('Date')
            axes[1].grid(True)
            
            # Rotation des dates
            for ax in axes:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Afficher avec option de téléchargement
            display_plot_with_download(
                fig,
                title="Tendances_Historiques_Production",
                key_prefix="dashboard_trends"
            )