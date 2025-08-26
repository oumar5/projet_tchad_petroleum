import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Imports des modules personnalisés
from src.data_loader import (
    load_production_data, load_pump_failures_data, load_interventions_data,
    split_data_for_validation, prepare_data_for_modeling,
    calculate_production_kpis, calculate_failure_kpis
)
from src.predictive_models import (
    PredictiveMaintenanceModel, ProductionForecastModel, 
    WaterInjectionOptimizer, ModelEvaluator
)
from src.plotting import (
    plot_model_performance_metrics, plot_confusion_matrix, plot_roc_curve,
    plot_feature_importance, plot_prediction_vs_actual, plot_time_series_forecast,
    plot_failure_probability_timeline, plot_production_components, plot_kpi_dashboard
)

# Configuration de la page
st.set_page_config(page_title="Modélisation Prédictive", layout="wide")
st.title("🔮 Modélisation Prédictive")

# Sidebar pour la navigation
st.sidebar.title("Navigation")
model_type = st.sidebar.selectbox(
    "Choisissez le type de modèle :",
    ["🏠 Accueil", "🔧 Maintenance Prédictive", "📈 Prévision de Production", "💧 Optimisation Injection d'Eau", "📊 Dashboard KPIs"]
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

# ==================== PAGE D'ACCUEIL ====================
if model_type == "🏠 Accueil":
    st.header("Bienvenue dans la Section Modélisation Prédictive")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Aperçu des Données")
        
        # Statistiques générales
        st.metric("Nombre d'enregistrements de production", len(production_df))
        st.metric("Nombre de pannes enregistrées", len(failures_df) if not failures_df.empty else 0)
        
        if not production_df.empty:
            date_range = production_df['Date'].max() - production_df['Date'].min()
            st.metric("Période couverte (jours)", date_range.days)
    
    with col2:
        st.subheader("🤖 Modèles Disponibles")
        
        st.info("""
        **🔧 Maintenance Prédictive**
        - Prédiction des pannes de pompes
        - Analyse des patterns de défaillance
        - Recommandations de maintenance
        """)
        
        st.info("""
        **📈 Prévision de Production**
        - Prédiction de la production d'huile
        - Analyse des tendances
        - Planification de la production
        """)
        
        st.info("""
        **💧 Optimisation Injection d'Eau**
        - Optimisation des paramètres d'injection
        - Maximisation de la récupération
        - Réduction des coûts
        """)
    
    # Graphique de vue d'ensemble
    st.subheader("📈 Vue d'Ensemble de la Production")
    if not production_df.empty:
        fig = plot_production_components(production_df)
        st.pyplot(fig)
    
    # Configuration de validation
    st.subheader("⚙️ Configuration de Validation")
    validation_years = st.slider(
        "Nombre d'années pour la validation :",
        min_value=1, max_value=5, value=2,
        help="Les N dernières années seront utilisées pour valider les modèles"
    )
    st.session_state['validation_years'] = validation_years
    
    st.success(f"✅ Configuration sauvegardée : {validation_years} années pour la validation")

# ==================== MAINTENANCE PRÉDICTIVE ====================
elif model_type == "🔧 Maintenance Prédictive":
    st.header("🔧 Maintenance Prédictive des Pompes")
    
    if failures_df.empty:
        st.warning("⚠️ Aucune donnée de panne disponible pour l'entraînement du modèle.")
        st.stop()
    
    # Configuration du modèle
    st.subheader("⚙️ Configuration du Modèle")
    
    col1, col2 = st.columns(2)
    with col1:
        prediction_horizon = st.selectbox(
            "Horizon de prédiction :",
            [7, 14, 30],
            index=0,
            help="Nombre de jours à l'avance pour prédire les pannes"
        )
    
    with col2:
        test_size = st.slider(
            "Taille du jeu de test (%) :",
            min_value=10, max_value=40, value=20
        ) / 100
    
    # Bouton d'entraînement
    if st.button("🚀 Entraîner le Modèle de Maintenance Prédictive", type="primary"):
        with st.spinner("Entraînement du modèle en cours..."):
            try:
                # Initialiser le modèle
                maintenance_model = PredictiveMaintenanceModel()
                
                # Diviser les données pour validation
                validation_years = st.session_state.get('validation_years', 2)
                train_prod, val_prod = split_data_for_validation(production_df, validation_years)
                train_failures, val_failures = split_data_for_validation(failures_df, validation_years)
                
                # Entraîner le modèle
                metrics, X_test, y_test, y_pred = maintenance_model.train(
                    train_prod, train_failures, test_size=test_size
                )
                
                # Sauvegarder le modèle dans la session
                st.session_state['maintenance_model'] = maintenance_model
                st.session_state['maintenance_metrics'] = metrics
                st.session_state['maintenance_test_data'] = (X_test, y_test, y_pred)
                
                st.success("✅ Modèle entraîné avec succès !")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'entraînement : {str(e)}")
    
    # Affichage des résultats si le modèle est entraîné
    if 'maintenance_model' in st.session_state:
        st.subheader("📊 Résultats du Modèle")
        
        # Métriques de performance
        metrics = st.session_state['maintenance_metrics']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Accuracy", f"{metrics['accuracy']:.3f}")
        with col2:
            st.metric("Precision", f"{metrics['precision']:.3f}")
        with col3:
            st.metric("Recall", f"{metrics['recall']:.3f}")
        with col4:
            st.metric("F1-Score", f"{metrics['f1_score']:.3f}")
        
        # Visualisations
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Métriques", "🎯 Matrice de Confusion", "📊 Courbe ROC", "🔍 Importance des Features"])
        
        with tab1:
            fig = plot_model_performance_metrics(metrics, "Maintenance Prédictive")
            st.pyplot(fig)
        
        with tab2:
            X_test, y_test, y_pred = st.session_state['maintenance_test_data']
            fig = plot_confusion_matrix(y_test, y_pred)
            st.pyplot(fig)
        
        with tab3:
            # Calculer les probabilités pour la courbe ROC
            model = st.session_state['maintenance_model']
            y_prob = model.predict_failure_probability(X_test)
            fig = plot_roc_curve(y_test, y_prob)
            st.pyplot(fig)
        
        with tab4:
            if hasattr(model, 'feature_importance') and model.feature_importance is not None:
                fig = plot_feature_importance(model.feature_importance)
                st.pyplot(fig)
        
        # Prédictions en temps réel
        st.subheader("🔮 Prédictions en Temps Réel")
        
        if st.button("Calculer les Probabilités de Panne Actuelles"):
            try:
                # Prendre les dernières données
                recent_data = production_df.tail(30)
                features_data = model.prepare_features(recent_data, failures_df)
                
                if not features_data.empty:
                    # Sélectionner les features nécessaires
                    feature_columns = [
                        "Production journaliere d'huile bbl",
                        "Production journaliere d'eau bbl",
                        "Teneur en eau (Watercut)",
                        "Nombre des puits actifs",
                        'Production_MA_7',
                        'Production_MA_30',
                        'Production_Std_7',
                        'Watercut_MA_7',
                        'Production_Trend',
                        'Days_Since_Start'
                    ]
                    
                    X_recent = features_data[feature_columns].tail(10)
                    probabilities = model.predict_failure_probability(X_recent)
                    dates = features_data['Date'].tail(10)
                    
                    # Visualiser les probabilités
                    fig = plot_failure_probability_timeline(dates, probabilities)
                    st.pyplot(fig)
                    
                    # Alertes
                    max_prob = probabilities.max()
                    if max_prob > 0.7:
                        st.error(f"🚨 ALERTE CRITIQUE : Probabilité de panne élevée ({max_prob:.1%})")
                    elif max_prob > 0.5:
                        st.warning(f"⚠️ ATTENTION : Probabilité de panne modérée ({max_prob:.1%})")
                    else:
                        st.success(f"✅ Situation normale (probabilité max: {max_prob:.1%})")
                        
            except Exception as e:
                st.error(f"Erreur lors du calcul des prédictions : {str(e)}")

# ==================== PRÉVISION DE PRODUCTION ====================
elif model_type == "📈 Prévision de Production":
    st.header("📈 Prévision de Production d'Huile")
    
    # Configuration du modèle
    st.subheader("⚙️ Configuration du Modèle")
    
    col1, col2 = st.columns(2)
    with col1:
        forecast_days = st.selectbox(
            "Horizon de prévision (jours) :",
            [30, 60, 90, 180],
            index=1
        )
    
    with col2:
        test_size = st.slider(
            "Taille du jeu de test (%) :",
            min_value=10, max_value=40, value=20,
            key="forecast_test_size"
        ) / 100
    
    # Bouton d'entraînement
    if st.button("🚀 Entraîner le Modèle de Prévision", type="primary"):
        with st.spinner("Entraînement du modèle de prévision..."):
            try:
                # Initialiser le modèle
                forecast_model = ProductionForecastModel()
                
                # Diviser les données pour validation
                validation_years = st.session_state.get('validation_years', 2)
                train_data, val_data = split_data_for_validation(production_df, validation_years)
                
                # Entraîner le modèle
                metrics, X_test, y_test, y_pred, test_dates = forecast_model.train(
                    train_data, test_size=test_size
                )
                
                # Sauvegarder le modèle
                st.session_state['forecast_model'] = forecast_model
                st.session_state['forecast_metrics'] = metrics
                st.session_state['forecast_test_data'] = (X_test, y_test, y_pred, test_dates)
                
                st.success("✅ Modèle de prévision entraîné avec succès !")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'entraînement : {str(e)}")
    
    # Affichage des résultats
    if 'forecast_model' in st.session_state:
        st.subheader("📊 Résultats du Modèle de Prévision")
        
        # Métriques
        metrics = st.session_state['forecast_metrics']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("RMSE", f"{metrics['rmse']:.2f}")
        with col2:
            st.metric("MAE", f"{metrics['mae']:.2f}")
        with col3:
            st.metric("R²", f"{metrics['r2']:.3f}")
        with col4:
            st.metric("MSE", f"{metrics['mse']:.2f}")
        
        # Visualisations
        tab1, tab2, tab3 = st.tabs(["📈 Métriques", "🎯 Prédictions vs Réalité", "📊 Série Temporelle"])
        
        with tab1:
            fig = plot_model_performance_metrics(metrics, "Prévision de Production")
            st.pyplot(fig)
        
        with tab2:
            X_test, y_test, y_pred, test_dates = st.session_state['forecast_test_data']
            fig = plot_prediction_vs_actual(y_test, y_pred, "Prévision de Production")
            st.pyplot(fig)
        
        with tab3:
            fig = plot_time_series_forecast(test_dates, y_test, y_pred)
            st.pyplot(fig)
        
        # Prévisions futures
        st.subheader("🔮 Prévisions Futures")
        
        if st.button("Générer des Prévisions"):
            try:
                model = st.session_state['forecast_model']
                
                # Préparer les données récentes
                recent_data = model.prepare_time_series_features(
                    production_df, "Production journaliere d'huile bbl"
                ).tail(1)
                
                # Sélectionner les features
                feature_columns = [
                    'Year', 'Month', 'Day', 'DayOfWeek', 'DayOfYear',
                    "Nombre des puits actifs",
                    "Production journaliere d'eau bbl",
                    "Teneur en eau (Watercut)"
                ]
                
                # Ajouter les features de lag et moyennes mobiles
                lag_features = [col for col in recent_data.columns if '_lag_' in col or '_MA_' in col or '_Std_' in col or '_Trend_' in col]
                feature_columns.extend(lag_features)
                
                X_recent = recent_data[feature_columns]
                forecast = model.forecast(X_recent)
                
                st.success(f"🎯 Prévision pour demain : {forecast[0]:.2f} barils")
                
                # Générer des prévisions pour plusieurs jours
                future_dates = pd.date_range(
                    start=production_df['Date'].max() + timedelta(days=1),
                    periods=forecast_days,
                    freq='D'
                )
                
                # Note: Pour une vraie prévision multi-pas, il faudrait implémenter
                # une logique plus complexe qui utilise les prédictions précédentes
                st.info("💡 Prévisions multi-pas en cours de développement...")
                
            except Exception as e:
                st.error(f"Erreur lors de la génération des prévisions : {str(e)}")

# ==================== OPTIMISATION INJECTION D'EAU ====================
elif model_type == "💧 Optimisation Injection d'Eau":
    st.header("💧 Optimisation de l'Injection d'Eau")
    
    # Configuration
    st.subheader("⚙️ Configuration du Modèle")
    
    test_size = st.slider(
        "Taille du jeu de test (%) :",
        min_value=10, max_value=40, value=20,
        key="water_test_size"
    ) / 100
    
    # Bouton d'entraînement
    if st.button("🚀 Entraîner le Modèle d'Optimisation", type="primary"):
        with st.spinner("Entraînement du modèle d'optimisation..."):
            try:
                # Initialiser le modèle
                water_optimizer = WaterInjectionOptimizer()
                
                # Diviser les données
                validation_years = st.session_state.get('validation_years', 2)
                train_data, val_data = split_data_for_validation(production_df, validation_years)
                
                # Entraîner le modèle
                metrics, X_test, y_test, y_pred = water_optimizer.train(
                    train_data, test_size=test_size
                )
                
                # Sauvegarder
                st.session_state['water_optimizer'] = water_optimizer
                st.session_state['water_metrics'] = metrics
                st.session_state['water_test_data'] = (X_test, y_test, y_pred)
                
                st.success("✅ Modèle d'optimisation entraîné avec succès !")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'entraînement : {str(e)}")
    
    # Affichage des résultats
    if 'water_optimizer' in st.session_state:
        st.subheader("📊 Résultats du Modèle d'Optimisation")
        
        # Métriques
        metrics = st.session_state['water_metrics']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("RMSE", f"{metrics['rmse']:.4f}")
        with col2:
            st.metric("MAE", f"{metrics['mae']:.4f}")
        with col3:
            st.metric("R²", f"{metrics['r2']:.3f}")
        with col4:
            st.metric("MSE", f"{metrics['mse']:.6f}")
        
        # Visualisations
        tab1, tab2 = st.tabs(["📈 Métriques", "🎯 Prédictions vs Réalité"])
        
        with tab1:
            fig = plot_model_performance_metrics(metrics, "Optimisation Injection d'Eau")
            st.pyplot(fig)
        
        with tab2:
            X_test, y_test, y_pred = st.session_state['water_test_data']
            fig = plot_prediction_vs_actual(y_test, y_pred, "Efficacité Injection d'Eau")
            st.pyplot(fig)
        
        # Recommandations
        st.subheader("💡 Recommandations d'Optimisation")
        
        if st.button("Calculer les Recommandations"):
            try:
                optimizer = st.session_state['water_optimizer']
                
                # Préparer les données actuelles
                recent_data = optimizer.prepare_injection_features(production_df).tail(1)
                
                feature_columns = [
                    "Production journaliere d'huile bbl",
                    "Production journaliere d'eau bbl",
                    "Teneur en eau (Watercut)",
                    "Nombre des puits actifs",
                    'Watercut_Change',
                    'Production_Change',
                    'Water_Production_Ratio'
                ]
                
                # Ajouter les moyennes mobiles
                ma_features = [col for col in recent_data.columns if '_MA_' in col]
                feature_columns.extend(ma_features)
                
                X_current = recent_data[feature_columns]
                efficiency = optimizer.optimize_injection(X_current)
                
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

# ==================== DASHBOARD KPIs ====================
elif model_type == "📊 Dashboard KPIs":
    st.header("📊 Dashboard des Indicateurs de Performance")
    
    # Calculer les KPIs
    production_kpis = calculate_production_kpis(production_df)
    failure_kpis = calculate_failure_kpis(failures_df)
    
    # Affichage du dashboard
    if production_kpis or failure_kpis:
        fig = plot_kpi_dashboard(production_kpis, failure_kpis)
        st.pyplot(fig)
    
    # KPIs détaillés
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 KPIs de Production")
        
        if 'oil_production' in production_kpis:
            oil_kpis = production_kpis['oil_production']
            st.metric("Production totale d'huile", f"{oil_kpis['total']:,.0f} bbl")
            st.metric("Production moyenne/jour", f"{oil_kpis['average_daily']:.0f} bbl")
            st.metric("Production max/jour", f"{oil_kpis['max_daily']:,.0f} bbl")
            st.metric("Écart-type", f"{oil_kpis['std_daily']:.0f} bbl")
        
        if 'watercut' in production_kpis:
            wc_kpis = production_kpis['watercut']
            st.metric("Watercut actuel", f"{wc_kpis['current']:.1f}%")
            st.metric("Watercut moyen", f"{wc_kpis['average']:.1f}%")
    
    with col2:
        st.subheader("🔧 KPIs de Maintenance")
        
        if failure_kpis:
            st.metric("Nombre total de pannes", failure_kpis.get('total_failures', 0))
            
            if 'mtbf_days' in failure_kpis:
                st.metric("MTBF (jours)", f"{failure_kpis['mtbf_days']:.0f}")
            
            if 'failures_by_block' in failure_kpis:
                st.write("**Pannes par bloc :**")
                for block, count in failure_kpis['failures_by_block'].items():
                    st.write(f"- {block}: {count} pannes")
    
    # Analyse comparative
    st.subheader("📊 Analyse Comparative")
    
    if st.button("Générer Rapport d'Analyse"):
        st.write("### 📋 Rapport d'Analyse Automatique")
        
        # Analyse de la production
        if 'oil_production' in production_kpis:
            oil_kpis = production_kpis['oil_production']
            cv = oil_kpis['std_daily'] / oil_kpis['average_daily']
            
            if cv > 0.3:
                st.warning(f"⚠️ **Variabilité élevée** de la production (CV = {cv:.2f})")
            else:
                st.success(f"✅ **Production stable** (CV = {cv:.2f})")
        
        # Analyse du watercut
        if 'watercut' in production_kpis:
            wc_kpis = production_kpis['watercut']
            if wc_kpis['current'] > 80:
                st.error("🚨 **Watercut critique** - Intervention urgente recommandée")
            elif wc_kpis['current'] > 60:
                st.warning("⚠️ **Watercut élevé** - Surveillance renforcée")
            else:
                st.success("✅ **Watercut acceptable**")
        
        # Analyse des pannes
        if 'mtbf_days' in failure_kpis:
            mtbf = failure_kpis['mtbf_days']
            if mtbf < 30:
                st.error(f"🚨 **MTBF critique** ({mtbf:.0f} jours) - Maintenance préventive urgente")
            elif mtbf < 90:
                st.warning(f"⚠️ **MTBF faible** ({mtbf:.0f} jours) - Améliorer la maintenance")
            else:
                st.success(f"✅ **MTBF acceptable** ({mtbf:.0f} jours)")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    🛢️ Tchad Petroleum Company - Système de Modélisation Prédictive
    <br>Développé avec ❤️ pour l'optimisation des opérations pétrolières
</div>
""", unsafe_allow_html=True)