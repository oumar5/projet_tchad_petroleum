# 📊 Guide de l'Interface Utilisateur et Visualisations

## Vue d'Ensemble

Ce document détaille l'interface utilisateur Streamlit et les composants de visualisation du système de modélisation prédictive de Tchad Petroleum Company.

## 🎯 Objectifs de l'Interface

- **Simplicité** : Interface intuitive pour tous les utilisateurs
- **Interactivité** : Contrôles dynamiques et temps réel
- **Visualisation** : Graphiques clairs et informatifs
- **Performance** : Réactivité et fluidité d'utilisation
- **Accessibilité** : Design responsive et ergonomique

## 🏗️ Architecture de l'Interface

### Structure Modulaire

```
src/ui_components/
├── __init__.py
├── sidebar_ui.py           # Barre latérale et navigation
├── home_ui.py              # Page d'accueil
├── dashboard_ui.py         # Tableau de bord KPIs
├── maintenance_ui.py       # Interface maintenance prédictive
├── forecast_ui.py          # Interface prévision production
├── water_optimization_ui.py # Interface optimisation injection
├── model_comparison_ui.py  # Comparaison de modèles
└── training_progress.py    # Suivi d'entraînement
```

### Composants de Visualisation

```
src/plotting/
├── __init__.py
├── basic_plots.py          # Graphiques de base
├── dashboard_plots.py      # Graphiques tableau de bord
├── model_plots.py          # Visualisations ML
├── timeseries_plots.py     # Séries temporelles
└── download_utils.py       # Téléchargement graphiques
```

## 🖥️ Pages Principales

### Page d'Accueil

#### 🏠 HomeUI
```python
class HomeUI:
    @staticmethod
    def render():
        """Affiche la page d'accueil avec vue d'ensemble."""
        st.title("🏠 Accueil - Tchad Petroleum")
        
        # Vue d'ensemble du système
        HomeUI._render_system_overview()
        
        # Statistiques rapides
        HomeUI._render_quick_stats()
        
        # Navigation rapide
        HomeUI._render_quick_navigation()
```

#### 📊 Fonctionnalités
- **Vue d'ensemble** du système
- **Statistiques rapides** de production
- **Navigation rapide** vers les modules
- **Statut** des données et modèles
- **Alertes** et notifications

### Tableau de Bord

#### 📈 DashboardUI
```python
class DashboardUI:
    @staticmethod
    def render(production_df: pd.DataFrame, failures_df: pd.DataFrame):
        """Affiche le tableau de bord principal."""
        # KPIs principaux
        DashboardUI._render_main_kpis(production_df)
        
        # Graphiques de tendances
        DashboardUI._render_trend_charts(production_df)
        
        # Alertes et recommandations
        DashboardUI._render_alerts_panel(failures_df)
```

#### 📊 Composants
- **KPIs temps réel** : Production, efficacité, pannes
- **Graphiques de tendances** : Évolution temporelle
- **Cartes de performance** : Métriques par bloc
- **Alertes intelligentes** : Notifications automatiques
- **Recommandations** : Actions suggérées

### Maintenance Prédictive

#### 🔧 MaintenanceUI
```python
class MaintenanceUI:
    @staticmethod
    def render(production_df: pd.DataFrame, failures_df: pd.DataFrame, dependencies: dict):
        """Interface de maintenance prédictive."""
        # Sélection des algorithmes
        selected_algorithms = MaintenanceUI._render_algorithm_selection(dependencies)
        
        # Configuration des paramètres
        config = MaintenanceUI._render_configuration_panel()
        
        # Entraînement des modèles
        if st.button("🚀 Entraîner les Modèles"):
            MaintenanceUI._train_models(selected_algorithms, config, production_df, failures_df)
        
        # Affichage des résultats
        MaintenanceUI._render_results()
```

#### 🛠️ Fonctionnalités
- **Sélection d'algorithmes** : Random Forest, Gradient Boosting, XGBoost
- **Configuration** : Horizon de prédiction, paramètres
- **Entraînement** : Processus interactif avec progress bar
- **Métriques** : Accuracy, Precision, Recall, F1-Score
- **Visualisations** : Matrices de confusion, courbes ROC
- **Prédictions temps réel** : Alertes de maintenance

### Prévision de Production

#### 📈 ForecastUI
```python
class ForecastUI:
    @staticmethod
    def render(production_df: pd.DataFrame, dependencies: dict):
        """Interface de prévision de production."""
        # Sélection des modèles
        selected_algorithms = ForecastUI._render_algorithm_selection(dependencies)
        
        # Configuration des prévisions
        config = ForecastUI._render_forecast_configuration()
        
        # Entraînement et prévisions
        if st.button("📊 Générer les Prévisions"):
            ForecastUI._train_models(selected_algorithms, config, production_df)
        
        # Résultats et visualisations
        ForecastUI._render_results(config['target_column'], config['forecast_horizon'])
```

#### 📊 Composants
- **Modèles disponibles** : Prophet, NeuralProphet, Random Forest, Gradient Boosting
- **Configuration** : Horizon, variable cible, paramètres
- **Séries temporelles** : Graphiques interactifs
- **Prévisions futures** : Projections avec intervalles de confiance
- **Décomposition** : Tendance, saisonnalité, résidus
- **Métriques** : RMSE, MAE, R², MAPE

## 🎨 Composants Visuels

### Graphiques de Base

#### 📊 basic_plots.py
```python
def plot_daily_production(df: pd.DataFrame, date_col: str = 'Date', 
                         production_col: str = "Production journaliere d'huile bbl"):
    """Graphique de production quotidienne."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df[date_col], df[production_col], linewidth=2, color='#1f77b4')
    ax.set_title('Production Quotidienne d\'Huile', fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Production (bbl)', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Formatage des dates
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig
```

#### 🔧 Fonctionnalités
- **Séries temporelles** : Production, watercut, ratios
- **Histogrammes** : Distribution des variables
- **Scatter plots** : Corrélations entre variables
- **Box plots** : Analyse des outliers
- **Heatmaps** : Matrices de corrélation

### Graphiques ML

#### 🤖 model_plots.py
```python
def plot_confusion_matrix(y_true, y_pred, class_names=None, figsize=(8, 6)):
    """Matrice de confusion pour classification."""
    cm = confusion_matrix(y_true, y_pred)
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names, ax=ax)
    
    ax.set_title('Matrice de Confusion', fontsize=16, fontweight='bold')
    ax.set_xlabel('Prédictions', fontsize=12)
    ax.set_ylabel('Valeurs Réelles', fontsize=12)
    
    return fig

def plot_roc_curve(y_true, y_prob, figsize=(8, 6)):
    """Courbe ROC pour évaluation binaire."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc_score = auc(fpr, tpr)
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {auc_score:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    
    ax.set_title('Courbe ROC', fontsize=16, fontweight='bold')
    ax.set_xlabel('Taux de Faux Positifs', fontsize=12)
    ax.set_ylabel('Taux de Vrais Positifs', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig
```

### Graphiques Tableau de Bord

#### 📈 dashboard_plots.py
```python
def create_kpi_cards(kpis: dict):
    """Crée des cartes KPI interactives."""
    cols = st.columns(len(kpis))
    
    for i, (kpi_name, kpi_data) in enumerate(kpis.items()):
        with cols[i]:
            # Calcul de la variation
            current_value = kpi_data['current']
            previous_value = kpi_data.get('previous', current_value)
            change = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
            
            # Couleur selon la variation
            color = "green" if change >= 0 else "red"
            arrow = "↗️" if change >= 0 else "↘️"
            
            # Affichage de la carte
            st.metric(
                label=kpi_name,
                value=f"{current_value:,.0f} {kpi_data.get('unit', '')}",
                delta=f"{change:+.1f}% {arrow}"
            )

def plot_production_trend(df: pd.DataFrame, period: str = '30D'):
    """Graphique de tendance de production."""
    # Agrégation par période
    df_agg = df.set_index('Date').resample(period).agg({
        "Production journaliere d'huile bbl": 'sum',
        "Production journaliere d'eau bbl": 'sum',
        'Teneur en eau (Watercut)': 'mean'
    })
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Production
    ax1.plot(df_agg.index, df_agg["Production journaliere d'huile bbl"], 
             label='Huile', linewidth=2, color='green')
    ax1.plot(df_agg.index, df_agg["Production journaliere d'eau bbl"], 
             label='Eau', linewidth=2, color='blue')
    ax1.set_title('Tendance de Production', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Production (bbl)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Watercut
    ax2.plot(df_agg.index, df_agg['Teneur en eau (Watercut)'], 
             linewidth=2, color='red')
    ax2.set_title('Évolution du Watercut', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Watercut (%)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
```

## 🎛️ Contrôles Interactifs

### Sidebar Navigation

#### 🧭 SidebarUI
```python
class SidebarUI:
    @staticmethod
    def render(production_df: pd.DataFrame, failures_df: pd.DataFrame) -> str:
        """Barre latérale avec navigation et contrôles."""
        st.sidebar.title("🛢️ Navigation")
        
        # Menu principal
        pages = {
            "🏠 Accueil": "home",
            "📊 Tableau de Bord": "dashboard", 
            "🔧 Maintenance Prédictive": "maintenance",
            "📈 Prévision de Production": "forecast",
            "💧 Optimisation Injection": "water_optimization",
            "🔍 Comparaison de Modèles": "model_comparison"
        }
        
        selected_page = st.sidebar.selectbox(
            "Sélectionnez une page",
            list(pages.keys()),
            index=0
        )
        
        # Informations sur les données
        SidebarUI._render_data_info(production_df, failures_df)
        
        # Actions rapides
        SidebarUI._render_quick_actions()
        
        return selected_page
    
    @staticmethod
    def _render_data_info(production_df: pd.DataFrame, failures_df: pd.DataFrame):
        """Affiche les informations sur les données."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Informations Données")
        
        # Statistiques production
        if not production_df.empty:
            st.sidebar.metric(
                "Lignes Production", 
                f"{len(production_df):,}"
            )
            st.sidebar.metric(
                "Période", 
                f"{production_df['Date'].min().strftime('%Y-%m-%d')} - {production_df['Date'].max().strftime('%Y-%m-%d')}"
            )
        
        # Statistiques pannes
        if not failures_df.empty:
            st.sidebar.metric(
                "Pannes Enregistrées", 
                f"{len(failures_df):,}"
            )
```

### Filtres et Contrôles

#### 🎚️ Composants Interactifs
```python
def render_date_filter(df: pd.DataFrame, key: str = "date_filter"):
    """Filtre de dates interactif."""
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Date de début",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key}_start"
        )
    
    with col2:
        end_date = st.date_input(
            "Date de fin",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key}_end"
        )
    
    return start_date, end_date

def render_algorithm_selector(available_algorithms: list, key: str = "algo_select"):
    """Sélecteur d'algorithmes multiple."""
    selected = st.multiselect(
        "Sélectionnez les algorithmes à comparer",
        available_algorithms,
        default=available_algorithms[:2] if len(available_algorithms) >= 2 else available_algorithms,
        key=key
    )
    
    if not selected:
        st.warning("⚠️ Veuillez sélectionner au moins un algorithme.")
    
    return selected

def render_parameter_sliders(algorithm: str):
    """Sliders pour paramètres d'algorithmes."""
    params = {}
    
    if algorithm in ['random_forest', 'gradient_boosting']:
        params['n_estimators'] = st.slider(
            "Nombre d'estimateurs",
            min_value=50, max_value=500, value=100, step=50
        )
        params['max_depth'] = st.slider(
            "Profondeur maximale",
            min_value=3, max_value=20, value=10, step=1
        )
    
    if algorithm == 'gradient_boosting':
        params['learning_rate'] = st.slider(
            "Taux d'apprentissage",
            min_value=0.01, max_value=0.3, value=0.1, step=0.01
        )
    
    return params
```

## 📱 Design Responsive

### Layout Adaptatif

#### 📐 Colonnes Dynamiques
```python
def create_responsive_layout(content_items: list, max_cols: int = 3):
    """Crée un layout responsive selon le nombre d'éléments."""
    n_items = len(content_items)
    
    if n_items == 1:
        cols = st.columns(1)
    elif n_items == 2:
        cols = st.columns(2)
    elif n_items <= max_cols:
        cols = st.columns(n_items)
    else:
        # Répartition sur plusieurs lignes
        cols_per_row = max_cols
        rows = (n_items + cols_per_row - 1) // cols_per_row
        
        for row in range(rows):
            start_idx = row * cols_per_row
            end_idx = min(start_idx + cols_per_row, n_items)
            row_items = content_items[start_idx:end_idx]
            
            cols = st.columns(len(row_items))
            for i, item in enumerate(row_items):
                with cols[i]:
                    item()
        return
    
    # Affichage normal
    for i, item in enumerate(content_items):
        with cols[i]:
            item()
```

#### 📱 Mobile-First
```python
# Configuration responsive
st.set_page_config(
    page_title="Tchad Petroleum - Analyse Prédictive",
    page_icon="🛢️",
    layout="wide",  # Utilise toute la largeur
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour mobile
st.markdown("""
<style>
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .metric-container {
            margin-bottom: 1rem;
        }
    }
    
    /* Amélioration des graphiques */
    .stPlotlyChart {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)
```

## 🎨 Thème et Styling

### Palette de Couleurs

```python
# Couleurs principales
COLOR_PALETTE = {
    'primary': '#1f77b4',      # Bleu principal
    'secondary': '#ff7f0e',    # Orange secondaire
    'success': '#2ca02c',      # Vert succès
    'warning': '#d62728',      # Rouge alerte
    'info': '#17becf',         # Cyan info
    'light': '#f8f9fa',        # Gris clair
    'dark': '#343a40'          # Gris foncé
}

# Application des couleurs
def apply_color_theme():
    """Applique le thème de couleurs personnalisé."""
    st.markdown("""
    <style>
        /* Variables CSS */
        :root {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --success-color: #2ca02c;
            --warning-color: #d62728;
        }
        
        /* Boutons personnalisés */
        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #1565c0;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Métriques personnalisées */
        .metric-container {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-color);
        }
    </style>
    """, unsafe_allow_html=True)
```

### Composants Stylisés

```python
def styled_metric_card(title: str, value: str, delta: str = None, color: str = "primary"):
    """Carte de métrique stylisée."""
    delta_html = f"<div class='metric-delta {color}'>{delta}</div>" if delta else ""
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def success_message(message: str):
    """Message de succès stylisé."""
    st.markdown(f"""
    <div class="alert alert-success">
        <i class="fas fa-check-circle"></i>
        {message}
    </div>
    """, unsafe_allow_html=True)

def warning_message(message: str):
    """Message d'avertissement stylisé."""
    st.markdown(f"""
    <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i>
        {message}
    </div>
    """, unsafe_allow_html=True)
```

## 📊 Téléchargement et Export

### Utilitaires de Téléchargement

#### 💾 download_utils.py
```python
def display_plot_with_download(fig, title: str = "graphique", format: str = "png"):
    """Affiche un graphique avec option de téléchargement."""
    # Affichage du graphique
    st.pyplot(fig)
    
    # Bouton de téléchargement
    buffer = BytesIO()
    fig.savefig(buffer, format=format, dpi=300, bbox_inches='tight')
    buffer.seek(0)
    
    st.download_button(
        label=f"📥 Télécharger {title}.{format}",
        data=buffer.getvalue(),
        file_name=f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
        mime=f"image/{format}"
    )

def create_download_section(data: pd.DataFrame, filename: str = "data"):
    """Section de téléchargement pour données."""
    st.markdown("### 📥 Téléchargement des Données")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV
        csv_buffer = StringIO()
        data.to_csv(csv_buffer, index=False)
        st.download_button(
            "📄 CSV",
            csv_buffer.getvalue(),
            f"{filename}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    
    with col2:
        # Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name='Data')
        
        st.download_button(
            "📊 Excel",
            excel_buffer.getvalue(),
            f"{filename}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col3:
        # JSON
        json_str = data.to_json(orient='records', indent=2)
        st.download_button(
            "🔗 JSON",
            json_str,
            f"{filename}_{datetime.now().strftime('%Y%m%d')}.json",
            "application/json"
        )
```

## ⚡ Performance et Optimisation

### Cache Streamlit

```python
# Cache pour données
@st.cache_data(ttl=3600)  # Cache 1 heure
def load_cached_data():
    """Charge les données avec cache."""
    return load_production_data(), load_pump_failures_data()

# Cache pour modèles
@st.cache_resource
def load_trained_model(model_type: str, algorithm: str):
    """Charge un modèle entraîné avec cache."""
    model = ModelFactory.create_model(model_type, algorithm)
    # Chargement des paramètres sauvegardés si disponibles
    return model

# Cache pour graphiques
@st.cache_data
def generate_cached_plot(data_hash: str, plot_type: str, **kwargs):
    """Génère un graphique avec cache basé sur hash des données."""
    # Génération du graphique
    return create_plot(plot_type, **kwargs)
```

### Optimisations UI

```python
# Lazy loading pour gros datasets
def render_paginated_table(df: pd.DataFrame, page_size: int = 100):
    """Table paginée pour gros volumes."""
    total_rows = len(df)
    total_pages = (total_rows + page_size - 1) // page_size
    
    # Contrôles de pagination
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.selectbox(
            "Page",
            range(1, total_pages + 1),
            format_func=lambda x: f"Page {x} sur {total_pages}"
        )
    
    # Affichage de la page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    st.dataframe(
        df.iloc[start_idx:end_idx],
        use_container_width=True
    )
    
    # Informations
    st.caption(f"Affichage des lignes {start_idx + 1} à {end_idx} sur {total_rows}")

# Progress bars pour opérations longues
def show_progress_operation(operation_func, steps: list):
    """Affiche une barre de progression pour opération longue."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, step in enumerate(steps):
        status_text.text(f"Étape {i+1}/{len(steps)}: {step}")
        
        # Exécution de l'étape
        operation_func(step)
        
        # Mise à jour de la progression
        progress_bar.progress((i + 1) / len(steps))
    
    status_text.text("✅ Opération terminée !")
    time.sleep(1)
    progress_bar.empty()
    status_text.empty()
```

## 🧪 Tests Interface

### Tests Unitaires UI

```python
import pytest
from unittest.mock import patch, MagicMock

def test_sidebar_rendering():
    """Test du rendu de la sidebar."""
    with patch('streamlit.sidebar') as mock_sidebar:
        # Mock des données
        mock_df = pd.DataFrame({'Date': ['2023-01-01'], 'Production': [1000]})
        
        # Test du rendu
        result = SidebarUI.render(mock_df, mock_df)
        
        # Vérifications
        assert mock_sidebar.title.called
        assert mock_sidebar.selectbox.called
        assert isinstance(result, str)

def test_kpi_calculation():
    """Test du calcul des KPIs."""
    # Données de test
    test_data = pd.DataFrame({
        'Date': pd.date_range('2023-01-01', periods=10),
        'Production': range(1000, 1100, 10)
    })
    
    # Calcul des KPIs
    kpis = calculate_production_kpis(test_data)
    
    # Vérifications
    assert 'production_totale' in kpis
    assert 'production_moyenne' in kpis
    assert kpis['production_totale'] > 0
```

### Tests d'Intégration

```python
def test_full_ui_workflow():
    """Test du workflow complet de l'interface."""
    # Simulation d'une session utilisateur
    with patch('streamlit.session_state') as mock_session:
        # 1. Chargement des données
        production_df, failures_df = load_all_data()
        assert not production_df.empty
        
        # 2. Navigation vers maintenance
        selected_page = "🔧 Maintenance Prédictive"
        
        # 3. Sélection d'algorithmes
        algorithms = ['random_forest', 'gradient_boosting']
        
        # 4. Configuration
        config = {'horizon': 30, 'test_size': 0.2}
        
        # 5. Vérification que tout fonctionne
        assert len(algorithms) > 0
        assert config['horizon'] > 0
```

## 📚 Bonnes Pratiques UI

### ✅ Recommandations

1. **Feedback utilisateur** : Messages clairs et informatifs
2. **Performance** : Cache et lazy loading
3. **Accessibilité** : Contraste et navigation clavier
4. **Responsive** : Adaptation mobile et desktop
5. **Cohérence** : Design system uniforme

### ❌ À Éviter

1. Surcharge d'informations sur une page
2. Temps de chargement > 3 secondes
3. Boutons sans feedback visuel
4. Graphiques non interactifs
5. Navigation confuse

## 🔍 Dépannage Interface

### Problèmes Courants

#### 🚨 "Page ne se charge pas"
- **Cause** : Erreur dans les données ou cache corrompu
- **Solution** : Vider le cache Streamlit, vérifier les données

#### 🚨 "Graphiques ne s'affichent pas"
- **Cause** : Problème matplotlib ou données vides
- **Solution** : Vérifier les dépendances, valider les données

#### 🚨 "Interface lente"
- **Cause** : Pas de cache ou opérations lourdes
- **Solution** : Implémenter le cache, optimiser les requêtes

## 📞 Support Interface

Pour assistance sur l'interface utilisateur :
- **Documentation** : Ce guide complet
- **Code source** : `src/ui_components/`
- **Exemples** : `src/plotting/`
- **Support** : Équipe UI/UX

---

*Guide complet de l'interface utilisateur et visualisations. Version 2.0*