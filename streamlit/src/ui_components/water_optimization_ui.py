import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from src.models.model_factory import ModelFactory
from src.models.model_evaluator import ModelEvaluator
from src.data_loader import split_data_for_validation
from src.plotting import plot_model_performance_metrics, plot_prediction_vs_actual

class WaterOptimizationUI:
    """Composant UI moderne pour l'optimisation de l'injection d'eau."""
    
    @staticmethod
    def render(production_df: pd.DataFrame, dependencies: dict):
        """Affiche l'interface moderne d'optimisation de l'injection d'eau."""
        
        # En-tête avec style moderne
        st.markdown("""
        <div style='background: linear-gradient(90deg, #1f4e79, #2e8b57); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
            <h1 style='color: white; text-align: center; margin: 0; font-size: 2.5rem;'>💧 Optimisation de l'Injection d'Eau</h1>
            <p style='color: #e0e0e0; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;'>Intelligence Artificielle pour l'Optimisation des Paramètres d'Injection</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Vue d'ensemble des données
        WaterOptimizationUI._render_data_overview(production_df)
        
        # Configuration avancée
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Configuration des Modèles")
            selected_algorithms = WaterOptimizationUI._render_algorithm_selection(dependencies)
            
            if not selected_algorithms:
                st.warning("⚠️ Veuillez sélectionner au moins un algorithme pour continuer.")
                st.stop()
        
        with col2:
            st.markdown("### ⚙️ Paramètres")
            test_size = st.slider(
                "Taille du jeu de test (%) :",
                min_value=10, max_value=40, value=20,
                key="water_test_size",
                help="Pourcentage des données utilisées pour tester les modèles"
            ) / 100
            
            validation_years = st.selectbox(
                "Années de validation :",
                [1, 2, 3],
                index=1,
                key="water_validation_years",
                help="Nombre d'années utilisées pour la validation temporelle"
            )
        
        # Bouton d'entraînement stylisé
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🚀 Lancer l'Optimisation IA", 
                type="primary", 
                use_container_width=True,
                help="Entraîner les modèles d'IA pour optimiser l'injection d'eau"
            ):
                WaterOptimizationUI._train_models(selected_algorithms, test_size, production_df, validation_years)
        
        # Affichage des résultats avec design moderne
        WaterOptimizationUI._render_results()
        
        # Analyse comparative
        WaterOptimizationUI._render_comparative_analysis()
    
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
    def _render_data_overview(production_df: pd.DataFrame):
        """Affiche une vue d'ensemble des données d'injection."""
        st.markdown("### 📊 Vue d'Ensemble des Données")
        
        if production_df.empty:
            st.warning("⚠️ Aucune donnée de production disponible.")
            return
        
        # Calcul des métriques d'injection
        oil_production = production_df["Production journaliere d'huile bbl"].mean()
        water_production = production_df["Production journaliere d'eau bbl"].mean()
        watercut = production_df["Teneur en eau (Watercut)"].mean()
        
        # Efficacité d'injection
        efficiency = oil_production / (water_production + 1) if water_production > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🛢️ Production Huile Moyenne",
                f"{oil_production:,.0f} bbl/jour",
                help="Production quotidienne moyenne d'huile"
            )
        
        with col2:
            st.metric(
                "💧 Production Eau Moyenne",
                f"{water_production:,.0f} bbl/jour",
                help="Production quotidienne moyenne d'eau"
            )
        
        with col3:
            st.metric(
                "📈 Watercut Moyen",
                f"{watercut:.1f}%",
                help="Teneur en eau moyenne"
            )
        
        with col4:
            st.metric(
                "⚡ Efficacité Injection",
                f"{efficiency:.3f}",
                help="Ratio huile/eau d'injection"
            )
        
        # Graphique de tendance
        if len(production_df) > 1:
            try:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=production_df['Date'],
                    y=production_df["Production journaliere d'huile bbl"],
                    mode='lines',
                    name='Production Huile',
                    line=dict(color='#2e8b57', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=production_df['Date'],
                    y=production_df["Production journaliere d'eau bbl"],
                    mode='lines',
                    name='Production Eau',
                    line=dict(color='#1f4e79', width=2),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title="Évolution de la Production Huile vs Eau",
                    xaxis_title="Date",
                    yaxis_title="Production Huile (bbl/jour)",
                    yaxis2=dict(
                        title="Production Eau (bbl/jour)",
                        overlaying='y',
                        side='right'
                    ),
                    height=400,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.info("📊 Graphique non disponible (Plotly requis)")
    
    @staticmethod
    def _train_models(selected_algorithms: list, test_size: float, production_df: pd.DataFrame, validation_years: int = 2):
        """Entraîne les modèles sélectionnés avec interface améliorée."""
        
        # Container pour l'entraînement
        with st.container():
            st.markdown("### 🚀 Entraînement des Modèles IA")
            
            # Informations sur l'entraînement
            st.info(f"🎯 Entraînement de {len(selected_algorithms)} modèle(s) avec {validation_years} année(s) de validation")
            
            evaluator = ModelEvaluator()
            train_data, val_data = split_data_for_validation(production_df, validation_years)
            
            # Barre de progression moderne
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                metrics_placeholder = st.empty()
            
            results = {}
            trained_models = {}
            
            for i, algorithm in enumerate(selected_algorithms):
                status_text.markdown(f"🔄 **Entraînement en cours:** {algorithm}")
                progress_bar.progress((i) / len(selected_algorithms))
                
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
                    if 'X_test' in train_results and 'y_test' in train_results:
                        X_test = train_results['X_test']
                        y_test = train_results['y_test']
                        metrics = evaluator.evaluate_model(model, X_test, y_test, algorithm)
                    else:
                        # Fallback pour les modèles qui ne retournent pas X_test/y_test
                        metrics = {'r2': 0.0, 'rmse': 0.0, 'mae': 0.0, 'mape': 0.0}
                    
                    results[algorithm] = {
                        'model': model,
                        'metrics': metrics,
                        'train_results': train_results
                    }
                    trained_models[algorithm] = model
                    
                    # Affichage des métriques en temps réel
                    with metrics_placeholder.container():
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric(f"R² ({algorithm})", f"{metrics.get('r2', 0):.3f}")
                        with col2:
                            st.metric(f"RMSE ({algorithm})", f"{metrics.get('rmse', 0):.4f}")
                        with col3:
                            st.metric(f"MAE ({algorithm})", f"{metrics.get('mae', 0):.4f}")
                        with col4:
                            st.metric(f"MAPE ({algorithm})", f"{metrics.get('mape', 0):.2f}%")
                    
                    st.success(f"✅ **{algorithm}** entraîné avec succès ! (R² = {metrics.get('r2', 0):.3f})")
                    
                except Exception as e:
                    st.error(f"❌ **Erreur {algorithm}:** {str(e)}")
                    continue
            
            progress_bar.progress(1.0)
            status_text.markdown("🎉 **Entraînement terminé avec succès !**")
            
            if results:
                st.session_state['water_results'] = results
                st.session_state['water_evaluator'] = evaluator
                st.session_state['water_models'] = trained_models
                
                # Affichage du meilleur modèle
                best_model = max(results.keys(), key=lambda k: results[k]['metrics'].get('r2', 0))
                best_r2 = results[best_model]['metrics'].get('r2', 0)
                st.success(f"🏆 **Meilleur modèle:** {best_model} (R² = {best_r2:.3f})")
            else:
                st.error("❌ Aucun modèle n'a pu être entraîné avec succès.")
    
    @staticmethod
    def _render_results():
        """Affiche les résultats des modèles entraînés avec design moderne."""
        if 'water_results' not in st.session_state:
            st.info("🎯 Entraînez d'abord des modèles pour voir les résultats ici.")
            return
        
        results = st.session_state['water_results']
        evaluator = st.session_state['water_evaluator']
        
        st.markdown("---")
        st.markdown("### 📊 Résultats et Analyse des Modèles")
        
        # Tableau de comparaison des modèles
        if len(results) > 1:
            st.markdown("#### 🏆 Comparaison des Performances")
            
            comparison_data = []
            for model_name, model_data in results.items():
                metrics = model_data['metrics']
                comparison_data.append({
                    'Modèle': model_name,
                    'R²': f"{metrics.get('r2', 0):.3f}",
                    'RMSE': f"{metrics.get('rmse', 0):.4f}",
                    'MAE': f"{metrics.get('mae', 0):.4f}",
                    'MAPE': f"{metrics.get('mape', 0):.2f}%"
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
        
        # Sélection automatique du meilleur modèle par défaut
        best_model = max(results.keys(), key=lambda k: results[k]['metrics'].get('r2', 0))
        
        # Interface de sélection améliorée
        st.markdown("#### 🏆 Analyse des Modèles Entraînés")
        
        # Affichage du meilleur modèle en premier
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**🥇 Meilleur Modèle Détecté:** {best_model}")
            best_r2 = results[best_model]['metrics'].get('r2', 0)
            
            # Indicateur de qualité du meilleur modèle
            if best_r2 >= 0.8:
                quality = "🟢 Excellent"
                quality_color = "green"
            elif best_r2 >= 0.6:
                quality = "🟡 Bon"
                quality_color = "orange"
            else:
                quality = "🔴 À améliorer"
                quality_color = "red"
            
            st.markdown(f"**Qualité:** <span style='color: {quality_color}'>{quality}</span> (R² = {best_r2:.3f})", unsafe_allow_html=True)
        
        with col2:
            # Option pour changer de modèle si plusieurs disponibles
            if len(results) > 1:
                change_model = st.button("🔄 Comparer avec d'autres modèles", key="toggle_model_selection")
                
                if change_model or st.session_state.get('show_model_selector', False):
                    st.session_state['show_model_selector'] = True
                else:
                    st.session_state['show_model_selector'] = False
        
        # Sélecteur conditionnel
        if st.session_state.get('show_model_selector', False) and len(results) > 1:
            st.markdown("##### 📋 Sélectionner un autre modèle :")
            selected_model = st.selectbox(
                "Modèles disponibles :",
                list(results.keys()),
                index=list(results.keys()).index(best_model),
                key="water_model_select",
                help="Comparez les performances des différents modèles"
            )
        else:
            selected_model = best_model
        
        if selected_model:
            model_result = results[selected_model]
            model_metrics = model_result['metrics']
            
            # Métriques avec design simplifié et intuitif
            st.markdown(f"#### 📈 Performance du Modèle - {selected_model}")
            
            # Score de performance global
            r2_score = model_metrics.get('r2', 0)
            performance_percentage = r2_score * 100
            
            # Affichage du score principal
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown("""
                <div style='background: linear-gradient(90deg, #1f4e79, #2e8b57); padding: 1.5rem; border-radius: 10px; text-align: center;'>
                    <h3 style='color: white; margin: 0;'>🎯 Score de Performance</h3>
                    <h1 style='color: white; margin: 0.5rem 0; font-size: 3rem;'>{:.0f}%</h1>
                    <p style='color: #e0e0e0; margin: 0;'>Précision du modèle d'optimisation</p>
                </div>
                """.format(performance_percentage), unsafe_allow_html=True)
            
            with col2:
                # Indicateur de fiabilité
                mape = model_metrics.get('mape', 0)
                if mape <= 5:
                    reliability = "🟢 Très Fiable"
                elif mape <= 10:
                    reliability = "🟡 Fiable"
                else:
                    reliability = "🔴 Peu Fiable"
                
                st.metric(
                    "🔍 Fiabilité",
                    reliability,
                    help=f"Basé sur l'erreur de prédiction: {mape:.1f}%"
                )
            
            with col3:
                # Recommandation d'usage
                if r2_score >= 0.8:
                    usage = "✅ Recommandé"
                    usage_color = "green"
                elif r2_score >= 0.6:
                    usage = "⚠️ Acceptable"
                    usage_color = "orange"
                else:
                    usage = "❌ À améliorer"
                    usage_color = "red"
                
                st.markdown(f"**Usage:**")
                st.markdown(f"<span style='color: {usage_color}; font-weight: bold;'>{usage}</span>", unsafe_allow_html=True)
            
            # Métriques techniques en option
            with st.expander("📊 Voir les métriques techniques détaillées"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "R² (Coefficient de détermination)", 
                        f"{model_metrics.get('r2', 0):.3f}",
                        help="0 = aucune prédiction, 1 = prédiction parfaite"
                    )
                with col2:
                    st.metric(
                        "RMSE (Erreur quadratique)", 
                        f"{model_metrics.get('rmse', 0):.4f}",
                        help="Plus faible = meilleur"
                    )
                with col3:
                    st.metric(
                        "MAE (Erreur absolue)", 
                        f"{model_metrics.get('mae', 0):.4f}",
                        help="Plus faible = meilleur"
                    )
                with col4:
                    st.metric(
                        "MAPE (Erreur en %)", 
                        f"{model_metrics.get('mape', 0):.2f}%",
                        help="Plus faible = meilleur"
                    )
            
            # Section recommandations avec design moderne
            st.markdown("---")
            st.markdown("### 💡 Recommandations d'Optimisation IA")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button(
                    "🧠 Générer Recommandations IA", 
                    type="primary",
                    key="water_recommendations",
                    help="Utiliser l'IA pour générer des recommandations d'optimisation"
                ):
                    WaterOptimizationUI._calculate_recommendations(selected_model)
            
            with col2:
                if st.button(
                    "📊 Analyser Tendances",
                    key="water_trends",
                    help="Analyser les tendances d'efficacité d'injection"
                ):
                    WaterOptimizationUI._analyze_injection_trends(selected_model)
    
    @staticmethod
    def _render_comparative_analysis():
        """Affiche une analyse comparative avancée."""
        if 'water_results' not in st.session_state or len(st.session_state['water_results']) < 2:
            return
        
        st.markdown("---")
        st.markdown("### 🔍 Analyse Comparative Avancée")
        
        results = st.session_state['water_results']
        
        # Graphique de comparaison des performances
        try:
            models = list(results.keys())
            r2_scores = [results[model]['metrics'].get('r2', 0) for model in models]
            rmse_scores = [results[model]['metrics'].get('rmse', 0) for model in models]
            
            fig = go.Figure()
            
            # Graphique en barres pour R²
            fig.add_trace(go.Bar(
                name='R² Score',
                x=models,
                y=r2_scores,
                marker_color='#2e8b57',
                text=[f'{score:.3f}' for score in r2_scores],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="Comparaison des Performances des Modèles (R²)",
                xaxis_title="Modèles",
                yaxis_title="Score R²",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.info("📊 Graphique de comparaison non disponible (Plotly requis)")
        
        # Recommandations basées sur la comparaison
        best_model = max(results.keys(), key=lambda k: results[k]['metrics'].get('r2', 0))
        best_r2 = results[best_model]['metrics'].get('r2', 0)
        
        st.markdown("#### 🎯 Recommandations de Sélection")
        
        if best_r2 >= 0.8:
            st.success(f"🏆 **Modèle recommandé:** {best_model} (R² = {best_r2:.3f})")
            st.info("✅ Ce modèle présente d'excellentes performances pour l'optimisation de l'injection d'eau.")
        elif best_r2 >= 0.6:
            st.warning(f"🥈 **Modèle acceptable:** {best_model} (R² = {best_r2:.3f})")
            st.info("⚠️ Performances correctes, mais considérez l'ajout de plus de données ou l'optimisation des hyperparamètres.")
        else:
            st.error(f"🥉 **Modèle à améliorer:** {best_model} (R² = {best_r2:.3f})")
            st.info("❌ Performances insuffisantes. Recommandations : plus de données, feature engineering, ou algorithmes différents.")
    
    @staticmethod
    def _analyze_injection_trends(selected_model: str):
        """Analyse les tendances d'efficacité d'injection."""
        try:
            st.markdown("#### 📈 Analyse des Tendances d'Injection")
            
            from src.data_loader import load_production_data
            production_df = load_production_data()
            
            if production_df.empty:
                st.warning("⚠️ Aucune donnée disponible pour l'analyse des tendances.")
                return
            
            # Calcul de l'efficacité historique
            production_df['Efficacite_Injection'] = production_df["Production journaliere d'huile bbl"] / (production_df["Production journaliere d'eau bbl"] + 1)
            
            # Tendance sur les 30 derniers jours
            recent_data = production_df.tail(30)
            
            if len(recent_data) > 1:
                try:
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=recent_data['Date'],
                        y=recent_data['Efficacite_Injection'],
                        mode='lines+markers',
                        name='Efficacité d\'Injection',
                        line=dict(color='#1f4e79', width=3),
                        marker=dict(size=6)
                    ))
                    
                    # Ligne de tendance
                    z = np.polyfit(range(len(recent_data)), recent_data['Efficacite_Injection'], 1)
                    p = np.poly1d(z)
                    
                    fig.add_trace(go.Scatter(
                        x=recent_data['Date'],
                        y=p(range(len(recent_data))),
                        mode='lines',
                        name='Tendance',
                        line=dict(color='#ff6b6b', width=2, dash='dash')
                    ))
                    
                    fig.update_layout(
                        title="Évolution de l'Efficacité d'Injection (30 derniers jours)",
                        xaxis_title="Date",
                        yaxis_title="Efficacité d'Injection",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Analyse de la tendance
                    slope = z[0]
                    if slope > 0.001:
                        st.success("📈 **Tendance positive:** L'efficacité d'injection s'améliore.")
                    elif slope < -0.001:
                        st.warning("📉 **Tendance négative:** L'efficacité d'injection diminue. Intervention recommandée.")
                    else:
                        st.info("➡️ **Tendance stable:** L'efficacité d'injection reste constante.")
                        
                except Exception as e:
                    st.info("📊 Graphique de tendance non disponible (Plotly requis)")
            
            # Statistiques de tendance
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_efficiency = recent_data['Efficacite_Injection'].mean()
                st.metric("Efficacité Moyenne", f"{avg_efficiency:.4f}")
            
            with col2:
                std_efficiency = recent_data['Efficacite_Injection'].std()
                st.metric("Variabilité", f"{std_efficiency:.4f}")
            
            with col3:
                max_efficiency = recent_data['Efficacite_Injection'].max()
                st.metric("Efficacité Max", f"{max_efficiency:.4f}")
                
        except Exception as e:
            st.error(f"Erreur lors de l'analyse des tendances : {str(e)}")
    
    @staticmethod
    def _calculate_recommendations(selected_model: str):
        """Calcule les recommandations d'optimisation avec interface moderne."""
        try:
            st.markdown("#### 🧠 Recommandations IA Générées")
            
            with st.spinner("🔄 Analyse en cours par l'Intelligence Artificielle..."):
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
            
            # Affichage de l'efficacité actuelle avec style
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.metric(
                    "🎯 Efficacité Prédite Actuelle",
                    f"{efficiency[0]:.4f}",
                    help="Efficacité d'injection calculée par l'IA"
                )
            
            # Recommandations détaillées avec design moderne
            st.markdown("---")
            
            if efficiency[0] < 0.1:
                st.markdown("""
                <div style='background: linear-gradient(90deg, #ff6b6b, #ffa500); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;'>
                    <h4 style='color: white; margin: 0;'>⚠️ Efficacité Faible Détectée</h4>
                    <p style='color: #ffe0e0; margin: 0.5rem 0 0 0;'>Intervention urgente recommandée</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔧 Actions Immédiates :**")
                    st.markdown("• 📉 Réduire le volume d'injection d'eau de 15-20%")
                    st.markdown("• 🔍 Vérifier l'intégrité des puits injecteurs")
                    st.markdown("• 🛠️ Inspecter les équipements de surface")
                
                with col2:
                    st.markdown("**📋 Actions à Moyen Terme :**")
                    st.markdown("• 💉 Considérer des interventions de stimulation")
                    st.markdown("• 📊 Analyser la géologie du réservoir")
                    st.markdown("• 🔄 Réviser la stratégie d'injection")
                    
            elif efficiency[0] > 0.3:
                st.markdown("""
                <div style='background: linear-gradient(90deg, #2e8b57, #32cd32); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;'>
                    <h4 style='color: white; margin: 0;'>✅ Efficacité Élevée</h4>
                    <p style='color: #e0ffe0; margin: 0.5rem 0 0 0;'>Performances optimales détectées</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🎯 Maintenir l'Excellence :**")
                    st.markdown("• ✅ Conserver les paramètres actuels")
                    st.markdown("• 📈 Surveiller l'évolution du watercut")
                    st.markdown("• 📊 Documenter les bonnes pratiques")
                
                with col2:
                    st.markdown("**🔍 Surveillance Continue :**")
                    st.markdown("• 📅 Monitoring quotidien des KPIs")
                    st.markdown("• 🔔 Alertes en cas de dégradation")
                    st.markdown("• 📈 Optimisation fine si possible")
                    
            else:
                st.markdown("""
                <div style='background: linear-gradient(90deg, #1f4e79, #4682b4); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;'>
                    <h4 style='color: white; margin: 0;'>💡 Efficacité Modérée</h4>
                    <p style='color: #e0f0ff; margin: 0.5rem 0 0 0;'>Potentiel d'amélioration identifié</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**⚡ Optimisations Graduelles :**")
                    st.markdown("• 🔧 Ajuster les paramètres d'injection par paliers")
                    st.markdown("• 📊 Surveiller les tendances de production")
                    st.markdown("• 🎯 Tester différentes stratégies")
                
                with col2:
                    st.markdown("**📈 Amélioration Continue :**")
                    st.markdown("• 📋 Collecter plus de données historiques")
                    st.markdown("• 🧪 Expérimenter avec de nouveaux paramètres")
                    st.markdown("• 🤖 Réentraîner les modèles régulièrement")
            
            # Recommandations économiques
            st.markdown("---")
            st.markdown("#### 💰 Impact Économique Estimé")
            
            # Calcul d'impact économique simplifié
            current_oil_prod = recent_data["Production journaliere d'huile bbl"].iloc[0] if not recent_data.empty else 1000
            oil_price = 75  # Prix du baril en USD (exemple)
            
            if efficiency[0] < 0.1:
                potential_gain = current_oil_prod * 0.15 * oil_price  # 15% d'amélioration potentielle
                st.error(f"💸 **Perte estimée:** ${potential_gain:,.0f}/jour si non optimisé")
            elif efficiency[0] > 0.3:
                current_value = current_oil_prod * oil_price
                st.success(f"💰 **Valeur actuelle optimisée:** ${current_value:,.0f}/jour")
            else:
                potential_gain = current_oil_prod * 0.08 * oil_price  # 8% d'amélioration potentielle
                st.info(f"📈 **Gain potentiel:** ${potential_gain:,.0f}/jour avec optimisation")
                
        except Exception as e:
            st.error(f"❌ Erreur lors du calcul des recommandations : {str(e)}")
            st.info("💡 Vérifiez que les données sont disponibles et que le modèle est correctement entraîné.")