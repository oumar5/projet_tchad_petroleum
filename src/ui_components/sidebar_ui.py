import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.models.model_factory import ModelFactory

class SidebarUI:
    """Composant UI pour une sidebar intuitive et informative."""
    
    @staticmethod
    def render(production_df: pd.DataFrame, failures_df: pd.DataFrame) -> str:
        """
        Affiche une sidebar améliorée avec navigation et informations contextuelles.
        
        Returns:
            str: Le type de modèle sélectionné
        """
        # Configuration de la sidebar
        st.sidebar.markdown("""
        <div style='text-align: center; padding: 10px; background: linear-gradient(90deg, #1f4e79, #2e8b57); border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0;'>🛢️ Tchad Petroleum</h2>
            <p style='color: #e0e0e0; margin: 5px 0 0 0; font-size: 14px;'>Système d'Analyse Prédictive</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Informations sur les données
        SidebarUI._render_data_status(production_df, failures_df)
        
        # Navigation principale
        st.sidebar.markdown("### 🎯 Navigation Principale")
        
        # Options de navigation avec descriptions
        nav_options = {
            "🏠 Accueil": {
                "description": "Vue d'ensemble et configuration",
                "icon": "🏠",
                "status": "ready"
            },
            "📈 Analyse de Production": {
                "description": "Visualisation des données de production",
                "icon": "📈",
                "status": "ready" if not production_df.empty else "warning"
            },
            "🔧 Analyse des Pannes": {
                "description": "Historique et répartition des pannes",
                "icon": "🔧",
                "status": "ready" if not failures_df.empty else "warning"
            },
            "🔮 Modélisation Prédictive": {
                "description": "Modèles ML avancés",
                "icon": "🔮",
                "status": "ready"
            },
            "📚 Documentation": {
                "description": "Guides et documentation technique",
                "icon": "📚",
                "status": "ready"
            }
        }
        
        # Sélection avec radio buttons stylisés
        selected_page = st.sidebar.radio(
            "Sélectionnez une section :",
            list(nav_options.keys()),
            format_func=lambda x: SidebarUI._format_nav_option(x, nav_options[x]),
            key="main_navigation"
        )
        
        # Navigation secondaire pour la modélisation prédictive
        if selected_page == "🔮 Modélisation Prédictive":
            selected_model = SidebarUI._render_ml_navigation()
            return selected_model
        
        return selected_page
    
    @staticmethod
    def _render_data_status(production_df: pd.DataFrame, failures_df: pd.DataFrame):
        """Affiche le statut des données dans la sidebar."""
        # Ajouter CSS pour l'adaptation au mode sombre
        st.sidebar.markdown("""
        <style>
        :root {
            --background-color: rgba(240, 242, 246, 0.8);
            --border-color: rgba(0, 0, 0, 0.1);
            --text-color: #262730;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
        }
        
        [data-theme="dark"] {
            --background-color: rgba(38, 39, 48, 0.8);
            --border-color: rgba(255, 255, 255, 0.1);
            --text-color: #fafafa;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --info-color: #2196f3;
        }
        
        /* Détection automatique du mode sombre */
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: rgba(38, 39, 48, 0.8);
                --border-color: rgba(255, 255, 255, 0.1);
                --text-color: #fafafa;
                --success-color: #4caf50;
                --warning-color: #ff9800;
                --info-color: #2196f3;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown("### 📊 Statut des Données")
        
        # Statut production
        prod_status = "✅" if not production_df.empty else "❌"
        prod_count = len(production_df) if not production_df.empty else 0
        
        # Statut pannes
        failure_status = "✅" if not failures_df.empty else "❌"
        failure_count = len(failures_df) if not failures_df.empty else 0
        
        # Période des données
        if not production_df.empty:
            date_range = production_df['Date'].max() - production_df['Date'].min()
            period_text = f"{date_range.days} jours"
        else:
            period_text = "N/A"
        
        # Affichage compact avec adaptation au mode sombre
        st.sidebar.markdown(f"""
        <div class='data-status-card' style='background: var(--background-color, rgba(240, 242, 246, 0.9)); 
                    backdrop-filter: blur(10px); 
                    border: 1px solid var(--border-color, rgba(0, 0, 0, 0.1)); 
                    padding: 12px; 
                    border-radius: 8px; 
                    margin-bottom: 15px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 8px; color: var(--text-color, inherit);'>
                <span style='font-weight: 500; opacity: 0.9;'>📈 Production:</span>
                <span style='font-weight: 600; color: var(--success-color, #28a745);'>{prod_status} {prod_count:,} pts</span>
            </div>
            <div style='display: flex; justify-content: space-between; margin-bottom: 8px; color: var(--text-color, inherit);'>
                <span style='font-weight: 500; opacity: 0.9;'>🔧 Pannes:</span>
                <span style='font-weight: 600; color: var(--warning-color, #ffc107);'>{failure_status} {failure_count} evt</span>
            </div>
            <div style='display: flex; justify-content: space-between; color: var(--text-color, inherit);'>
                <span style='font-weight: 500; opacity: 0.9;'>📅 Période:</span>
                <span style='font-weight: 600; color: var(--info-color, #17a2b8);'>{period_text}</span>
            </div>
        </div>
        
        <style>
        /* Styles spécifiques pour le mode sombre de Streamlit */
        .stApp[data-theme='dark'] .data-status-card,
        .stApp.dark-theme .data-status-card {{
            background: rgba(38, 39, 48, 0.9) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #fafafa !important;
        }}
        
        .stApp[data-theme='dark'] .data-status-card span,
        .stApp.dark-theme .data-status-card span {{
            color: #fafafa !important;
        }}
        
        /* Détection automatique du mode sombre du système */
        @media (prefers-color-scheme: dark) {{
            .data-status-card {{
                background: rgba(38, 39, 48, 0.9) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                color: #fafafa !important;
            }}
            .data-status-card span {{
                color: #fafafa !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def _format_nav_option(option: str, config: Dict[str, Any]) -> str:
        """Formate les options de navigation avec statut."""
        status_icon = {
            "ready": "🟢",
            "warning": "🟡",
            "error": "🔴"
        }.get(config["status"], "⚪")
        
        return f"{status_icon} {option}"
    
    @staticmethod
    def _render_ml_navigation() -> str:
        """Affiche la navigation pour la modélisation prédictive."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤖 Modules ML")
        
        # Vérification des dépendances
        dependencies = ModelFactory.check_dependencies()
        
        ml_options = {
            "🏠 Accueil": {
                "description": "Configuration et vue d'ensemble",
                "status": "ready",
                "deps": []
            },
            "🔧 Maintenance Prédictive": {
                "description": "Prédiction des pannes de pompes",
                "status": "ready",
                "deps": ["scikit-learn"]
            },
            "📈 Prévision de Production": {
                "description": "Prédiction de production d'huile",
                "status": "ready" if dependencies.get('prophet', False) else "warning",
                "deps": ["prophet", "neuralprophet"]
            },
            "💧 Optimisation Injection d'Eau": {
                "description": "Optimisation des paramètres",
                "status": "ready",
                "deps": ["scikit-learn"]
            },
            "📊 Comparaison de Modèles": {
                "description": "Analyse comparative",
                "status": "ready",
                "deps": []
            },
            "📋 Dashboard KPIs": {
                "description": "Indicateurs de performance",
                "status": "ready",
                "deps": []
            }
        }
        
        # Sélection avec descriptions
        selected_option = st.sidebar.selectbox(
            "Choisissez un module :",
            list(ml_options.keys()),
            format_func=lambda x: SidebarUI._format_ml_option(x, ml_options[x], dependencies),
            key="ml_navigation"
        )
        
        # Affichage des informations sur le module sélectionné
        if selected_option in ml_options:
            config = ml_options[selected_option]
            SidebarUI._render_module_info(config, dependencies)
        
        return selected_option
    
    @staticmethod
    def _format_ml_option(option: str, config: Dict[str, Any], dependencies: Dict[str, bool]) -> str:
        """Formate les options ML avec statut des dépendances."""
        # Vérifier les dépendances
        deps_ok = all(dependencies.get(dep, True) for dep in config["deps"] if dep in dependencies)
        
        if not config["deps"]:
            status_icon = "🟢"
        elif deps_ok:
            status_icon = "🟢"
        else:
            status_icon = "🟡"
        
        return f"{status_icon} {option}"
    
    @staticmethod
    def _render_module_info(config: Dict[str, Any], dependencies: Dict[str, bool]):
        """Affiche les informations sur le module sélectionné."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ℹ️ Informations")
        
        # Description
        st.sidebar.markdown(f"**Description :** {config['description']}")
        
        # Dépendances
        if config["deps"]:
            st.sidebar.markdown("**Dépendances :**")
            for dep in config["deps"]:
                if dep in dependencies:
                    status = "✅" if dependencies[dep] else "❌"
                    st.sidebar.markdown(f"- {status} {dep}")
                else:
                    st.sidebar.markdown(f"- ✅ {dep}")
        
        # Conseils d'utilisation
        SidebarUI._render_usage_tips(config)
    
    @staticmethod
    def _render_usage_tips(config: Dict[str, Any]):
        """Affiche des conseils d'utilisation contextuels."""
        tips = {
            "🏠 Accueil": "💡 Configurez les paramètres globaux ici",
            "🔧 Maintenance Prédictive": "💡 Utilisez plusieurs algorithmes pour comparer",
            "📈 Prévision de Production": "💡 Prophet excelle pour les séries temporelles",
            "💧 Optimisation Injection d'Eau": "💡 Analysez l'efficacité huile/eau",
            "📊 Comparaison de Modèles": "💡 Entraînez d'abord des modèles",
            "📋 Dashboard KPIs": "💡 Vue d'ensemble des performances"
        }
        
        # Trouver le tip correspondant
        for key, tip in tips.items():
            if key in config.get("description", "") or any(word in key for word in config.get("description", "").split()):
                st.sidebar.info(tip)
                break
    
    @staticmethod
    def render_quick_actions():
        """Affiche des actions rapides dans la sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚡ Actions Rapides")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🔄 Actualiser", key="refresh_data"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("📥 Export", key="export_data"):
                st.sidebar.success("Export en cours...")
        
        # Accès rapide à la documentation
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📚 Accès Rapide")
        
        if st.sidebar.button("📖 Ouvrir Documentation", key="open_docs_main", use_container_width=True):
            st.session_state['selected_doc_page'] = True
            st.rerun()
        
        # Informations sur la documentation disponible
        st.sidebar.markdown("""
        **Documentation Disponible :**
        • Guide Utilisateur
        • Architecture Système
        • Modèles Prédictifs
        • Interface UI
        • Guide Développement
        • Guide Déploiement
        • Collecte des Données
        • Nettoyage des Données
        """)
        
        # Footer de la sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        <div style='text-align: center; color: #666; font-size: 12px;'>
            <p>v2.0.0 • Architecture Modulaire</p>
            <p>Développé avec ❤️</p>
        </div>
        """, unsafe_allow_html=True)