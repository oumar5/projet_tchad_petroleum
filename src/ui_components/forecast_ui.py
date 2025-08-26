import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta
from src.models.model_factory import ModelFactory
from src.models.model_evaluator import ModelEvaluator
from src.data_loader import split_data_for_validation
from src.plotting import plot_model_performance_metrics, plot_prediction_vs_actual, plot_time_series_forecast

class ForecastUI:
    """Composant UI pour la prévision de production."""
    
    @staticmethod
    def render(production_df: pd.DataFrame, dependencies: dict):
        """Affiche l'interface de prévision de production."""
        st.header("📈 Prévision de Production d'Huile")
        
        # Configuration et sélection d'algorithmes
        selected_algorithms, config = ForecastUI._render_algorithm_selection(dependencies)
        
        if not selected_algorithms:
            st.warning("⚠️ Veuillez sélectionner au moins un algorithme.")
            st.stop()
        
        # Entraînement des modèles
        if st.button("🚀 Entraîner les Modèles de Prévision", type="primary"):
            ForecastUI._train_models(selected_algorithms, config, production_df)
        
        # Affichage des résultats
        ForecastUI._render_results(config['target_column'], config['forecast_horizon'])
    
    @staticmethod
    def _render_algorithm_selection(dependencies: dict):
        """Affiche la sélection d'algorithmes et la configuration."""
        st.subheader("🎯 Sélection d'Algorithmes")
        
        available_algorithms = ModelFactory.get_available_models('production_forecast')
        algorithm_options = []
        
        for alg_name, alg_config in available_algorithms['production_forecast'].items():
            if alg_config['category'] == 'xgboost' and not dependencies['xgboost']:
                continue
            if alg_config['category'] == 'prophet' and alg_name == 'prophet' and not dependencies['prophet']:
                continue
            if alg_config['category'] == 'prophet' and alg_name == 'neuralprophet' and not dependencies['neuralprophet']:
                continue
            algorithm_options.append(alg_name)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_algorithms = st.multiselect(
                "Algorithmes à comparer :",
                algorithm_options,
                default=[algorithm_options[0]] if algorithm_options else [],
                help="Sélectionnez un ou plusieurs algorithmes pour la prévision"
            )
        
        with col2:
            forecast_horizon = st.selectbox(
                "Horizon de prévision (jours) :",
                [30, 60, 90, 180],
                index=1
            )
        
        # Configuration
        st.subheader("⚙️ Configuration des Modèles")
        
        col1, col2 = st.columns(2)
        with col1:
            test_size = st.slider(
                "Taille du jeu de test (%) :",
                min_value=10, max_value=40, value=20,
                key="forecast_test_size"
            ) / 100
        
        with col2:
            target_column = st.selectbox(
                "Variable à prédire :",
                ["Production journaliere d'huile bbl", "Production journaliere d'eau bbl"],
                index=0
            )
        
        config = {
            'forecast_horizon': forecast_horizon,
            'test_size': test_size,
            'target_column': target_column
        }
        
        return selected_algorithms, config
    
    @staticmethod
    def _train_models(selected_algorithms: list, config: dict, production_df: pd.DataFrame):
        """Entraîne les modèles sélectionnés."""
        evaluator = ModelEvaluator()
        
        # Préparer les données
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
                model = ModelFactory.create_model('production_forecast', algorithm)
                
                if algorithm in ['prophet', 'neuralprophet']:
                    # Modèles Prophet
                    X, y = model.prepare_data(train_data, config['target_column'], 'Date')
                    train_results = model.train(X, y, test_size=config['test_size'])
                else:
                    # Modèles classiques/XGBoost
                    prepared_data = ForecastUI._prepare_features(model, train_data, config['target_column'])
                    X, y = model.prepare_data(prepared_data, config['target_column'])
                    train_results = model.train(X, y, test_size=config['test_size'])
                
                # Évaluation
                if algorithm in ['prophet', 'neuralprophet']:
                    test_data = train_results['test_data']
                    y_test = test_data['y']
                    y_pred = train_results['y_pred_test']
                else:
                    X_test = train_results['X_test']
                    y_test = train_results['y_test']
                    y_pred = train_results['y_pred']
                
                metrics = evaluator.evaluate_model(model, None, y_test, algorithm)
                
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
        
        st.session_state['forecast_results'] = results
        st.session_state['forecast_evaluator'] = evaluator
        st.session_state['forecast_models'] = trained_models
    
    @staticmethod
    def _prepare_features(model, train_data: pd.DataFrame, target_column: str):
        """Prépare les features pour le modèle."""
        if hasattr(model, 'prepare_time_series_features'):
            return model.prepare_time_series_features(train_data, target_column)
        elif hasattr(model, 'prepare_production_features'):
            return model.prepare_production_features(train_data, target_column)
        else:
            return train_data.copy()
    
    @staticmethod
    def _render_results(target_column: str, forecast_horizon: int):
        """Affiche les résultats des modèles entraînés."""
        if 'forecast_results' not in st.session_state:
            return
        
        results = st.session_state['forecast_results']
        evaluator = st.session_state['forecast_evaluator']
        
        st.subheader("📊 Résultats des Modèles de Prévision")
        
        # Comparaison des métriques
        if len(results) > 1:
            ForecastUI._render_model_comparison(results, evaluator)
        
        # Analyse détaillée
        ForecastUI._render_detailed_analysis(results, evaluator)
        
        # Prévisions futures
        ForecastUI._render_future_forecasts(evaluator, target_column, forecast_horizon)
    
    @staticmethod
    def _render_model_comparison(results: dict, evaluator):
        """Affiche la comparaison des modèles."""
        st.subheader("🏆 Comparaison des Performances")
        
        comparison_data = []
        for alg_name, result in results.items():
            metrics = result['metrics']
            comparison_data.append({
                'Algorithme': alg_name,
                'R²': f"{metrics.get('r2', 0):.3f}",
                'RMSE': f"{metrics.get('rmse', 0):.2f}",
                'MAE': f"{metrics.get('mae', 0):.2f}",
                'MAPE': f"{metrics.get('mape', 0):.2f}%"
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Graphique de comparaison
        fig_comp = evaluator.plot_model_comparison('r2')
        st.pyplot(fig_comp)
    
    @staticmethod
    def _render_detailed_analysis(results: dict, evaluator):
        """Affiche l'analyse détaillée par modèle."""
        selected_model = st.selectbox(
            "Sélectionnez un modèle pour l'analyse détaillée :",
            list(results.keys()),
            key="forecast_model_select"
        )
        
        if selected_model:
            model_result = results[selected_model]
            model_metrics = model_result['metrics']
            train_results = model_result['train_results']
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("R²", f"{model_metrics.get('r2', 0):.3f}")
            with col2:
                st.metric("RMSE", f"{model_metrics.get('rmse', 0):.2f}")
            with col3:
                st.metric("MAE", f"{model_metrics.get('mae', 0):.2f}")
            with col4:
                st.metric("MAPE", f"{model_metrics.get('mape', 0):.2f}%")
            
            # Visualisations
            tab1, tab2, tab3 = st.tabs(["📈 Métriques", "🎯 Prédictions vs Réalité", "📊 Série Temporelle"])
            
            with tab1:
                fig_metrics = plot_model_performance_metrics(model_metrics, selected_model)
                st.pyplot(fig_metrics)
            
            with tab2:
                if selected_model in ['prophet', 'neuralprophet']:
                    test_data = train_results['test_data']
                    y_test = test_data['y']
                    y_pred = train_results['y_pred_test']
                else:
                    y_test = train_results['y_test']
                    y_pred = train_results['y_pred']
                
                fig_pred = plot_prediction_vs_actual(y_test, y_pred, f"Prévision - {selected_model}")
                st.pyplot(fig_pred)
            
            with tab3:
                if selected_model in ['prophet', 'neuralprophet']:
                    test_dates = train_results['test_data']['ds'] if 'test_data' in train_results else None
                    if test_dates is not None:
                        y_test = train_results['test_data']['y']
                        y_pred = train_results['y_pred_test']
                        fig_ts = plot_time_series_forecast(test_dates, y_test, y_pred)
                        st.pyplot(fig_ts)
                    else:
                        st.info("Données de série temporelle non disponibles.")
                else:
                    st.info("Visualisation de série temporelle disponible uniquement pour Prophet/NeuralProphet.")
    
    @staticmethod
    def _render_future_forecasts(evaluator, target_column: str, forecast_horizon: int):
        """Affiche les prévisions futures."""
        st.subheader("🔮 Prévisions Futures")
        
        if st.button("Générer des Prévisions", key="generate_forecast"):
            try:
                best_model_name = evaluator.get_best_model('r2')
                if best_model_name and best_model_name in st.session_state['forecast_models']:
                    ForecastUI._generate_forecasts(best_model_name, target_column, forecast_horizon)
                else:
                    st.error("Aucun modèle disponible pour les prévisions.")
            except Exception as e:
                st.error(f"Erreur lors de la génération des prévisions : {str(e)}")
    
    @staticmethod
    def _generate_forecasts(best_model_name: str, target_column: str, forecast_horizon: int):
        """Génère les prévisions futures."""
        from src.data_loader import load_production_data
        
        model = st.session_state['forecast_models'][best_model_name]
        production_df = load_production_data()
        
        if best_model_name in ['prophet', 'neuralprophet']:
            # Prévisions Prophet
            predictions = model.predict(periods=forecast_horizon)
            
            # Créer les dates futures
            last_date = production_df['Date'].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=forecast_horizon,
                freq='D'
            )
            
            # Afficher les prévisions
            forecast_df = pd.DataFrame({
                'Date': future_dates,
                'Prévision': predictions
            })
            
            st.success(f"🎯 Prévisions générées pour les {forecast_horizon} prochains jours")
            st.dataframe(forecast_df.head(10))
            
            # Graphique des prévisions
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Données historiques récentes
            recent_data = production_df.tail(90)
            ax.plot(recent_data['Date'], recent_data[target_column], 
                   label='Historique', color='blue', linewidth=2)
            
            # Prévisions
            ax.plot(future_dates, predictions, 
                   label='Prévisions', color='red', linewidth=2, linestyle='--')
            
            ax.set_title(f'Prévisions de {target_column}')
            ax.set_xlabel('Date')
            ax.set_ylabel('Production (bbl)')
            ax.legend()
            ax.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            st.pyplot(fig)
            
        else:
            st.info("💡 Prévisions futures en cours de développement pour les modèles non-Prophet...")