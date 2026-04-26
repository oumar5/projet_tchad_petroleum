import streamlit as st
import pandas as pd
import numpy as np
from src.models.model_factory import ModelFactory
from src.models.model_evaluator import ModelEvaluator
from src.data_loader import split_data_for_validation
from src.plotting import (
    plot_model_performance_metrics, plot_failure_probability_timeline,
    display_plot_with_download, create_download_section
)

class MaintenanceUI:
    """Composant UI pour la maintenance prédictive."""
    
    @staticmethod
    def render(production_df: pd.DataFrame, failures_df: pd.DataFrame, dependencies: dict):
        """Affiche l'interface de maintenance prédictive."""
        if failures_df.empty:
            st.warning("⚠️ Aucune donnée de panne disponible pour l'entraînement du modèle.")
            st.stop()
        
        # Configuration et sélection d'algorithmes
        selected_algorithms, config = MaintenanceUI._render_algorithm_selection(dependencies)
        
        if not selected_algorithms:
            st.warning("⚠️ Veuillez sélectionner au moins un algorithme.")
            st.stop()
        
        # Entraînement des modèles
        if st.button("🚀 Entraîner les Modèles de Maintenance Prédictive", type="primary"):
            MaintenanceUI._train_models(selected_algorithms, config, production_df, failures_df)
        
        # Affichage des résultats
        MaintenanceUI._render_results()
    
    @staticmethod
    def _render_algorithm_selection(dependencies: dict):
        """Affiche la sélection d'algorithmes et la configuration."""
        st.subheader("🎯 Sélection d'Algorithmes")
        
        available_algorithms = ModelFactory.get_available_models('maintenance_predictive')
        algorithm_options = []
        
        for alg_name, alg_config in available_algorithms['maintenance_predictive'].items():
            if alg_config['category'] == 'xgboost' and not dependencies['xgboost']:
                continue
            algorithm_options.append(alg_name)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_algorithms = st.multiselect(
                "Algorithmes à comparer :",
                algorithm_options,
                default=[algorithm_options[0]] if algorithm_options else [],
                help="Sélectionnez un ou plusieurs algorithmes à entraîner et comparer"
            )
        
        with col2:
            ensemble_mode = st.checkbox(
                "Mode Ensemble",
                value=False,
                help="Combine les prédictions de tous les modèles sélectionnés"
            )
        
        # Configuration des modèles
        st.subheader("⚙️ Configuration des Modèles")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            prediction_horizon = st.selectbox(
                "Horizon de prédiction (jours) :",
                [7, 14, 30],
                index=0,
                help="Nombre de jours à l'avance pour prédire les pannes"
            )
        
        with col2:
            test_size = st.slider(
                "Taille du jeu de test (%) :",
                min_value=10, max_value=40, value=20
            ) / 100
        
        with col3:
            optimize_hyperparams = st.checkbox(
                "Optimiser les hyperparamètres",
                value=st.session_state.get('auto_optimize', False)
            )
        
        config = {
            'ensemble_mode': ensemble_mode,
            'prediction_horizon': prediction_horizon,
            'test_size': test_size,
            'optimize_hyperparams': optimize_hyperparams
        }
        
        return selected_algorithms, config
    
    @staticmethod
    def _train_models(selected_algorithms: list, config: dict, production_df: pd.DataFrame, failures_df: pd.DataFrame):
        """Entraîne les modèles sélectionnés."""
        evaluator = ModelEvaluator()
        
        # Préparer les données
        validation_years = st.session_state.get('validation_years', 2)
        train_prod, val_prod = split_data_for_validation(production_df, validation_years)
        train_failures, val_failures = split_data_for_validation(failures_df, validation_years)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = {}
        trained_models = {}
        
        for i, algorithm in enumerate(selected_algorithms):
            status_text.text(f"Entraînement du modèle {algorithm}...")
            progress_bar.progress((i + 1) / len(selected_algorithms))
            
            try:
                # Créer le modèle
                model = ModelFactory.create_model('maintenance_predictive', algorithm)
                
                # Préparer les features spécifiques
                features_data = MaintenanceUI._prepare_features(model, train_prod, train_failures)
                
                if features_data.empty:
                    st.error(f"❌ Impossible de préparer les features pour {algorithm}")
                    continue
                
                # Préparer les données pour l'entraînement
                X, y = model.prepare_data(features_data, 'Failure_Next_Days')
                
                # Entraîner le modèle
                train_results = model.train(
                    X, y, 
                    test_size=config['test_size'],
                    optimize_hyperparameters=config['optimize_hyperparams'],
                    random_state=42
                )
                
                # Évaluer le modèle
                X_test = train_results['X_test']
                y_test = train_results['y_test']
                y_pred = train_results['y_pred']
                
                metrics = evaluator.evaluate_model(model, X_test, y_test, algorithm)
                
                results[algorithm] = {
                    'model': model,
                    'metrics': metrics,
                    'train_results': train_results
                }
                trained_models[algorithm] = model
                
                st.success(f"✅ {algorithm} entraîné avec succès !")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'entraînement de {algorithm}: {str(e)}")
        
        progress_bar.progress(1.0)
        status_text.text("Entraînement terminé !")
        
        # Sauvegarder les résultats
        st.session_state['maintenance_results'] = results
        st.session_state['maintenance_evaluator'] = evaluator
        st.session_state['maintenance_models'] = trained_models
    
    @staticmethod
    def _prepare_features(model, train_prod: pd.DataFrame, train_failures: pd.DataFrame):
        """Prépare les features pour le modèle."""
        if hasattr(model, 'prepare_features'):
            return model.prepare_features(train_prod, train_failures)
        elif hasattr(model, 'prepare_maintenance_features'):
            return model.prepare_maintenance_features(train_prod, train_failures)
        else:
            # Fallback pour modèles génériques
            from src.models.classical_models import MaintenancePredictiveModel
            temp_model = MaintenancePredictiveModel()
            return temp_model.prepare_features(train_prod, train_failures)
    
    @staticmethod
    def _render_results():
        """Affiche les résultats des modèles entraînés."""
        if 'maintenance_results' not in st.session_state:
            return
        
        results = st.session_state['maintenance_results']
        evaluator = st.session_state['maintenance_evaluator']
        
        st.subheader("📊 Résultats des Modèles")
        
        # Comparaison des métriques
        if len(results) > 1:
            MaintenanceUI._render_model_comparison(results, evaluator)
        
        # Analyse détaillée
        MaintenanceUI._render_detailed_analysis(results, evaluator)
        
        # Prédictions en temps réel
        MaintenanceUI._render_real_time_predictions(evaluator)
    
    @staticmethod
    def _render_model_comparison(results: dict, evaluator):
        """Affiche la comparaison des modèles."""
        st.subheader("🏆 Comparaison des Performances")
        
        # Tableau de comparaison
        comparison_data = []
        for alg_name, result in results.items():
            metrics = result['metrics']
            comparison_data.append({
                'Algorithme': alg_name,
                'Accuracy': f"{metrics.get('accuracy', 0):.3f}",
                'Precision': f"{metrics.get('precision', 0):.3f}",
                'Recall': f"{metrics.get('recall', 0):.3f}",
                'F1-Score': f"{metrics.get('f1_score', 0):.3f}",
                'ROC-AUC': f"{metrics.get('roc_auc', 0):.3f}"
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Graphiques de comparaison avec téléchargement
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Comparaison F1-Score**")
            fig_comp = evaluator.plot_model_comparison('f1_score')
            display_plot_with_download(
                fig_comp,
                title="Comparaison_F1_Score_Maintenance",
                key_prefix="maintenance_f1_comp"
            )
        
        with col2:
            if len([r for r in results.values() if 'roc_auc' in r['metrics']]) > 1:
                st.markdown("**Courbes ROC**")
                fig_roc = evaluator.plot_roc_curve(list(results.keys()))
                display_plot_with_download(
                    fig_roc,
                    title="Courbes_ROC_Maintenance",
                    key_prefix="maintenance_roc_comp"
                )
    
    @staticmethod
    def _render_detailed_analysis(results: dict, evaluator):
        """Affiche l'analyse détaillée par modèle."""
        st.subheader("🔍 Analyse Détaillée par Modèle")
        
        selected_model = st.selectbox(
            "Sélectionnez un modèle pour l'analyse détaillée :",
            list(results.keys())
        )
        
        if selected_model:
            model_result = results[selected_model]
            model_metrics = model_result['metrics']
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Accuracy", f"{model_metrics.get('accuracy', 0):.3f}")
            with col2:
                st.metric("Precision", f"{model_metrics.get('precision', 0):.3f}")
            with col3:
                st.metric("Recall", f"{model_metrics.get('recall', 0):.3f}")
            with col4:
                st.metric("F1-Score", f"{model_metrics.get('f1_score', 0):.3f}")
            
            # Visualisations détaillées
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Métriques", "🎯 Matrice de Confusion", "📊 Courbe ROC", "🔍 Importance des Features"])
            
            with tab1:
                fig_metrics = plot_model_performance_metrics(model_metrics, selected_model)
                st.pyplot(fig_metrics)
            
            with tab2:
                try:
                    fig_cm = evaluator.plot_confusion_matrix(selected_model)
                    st.pyplot(fig_cm)
                except Exception as e:
                    st.error(f"Impossible d'afficher la matrice de confusion: {e}")
            
            with tab3:
                try:
                    fig_roc = evaluator.plot_roc_curve([selected_model])
                    st.pyplot(fig_roc)
                except Exception as e:
                    st.error(f"Impossible d'afficher la courbe ROC: {e}")
            
            with tab4:
                if 'feature_importance' in model_metrics:
                    fig_fi = evaluator.plot_feature_importance(selected_model)
                    st.pyplot(fig_fi)
                else:
                    st.info("Importance des features non disponible pour ce modèle.")
            
            # Rapport détaillé
            with st.expander("📋 Rapport Détaillé"):
                report = evaluator.generate_report(selected_model)
                st.text(report)
    
    @staticmethod
    def _render_real_time_predictions(evaluator):
        """Affiche les prédictions en temps réel."""
        st.subheader("🔮 Prédictions en Temps Réel")
        
        if st.button("Calculer les Probabilités de Panne Actuelles"):
            try:
                best_model_name = evaluator.get_best_model('f1_score')
                if best_model_name and best_model_name in st.session_state['maintenance_models']:
                    MaintenanceUI._calculate_current_predictions(best_model_name, evaluator)
                else:
                    st.error("Aucun modèle disponible pour les prédictions.")
            except Exception as e:
                st.error(f"Erreur lors du calcul des prédictions : {str(e)}")
    
    @staticmethod
    def _calculate_current_predictions(best_model_name: str, evaluator):
        """Calcule les prédictions actuelles."""
        from src.data_loader import load_production_data, load_pump_failures_data
        
        model = st.session_state['maintenance_models'][best_model_name]
        production_df = load_production_data()
        failures_df = load_pump_failures_data()
        
        # Préparer les données récentes
        recent_data = production_df.tail(30)
        
        features_data = MaintenanceUI._prepare_features(model, recent_data, failures_df)
        
        if not features_data.empty:
            X_recent, _ = model.prepare_data(features_data, 'Failure_Next_Days')
            X_recent = X_recent.tail(10)
            
            probabilities = model.predict_proba(X_recent)
            if probabilities is not None:
                prob_failure = probabilities[:, 1] if probabilities.shape[1] > 1 else probabilities
                dates = features_data['Date'].tail(10)
                
                # Visualiser les probabilités
                fig = plot_failure_probability_timeline(dates, prob_failure)
                st.pyplot(fig)
                
                # Alertes
                max_prob = prob_failure.max()
                if max_prob > 0.7:
                    st.error(f"🚨 ALERTE CRITIQUE : Probabilité de panne élevée ({max_prob:.1%})")
                elif max_prob > 0.5:
                    st.warning(f"⚠️ ATTENTION : Probabilité de panne modérée ({max_prob:.1%})")
                else:
                    st.success(f"✅ Situation normale (probabilité max: {max_prob:.1%})")
            else:
                st.error("Impossible de calculer les probabilités.")
        else:
            st.error("Impossible de préparer les données récentes.")