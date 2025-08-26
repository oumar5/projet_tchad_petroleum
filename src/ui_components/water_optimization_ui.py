import streamlit as st
import pandas as pd
from src.models.model_factory import ModelFactory
from src.models.model_evaluator import ModelEvaluator
from src.data_loader import split_data_for_validation
from src.plotting import plot_model_performance_metrics, plot_prediction_vs_actual

class WaterOptimizationUI:
    """Composant UI pour l'optimisation de l'injection d'eau."""
    
    @staticmethod
    def render(production_df: pd.DataFrame, dependencies: dict):
        """Affiche l'interface d'optimisation de l'injection d'eau."""
        st.header("💧 Optimisation de l'Injection d'Eau")
        
        # Sélection d'algorithmes
        selected_algorithms = WaterOptimizationUI._render_algorithm_selection(dependencies)
        
        if not selected_algorithms:
            st.warning("⚠️ Veuillez sélectionner au moins un algorithme.")
            st.stop()
        
        # Configuration
        test_size = st.slider(
            "Taille du jeu de test (%) :",
            min_value=10, max_value=40, value=20,
            key="water_test_size"
        ) / 100
        
        # Entraînement
        if st.button("🚀 Entraîner les Modèles d'Optimisation", type="primary"):
            WaterOptimizationUI._train_models(selected_algorithms, test_size, production_df)
        
        # Affichage des résultats
        WaterOptimizationUI._render_results()
    
    @staticmethod
    def _render_algorithm_selection(dependencies: dict):
        """Affiche la sélection d'algorithmes."""
        available_algorithms = ModelFactory.get_available_models('water_injection')
        algorithm_options = []
        
        for alg_name, alg_config in available_algorithms['water_injection'].items():
            if alg_config['category'] == 'xgboost' and not dependencies['xgboost']:
                continue
            algorithm_options.append(alg_name)
        
        selected_algorithms = st.multiselect(
            "Algorithmes à comparer :",
            algorithm_options,
            default=[algorithm_options[0]] if algorithm_options else []
        )
        
        return selected_algorithms
    
    @staticmethod
    def _train_models(selected_algorithms: list, test_size: float, production_df: pd.DataFrame):
        """Entraîne les modèles sélectionnés."""
        evaluator = ModelEvaluator()
        
        validation_years = st.session_state.get('validation_years', 2)
        train_data, val_data = split_data_for_validation(production_df, validation_years)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = {}
        trained_models = {}
        
        for i, algorithm in enumerate(selected_algorithms):
            status_text.text(f"Entraînement du modèle {algorithm}...")
            progress_bar.progress((i + 1) / len(selected_algorithms))
            
            try:
                model = ModelFactory.create_model('water_injection', algorithm)
                
                # Préparer les features spécifiques
                if hasattr(model, 'prepare_injection_features'):
                    prepared_data = model.prepare_injection_features(train_data)
                    target_col = 'Oil_Water_Efficiency'
                else:
                    prepared_data = train_data.copy()
                    # Calculer l'efficacité comme target
                    prepared_data['Oil_Water_Efficiency'] = prepared_data["Production journaliere d'huile bbl"] / (prepared_data["Production journaliere d'eau bbl"] + 1)
                    target_col = 'Oil_Water_Efficiency'
                
                X, y = model.prepare_data(prepared_data, target_col)
                train_results = model.train(X, y, test_size=test_size)
                
                # Évaluation
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
        
        st.session_state['water_results'] = results
        st.session_state['water_evaluator'] = evaluator
        st.session_state['water_models'] = trained_models
    
    @staticmethod
    def _render_results():
        """Affiche les résultats des modèles entraînés."""
        if 'water_results' not in st.session_state:
            return
        
        results = st.session_state['water_results']
        evaluator = st.session_state['water_evaluator']
        
        st.subheader("📊 Résultats des Modèles d'Optimisation")
        
        selected_model = st.selectbox(
            "Sélectionnez un modèle :",
            list(results.keys()),
            key="water_model_select"
        )
        
        if selected_model:
            model_result = results[selected_model]
            model_metrics = model_result['metrics']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("R²", f"{model_metrics.get('r2', 0):.3f}")
            with col2:
                st.metric("RMSE", f"{model_metrics.get('rmse', 0):.4f}")
            with col3:
                st.metric("MAE", f"{model_metrics.get('mae', 0):.4f}")
            with col4:
                st.metric("MAPE", f"{model_metrics.get('mape', 0):.2f}%")
            
            # Recommandations
            st.subheader("💡 Recommandations d'Optimisation")
            
            if st.button("Calculer les Recommandations", key="water_recommendations"):
                WaterOptimizationUI._calculate_recommendations(selected_model)
    
    @staticmethod
    def _calculate_recommendations(selected_model: str):
        """Calcule les recommandations d'optimisation."""
        try:
            from src.data_loader import load_production_data
            
            model = st.session_state['water_models'][selected_model]
            production_df = load_production_data()
            
            # Préparer les données actuelles
            if hasattr(model, 'prepare_injection_features'):
                recent_data = model.prepare_injection_features(production_df).tail(1)
                target_col = 'Oil_Water_Efficiency'
            else:
                recent_data = production_df.tail(1).copy()
                recent_data['Oil_Water_Efficiency'] = recent_data["Production journaliere d'huile bbl"] / (recent_data["Production journaliere d'eau bbl"] + 1)
                target_col = 'Oil_Water_Efficiency'
            
            X_current, _ = model.prepare_data(recent_data, target_col)
            
            if hasattr(model, 'optimize_injection'):
                efficiency = model.optimize_injection(X_current)
            else:
                efficiency = model.predict(X_current)
            
            st.success(f"🎯 Efficacité prédite actuelle : {efficiency[0]:.4f}")
            
            # Recommandations basées sur l'efficacité
            if efficiency[0] < 0.1:
                st.warning("⚠️ Efficacité faible. Recommandations :")
                st.write("- Réduire le volume d'injection d'eau")
                st.write("- Vérifier l'intégrité des puits")
                st.write("- Considérer des interventions de stimulation")
            elif efficiency[0] > 0.3:
                st.success("✅ Efficacité élevée. Recommandations :")
                st.write("- Maintenir les paramètres actuels")
                st.write("- Surveiller l'évolution du watercut")
            else:
                st.info("💡 Efficacité modérée. Recommandations :")
                st.write("- Optimiser graduellement les paramètres")
                st.write("- Surveiller les tendances de production")
                
        except Exception as e:
            st.error(f"Erreur lors du calcul des recommandations : {str(e)}")