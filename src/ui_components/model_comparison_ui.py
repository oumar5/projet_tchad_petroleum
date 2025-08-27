import streamlit as st
import pandas as pd

class ModelComparisonUI:
    """Composant UI pour la comparaison de modèles."""
    
    @staticmethod
    def render():
        """Affiche l'interface de comparaison de modèles."""
        # Vérifier s'il y a des résultats à comparer
        available_results = ModelComparisonUI._get_available_results()
        
        if not available_results:
            st.warning("⚠️ Aucun modèle entraîné disponible pour la comparaison. Veuillez d'abord entraîner des modèles dans les autres sections.")
            st.stop()
        
        # Sélection du type de comparaison
        comparison_type = st.selectbox(
            "Type de comparaison :",
            available_results
        )
        
        # Afficher la comparaison selon le type
        if comparison_type == "Maintenance Prédictive":
            ModelComparisonUI._render_maintenance_comparison()
        elif comparison_type == "Prévision de Production":
            ModelComparisonUI._render_forecast_comparison()
        elif comparison_type == "Optimisation Injection d'Eau":
            ModelComparisonUI._render_water_comparison()
        
        # Export des résultats
        ModelComparisonUI._render_export_section(comparison_type)
    
    @staticmethod
    def _get_available_results():
        """Retourne la liste des résultats disponibles."""
        available_results = []
        if 'maintenance_results' in st.session_state:
            available_results.append("Maintenance Prédictive")
        if 'forecast_results' in st.session_state:
            available_results.append("Prévision de Production")
        if 'water_results' in st.session_state:
            available_results.append("Optimisation Injection d'Eau")
        return available_results
    
    @staticmethod
    def _render_maintenance_comparison():
        """Affiche la comparaison des modèles de maintenance prédictive."""
        if 'maintenance_evaluator' not in st.session_state:
            return
        
        evaluator = st.session_state['maintenance_evaluator']
        results = st.session_state['maintenance_results']
        
        st.subheader("🔧 Comparaison des Modèles de Maintenance Prédictive")
        
        # Tableau de comparaison détaillé
        comparison_data = []
        for alg_name, result in results.items():
            metrics = result['metrics']
            comparison_data.append({
                'Algorithme': alg_name,
                'Accuracy': metrics.get('accuracy', 0),
                'Precision': metrics.get('precision', 0),
                'Recall': metrics.get('recall', 0),
                'F1-Score': metrics.get('f1_score', 0),
                'ROC-AUC': metrics.get('roc_auc', 0)
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df.style.highlight_max(axis=0), use_container_width=True)
        
        # Graphiques de comparaison
        col1, col2 = st.columns(2)
        
        with col1:
            fig_f1 = evaluator.plot_model_comparison('f1_score')
            st.pyplot(fig_f1)
        
        with col2:
            fig_acc = evaluator.plot_model_comparison('accuracy')
            st.pyplot(fig_acc)
        
        # Courbes ROC multiples
        if len([r for r in results.values() if 'roc_auc' in r['metrics']]) > 1:
            st.subheader("📈 Courbes ROC Comparatives")
            fig_roc = evaluator.plot_roc_curve(list(results.keys()))
            st.pyplot(fig_roc)
        
        # Recommandation du meilleur modèle
        best_model = evaluator.get_best_model('f1_score')
        if best_model:
            st.success(f"🏆 **Meilleur modèle recommandé** : {best_model} (F1-Score: {results[best_model]['metrics']['f1_score']:.3f})")
    
    @staticmethod
    def _render_forecast_comparison():
        """Affiche la comparaison des modèles de prévision."""
        if 'forecast_evaluator' not in st.session_state:
            return
        
        evaluator = st.session_state['forecast_evaluator']
        results = st.session_state['forecast_results']
        
        st.subheader("📈 Comparaison des Modèles de Prévision")
        
        # Tableau de comparaison
        comparison_data = []
        for alg_name, result in results.items():
            metrics = result['metrics']
            comparison_data.append({
                'Algorithme': alg_name,
                'R²': metrics.get('r2', 0),
                'RMSE': metrics.get('rmse', 0),
                'MAE': metrics.get('mae', 0),
                'MAPE': metrics.get('mape', 0)
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Highlight max pour R² (plus c'est haut, mieux c'est)
        # Highlight min pour RMSE, MAE, MAPE (plus c'est bas, mieux c'est)
        styled_df = comparison_df.style.highlight_max(subset=['R²'], color='lightgreen')
        styled_df = styled_df.highlight_min(subset=['RMSE', 'MAE', 'MAPE'], color='lightgreen')
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Graphiques de comparaison
        col1, col2 = st.columns(2)
        
        with col1:
            fig_r2 = evaluator.plot_model_comparison('r2')
            st.pyplot(fig_r2)
        
        with col2:
            fig_rmse = evaluator.plot_model_comparison('rmse')
            st.pyplot(fig_rmse)
        
        # Recommandation
        best_model = evaluator.get_best_model('r2')
        if best_model:
            st.success(f"🏆 **Meilleur modèle recommandé** : {best_model} (R²: {results[best_model]['metrics']['r2']:.3f})")
    
    @staticmethod
    def _render_water_comparison():
        """Affiche la comparaison des modèles d'optimisation de l'eau."""
        if 'water_evaluator' not in st.session_state:
            return
        
        evaluator = st.session_state['water_evaluator']
        results = st.session_state['water_results']
        
        st.subheader("💧 Comparaison des Modèles d'Optimisation")
        
        # Tableau de comparaison similaire à la prévision
        comparison_data = []
        for alg_name, result in results.items():
            metrics = result['metrics']
            comparison_data.append({
                'Algorithme': alg_name,
                'R²': metrics.get('r2', 0),
                'RMSE': metrics.get('rmse', 0),
                'MAE': metrics.get('mae', 0),
                'MAPE': metrics.get('mape', 0)
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        styled_df = comparison_df.style.highlight_max(subset=['R²'], color='lightgreen')
        styled_df = styled_df.highlight_min(subset=['RMSE', 'MAE', 'MAPE'], color='lightgreen')
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Recommandation
        best_model = evaluator.get_best_model('r2')
        if best_model:
            st.success(f"🏆 **Meilleur modèle recommandé** : {best_model} (R²: {results[best_model]['metrics']['r2']:.3f})")
    
    @staticmethod
    def _render_export_section(comparison_type: str):
        """Affiche la section d'export des résultats."""
        st.subheader("💾 Export des Résultats")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Exporter en CSV"):
                try:
                    evaluator = ModelComparisonUI._get_evaluator(comparison_type)
                    if evaluator:
                        evaluator.export_results('model_comparison.csv', format='csv')
                        st.success("✅ Résultats exportés en CSV")
                except Exception as e:
                    st.error(f"Erreur lors de l'export : {e}")
        
        with col2:
            if st.button("📋 Générer Rapport Complet"):
                try:
                    evaluator, results = ModelComparisonUI._get_evaluator_and_results(comparison_type)
                    if evaluator and results:
                        ModelComparisonUI._generate_full_report(evaluator, results, comparison_type)
                except Exception as e:
                    st.error(f"Erreur lors de la génération du rapport : {e}")
    
    @staticmethod
    def _get_evaluator(comparison_type: str):
        """Retourne l'évaluateur selon le type de comparaison."""
        if comparison_type == "Maintenance Prédictive":
            return st.session_state.get('maintenance_evaluator')
        elif comparison_type == "Prévision de Production":
            return st.session_state.get('forecast_evaluator')
        elif comparison_type == "Optimisation Injection d'Eau":
            return st.session_state.get('water_evaluator')
        return None
    
    @staticmethod
    def _get_evaluator_and_results(comparison_type: str):
        """Retourne l'évaluateur et les résultats selon le type de comparaison."""
        if comparison_type == "Maintenance Prédictive":
            return (st.session_state.get('maintenance_evaluator'), 
                   st.session_state.get('maintenance_results'))
        elif comparison_type == "Prévision de Production":
            return (st.session_state.get('forecast_evaluator'), 
                   st.session_state.get('forecast_results'))
        elif comparison_type == "Optimisation Injection d'Eau":
            return (st.session_state.get('water_evaluator'), 
                   st.session_state.get('water_results'))
        return None, None
    
    @staticmethod
    def _generate_full_report(evaluator, results: dict, comparison_type: str):
        """Génère un rapport complet."""
        # Générer un rapport pour chaque modèle
        full_report = f"RAPPORT COMPLET - {comparison_type.upper()}\n"
        full_report += "=" * 60 + "\n\n"
        
        for model_name in results.keys():
            report = evaluator.generate_report(model_name)
            full_report += report + "\n\n"
        
        st.text_area("Rapport Complet", full_report, height=400)