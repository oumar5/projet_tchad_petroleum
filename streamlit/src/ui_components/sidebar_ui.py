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
        # En-tête moderne et compact
        st.sidebar.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, #1f4e79, #2e8b57); border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <h2 style='color: white; margin: 0; font-size: 1.8rem; font-weight: 600;'>🛢️ Tchad Petroleum</h2>
            <p style='color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 13px; font-weight: 400;'>Intelligence Artificielle • Analyse Prédictive</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Statut des données en premier (information critique)
        SidebarUI._render_data_status_compact(production_df, failures_df)
        
        # Navigation principale simplifiée
        st.sidebar.markdown("### 🧭 Navigation")
        
        # Options de navigation regroupées logiquement
        nav_options = {
            "🏠 Tableau de Bord": {
                "description": "Vue d'ensemble et KPIs",
                "category": "main",
                "status": "ready"
            },
            "📊 Analyse des Données": {
                "description": "Production et pannes",
                "category": "analysis", 
                "status": "ready" if not production_df.empty else "warning"
            },
            "🤖 Intelligence Artificielle": {
                "description": "Modèles prédictifs",
                "category": "ai",
                "status": "ready"
            },
            "📚 Documentation": {
                "description": "Guides et aide",
                "category": "help",
                "status": "ready"
            }
        }
        
        # Sélection avec interface améliorée
        selected_page = st.sidebar.radio(
            "Choisissez une section :",
            list(nav_options.keys()),
            format_func=lambda x: SidebarUI._format_nav_option_modern(x, nav_options[x]),
            key="main_navigation",
            help="Naviguez entre les différentes sections de l'application"
        )
        
        # Sous-navigation contextuelle
        if selected_page == "📊 Analyse des Données":
            selected_analysis = SidebarUI._render_analysis_navigation(production_df, failures_df)
            return selected_analysis
        elif selected_page == "🤖 Intelligence Artificielle":
            selected_ai = SidebarUI._render_ai_navigation()
            return selected_ai
        elif selected_page == "🏠 Tableau de Bord":
            return "🏠 Accueil"
        
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
    def _render_data_status_compact(production_df: pd.DataFrame, failures_df: pd.DataFrame):
        """Affiche un statut compact des données."""
        st.sidebar.markdown("### 📊 État des Données")
        
        # Calcul des métriques
        prod_count = len(production_df) if not production_df.empty else 0
        failure_count = len(failures_df) if not failures_df.empty else 0
        
        # Période des données
        if not production_df.empty:
            date_range = production_df['Date'].max() - production_df['Date'].min()
            period_days = date_range.days
        else:
            period_days = 0
        
        # Affichage en colonnes
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.metric(
                "📈 Production",
                f"{prod_count:,}",
                help="Nombre de points de données de production"
            )
        
        with col2:
            st.metric(
                "🔧 Pannes",
                f"{failure_count}",
                help="Nombre d'événements de panne enregistrés"
            )
        
        # Période en bas
        if period_days > 0:
            st.sidebar.info(f"📅 **Période couverte :** {period_days} jours")
        else:
            st.sidebar.warning("⚠️ Aucune donnée disponible")
    
    @staticmethod
    def _format_nav_option_modern(option: str, config: Dict[str, Any]) -> str:
        """Formate les options de navigation avec style moderne."""
        status_icons = {
            "ready": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        status_icon = status_icons.get(config["status"], "⚪")
        description = config.get("description", "")
        
        return f"{option}\n{description}"
    
    @staticmethod
    def _render_analysis_navigation(production_df: pd.DataFrame, failures_df: pd.DataFrame) -> str:
        """Affiche la navigation pour l'analyse des données."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### 📊 Type d'Analyse")
        
        analysis_options = {
            "📈 Production": {
                "available": not production_df.empty,
                "description": "Analyse de la production d'huile"
            },
            "🔧 Pannes": {
                "available": not failures_df.empty,
                "description": "Historique des pannes"
            }
        }
        
        # Sélection du type d'analyse
        available_options = []
        for option, config in analysis_options.items():
            if config["available"]:
                available_options.append(option)
            else:
                st.sidebar.warning(f"⚠️ {option} : Données non disponibles")
        
        if available_options:
            selected_analysis = st.sidebar.radio(
                "Choisissez le type d'analyse :",
                available_options,
                key="analysis_type"
            )
            
            # Mapper vers les noms de pages originaux
            mapping = {
                "📈 Production": "📈 Analyse de Production",
                "🔧 Pannes": "🔧 Analyse des Pannes"
            }
            
            return mapping.get(selected_analysis, selected_analysis)
        else:
            st.sidebar.error("❌ Aucune donnée disponible pour l'analyse")
            return "🏠 Accueil"
    
    @staticmethod
    def _render_ai_navigation() -> str:
        """Affiche la navigation pour l'IA avec interface moderne."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### 🤖 Modules IA")
        
        # Vérification des dépendances
        dependencies = ModelFactory.check_dependencies()
        
        # Options IA organisées par catégorie
        ai_categories = {
            "🏠 Vue d'Ensemble": {
                "description": "Dashboard et configuration",
                "status": "ready",
                "deps": []
            },
            "🔧 Maintenance Prédictive": {
                "description": "Prédiction des pannes",
                "status": "ready",
                "deps": ["scikit-learn"]
            },
            "📈 Prévision Production": {
                "description": "Prédiction de production",
                "status": "ready" if dependencies.get('prophet', False) else "warning",
                "deps": ["prophet"]
            },
            "💧 Optimisation Injection": {
                "description": "Optimisation des paramètres",
                "status": "ready",
                "deps": ["scikit-learn"]
            },
            "📊 Comparaison Modèles": {
                "description": "Analyse comparative",
                "status": "ready",
                "deps": []
            }
        }
        
        # Sélection avec statut des dépendances
        selected_ai = st.sidebar.selectbox(
            "Sélectionnez un module IA :",
            list(ai_categories.keys()),
            format_func=lambda x: SidebarUI._format_ai_option(x, ai_categories[x], dependencies),
            key="ai_module"
        )
        
        # Affichage des informations du module
        if selected_ai in ai_categories:
            config = ai_categories[selected_ai]
            SidebarUI._render_ai_module_info(config, dependencies)
        
        # Mapper vers les noms de pages originaux
        mapping = {
            "🏠 Vue d'Ensemble": "🏠 Accueil",
            "🔧 Maintenance Prédictive": "🔧 Maintenance Prédictive",
            "📈 Prévision Production": "📈 Prévision de Production",
            "💧 Optimisation Injection": "💧 Optimisation Injection d'Eau",
            "📊 Comparaison Modèles": "📊 Comparaison de Modèles"
        }
        
        return mapping.get(selected_ai, selected_ai)
    
    @staticmethod
    def _format_ai_option(option: str, config: Dict[str, Any], dependencies: Dict[str, bool]) -> str:
        """Formate les options IA avec statut des dépendances."""
        # Vérifier les dépendances
        deps_ok = all(dependencies.get(dep, True) for dep in config["deps"] if dep in dependencies)
        
        if not config["deps"] or deps_ok:
            status_icon = "✅"
        else:
            status_icon = "⚠️"
        
        return f"{status_icon} {option}"
    
    @staticmethod
    def _render_ai_module_info(config: Dict[str, Any], dependencies: Dict[str, bool]):
        """Affiche les informations sur le module IA sélectionné."""
        # Description du module
        st.sidebar.info(f"💡 {config['description']}")
        
        # Statut des dépendances si nécessaire
        if config["deps"]:
            missing_deps = [dep for dep in config["deps"] if not dependencies.get(dep, True)]
            if missing_deps:
                st.sidebar.warning(f"⚠️ Dépendances manquantes : {', '.join(missing_deps)}")
            else:
                st.sidebar.success("✅ Toutes les dépendances sont disponibles")
    
    @staticmethod
    def _format_nav_option(option: str, config: Dict[str, Any]) -> str:
        """Formate les options de navigation avec statut (méthode legacy)."""
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
        """Affiche des actions rapides modernes dans la sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚡ Actions Rapides")
        
        # Actions principales en boutons complets
        if st.sidebar.button("🔄 Actualiser les Données", key="refresh_data", use_container_width=True, help="Recharger toutes les données et vider le cache"):
            st.cache_data.clear()
            st.rerun()
        
        if st.sidebar.button("📖 Ouvrir Documentation", key="open_docs_main", use_container_width=True, help="Accéder aux guides et à la documentation"):
            st.session_state['selected_doc_page'] = True
            st.rerun()
        
        # Informations système compactes
        st.sidebar.markdown("---")
        
        # Statut système en expander
        with st.sidebar.expander("ℹ️ Informations Système"):
            st.markdown("""
            **Version :** 2.0.0  
            **Architecture :** Modulaire  
            **IA :** Modèles Multiples  
            **Interface :** Streamlit  
            
            **Documentation Disponible :**
            • Guide Utilisateur Complet
            • Architecture Technique
            • Modèles d'IA et ML
            • Interface et Visualisations
            • Guide de Développement
            • Déploiement et Production
            """)
        
        # Footer moderne et compact
        st.sidebar.markdown("""
        <div style='text-align: center; margin-top: 20px; padding: 10px; background: rgba(0,0,0,0.05); border-radius: 8px;'>
            <p style='margin: 0; color: #666; font-size: 11px; font-weight: 500;'>🛢️ Tchad Petroleum • v2.0</p>
            <p style='margin: 0; color: #888; font-size: 10px;'>Développé avec ❤️ • IA & Analytics</p>
        </div>
        """, unsafe_allow_html=True)