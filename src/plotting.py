import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Configuration du style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def plot_daily_production(df: pd.DataFrame):
    """Génère le graphique de la production journalière d'huile."""
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(df['Date'], df["Production journaliere d'huile bbl"], marker='o', linestyle='-', markersize=2)
    ax.set_title("Production Journalière d'Huile")
    ax.set_xlabel('Année')
    ax.set_ylabel("Production d'Huile (bbl)")
    ax.grid(True)
    return fig

def plot_failures_by_block(df: pd.DataFrame):
    """Génère un bar chart du nombre de pannes par bloc."""
    failures_count = df['Bloc Faillé'].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    failures_count.sort_values(ascending=True).plot(kind='barh', ax=ax)
    ax.set_title('Nombre Total de Pannes par Bloc')
    ax.set_xlabel('Nombre de Pannes')
    ax.set_ylabel('Bloc')
    return fig

# ============= VISUALISATIONS AVANCÉES POUR MODÈLES PRÉDICTIFS =============

def plot_model_performance_metrics(metrics_dict, model_name="Modèle"):
    """Visualise les métriques de performance d'un modèle."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Métriques de Performance - {model_name}', fontsize=16)
    
    # Métriques de classification
    if 'accuracy' in metrics_dict:
        classification_metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        values = [metrics_dict.get(metric, 0) for metric in classification_metrics]
        
        axes[0, 0].bar(classification_metrics, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        axes[0, 0].set_title('Métriques de Classification')
        axes[0, 0].set_ylabel('Score')
        axes[0, 0].set_ylim(0, 1)
        
        # Ajouter les valeurs sur les barres
        for i, v in enumerate(values):
            axes[0, 0].text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom')
    
    # Métriques de régression
    if 'mse' in metrics_dict:
        regression_metrics = ['MSE', 'RMSE', 'MAE', 'R²']
        values = [metrics_dict.get('mse', 0), metrics_dict.get('rmse', 0), 
                 metrics_dict.get('mae', 0), metrics_dict.get('r2', 0)]
        
        axes[0, 1].bar(regression_metrics, values, color=['#9467bd', '#8c564b', '#e377c2', '#7f7f7f'])
        axes[0, 1].set_title('Métriques de Régression')
        axes[0, 1].set_ylabel('Valeur')
        
        # Ajouter les valeurs sur les barres
        for i, v in enumerate(values):
            axes[0, 1].text(i, v + max(values)*0.01, f'{v:.3f}', ha='center', va='bottom')
    
    # Graphique en radar pour les métriques normalisées
    if 'accuracy' in metrics_dict:
        categories = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        values = [metrics_dict.get('accuracy', 0), metrics_dict.get('precision', 0),
                 metrics_dict.get('recall', 0), metrics_dict.get('f1_score', 0)]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # Fermer le polygone
        angles += angles[:1]
        
        axes[1, 0].plot(angles, values, 'o-', linewidth=2, color='#1f77b4')
        axes[1, 0].fill(angles, values, alpha=0.25, color='#1f77b4')
        axes[1, 0].set_xticks(angles[:-1])
        axes[1, 0].set_xticklabels(categories)
        axes[1, 0].set_ylim(0, 1)
        axes[1, 0].set_title('Radar des Métriques')
        axes[1, 0].grid(True)
    
    # Graphique de comparaison (placeholder)
    axes[1, 1].text(0.5, 0.5, 'Comparaison avec\nautres modèles\n(à implémenter)', 
                    ha='center', va='center', transform=axes[1, 1].transAxes,
                    fontsize=12, bbox=dict(boxstyle='round', facecolor='lightgray'))
    axes[1, 1].set_title('Comparaison Modèles')
    
    plt.tight_layout()
    return fig

def plot_confusion_matrix(y_true, y_pred, class_names=None):
    """Visualise la matrice de confusion."""
    cm = confusion_matrix(y_true, y_pred)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=class_names or ['Non-Panne', 'Panne'],
                yticklabels=class_names or ['Non-Panne', 'Panne'])
    
    ax.set_title('Matrice de Confusion')
    ax.set_xlabel('Prédictions')
    ax.set_ylabel('Valeurs Réelles')
    
    return fig

def plot_roc_curve(y_true, y_prob):
    """Visualise la courbe ROC."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color='darkorange', lw=2, 
            label=f'Courbe ROC (AUC = {roc_auc:.2f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Aléatoire')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('Taux de Faux Positifs')
    ax.set_ylabel('Taux de Vrais Positifs')
    ax.set_title('Courbe ROC')
    ax.legend(loc="lower right")
    ax.grid(True)
    
    return fig

def plot_feature_importance(feature_importance_df, top_n=10):
    """Visualise l'importance des features."""
    top_features = feature_importance_df.head(top_n)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_features, x='importance', y='feature', ax=ax, palette='viridis')
    
    ax.set_title(f'Top {top_n} Features les Plus Importantes')
    ax.set_xlabel('Importance')
    ax.set_ylabel('Features')
    
    # Ajouter les valeurs sur les barres
    for i, v in enumerate(top_features['importance']):
        ax.text(v + 0.001, i, f'{v:.3f}', va='center')
    
    plt.tight_layout()
    return fig

def plot_prediction_vs_actual(y_true, y_pred, title="Prédictions vs Valeurs Réelles"):
    """Visualise les prédictions vs valeurs réelles pour la régression."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Scatter plot
    axes[0].scatter(y_true, y_pred, alpha=0.6, color='blue')
    axes[0].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 
                'r--', lw=2, label='Ligne parfaite')
    axes[0].set_xlabel('Valeurs Réelles')
    axes[0].set_ylabel('Prédictions')
    axes[0].set_title('Prédictions vs Réalité')
    axes[0].legend()
    axes[0].grid(True)
    
    # Résidus
    residuals = y_pred - y_true
    axes[1].scatter(y_pred, residuals, alpha=0.6, color='green')
    axes[1].axhline(y=0, color='r', linestyle='--')
    axes[1].set_xlabel('Prédictions')
    axes[1].set_ylabel('Résidus')
    axes[1].set_title('Graphique des Résidus')
    axes[1].grid(True)
    
    plt.suptitle(title, fontsize=16)
    plt.tight_layout()
    return fig

def plot_time_series_forecast(dates, actual, predicted, title="Prévision de Production"):
    """Visualise les prévisions de série temporelle."""
    fig, ax = plt.subplots(figsize=(15, 8))
    
    ax.plot(dates, actual, label='Valeurs Réelles', color='blue', linewidth=2)
    ax.plot(dates, predicted, label='Prédictions', color='red', linewidth=2, linestyle='--')
    
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Date')
    ax.set_ylabel('Production (bbl)')
    ax.legend()
    ax.grid(True)
    
    # Rotation des dates pour une meilleure lisibilité
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_failure_probability_timeline(dates, probabilities, threshold=0.5):
    """Visualise l'évolution de la probabilité de panne dans le temps."""
    fig, ax = plt.subplots(figsize=(15, 6))
    
    ax.plot(dates, probabilities, color='orange', linewidth=2, label='Probabilité de Panne')
    ax.axhline(y=threshold, color='red', linestyle='--', linewidth=2, 
              label=f'Seuil d\'Alerte ({threshold})')
    
    # Colorer les zones à risque
    ax.fill_between(dates, probabilities, threshold, 
                   where=(probabilities >= threshold), 
                   color='red', alpha=0.3, label='Zone à Risque')
    
    ax.set_title('Évolution de la Probabilité de Panne', fontsize=16)
    ax.set_xlabel('Date')
    ax.set_ylabel('Probabilité')
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(True)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_production_components(df):
    """Visualise les différentes composantes de la production."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Production d'huile
    axes[0, 0].plot(df['Date'], df["Production journaliere d'huile bbl"], 
                   color='green', linewidth=2)
    axes[0, 0].set_title('Production d\'Huile')
    axes[0, 0].set_ylabel('Barils/jour')
    axes[0, 0].grid(True)
    
    # Production d'eau
    axes[0, 1].plot(df['Date'], df["Production journaliere d'eau bbl"], 
                   color='blue', linewidth=2)
    axes[0, 1].set_title('Production d\'Eau')
    axes[0, 1].set_ylabel('Barils/jour')
    axes[0, 1].grid(True)
    
    # Watercut
    axes[1, 0].plot(df['Date'], df["Teneur en eau (Watercut)"], 
                   color='red', linewidth=2)
    axes[1, 0].set_title('Teneur en Eau (Watercut)')
    axes[1, 0].set_ylabel('%')
    axes[1, 0].grid(True)
    
    # Puits actifs
    axes[1, 1].plot(df['Date'], df["Nombre des puits actifs"], 
                   color='purple', linewidth=2, marker='o', markersize=3)
    axes[1, 1].set_title('Nombre de Puits Actifs')
    axes[1, 1].set_ylabel('Nombre')
    axes[1, 1].grid(True)
    
    # Rotation des dates
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def plot_kpi_dashboard(production_kpis, failure_kpis):
    """Crée un dashboard des KPIs principaux."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Dashboard des KPIs', fontsize=20)
    
    # KPI Production d'huile
    if 'oil_production' in production_kpis:
        oil_kpis = production_kpis['oil_production']
        metrics = ['Total', 'Moyenne/jour', 'Max/jour', 'Min/jour']
        values = [oil_kpis['total'], oil_kpis['average_daily'], 
                 oil_kpis['max_daily'], oil_kpis['min_daily']]
        
        axes[0, 0].bar(metrics, values, color='green', alpha=0.7)
        axes[0, 0].set_title('Production d\'Huile (bbl)')
        axes[0, 0].tick_params(axis='x', rotation=45)
    
    # KPI Watercut
    if 'watercut' in production_kpis:
        wc_kpis = production_kpis['watercut']
        axes[0, 1].pie([wc_kpis['current'], 100-wc_kpis['current']], 
                      labels=['Eau', 'Huile'], autopct='%1.1f%%',
                      colors=['lightblue', 'darkgreen'])
        axes[0, 1].set_title(f'Watercut Actuel: {wc_kpis["current"]:.1f}%')
    
    # Puits actifs
    if 'active_wells' in production_kpis:
        well_kpis = production_kpis['active_wells']
        axes[0, 2].text(0.5, 0.5, f"{int(well_kpis['current'])}\nPuits Actifs", 
                       ha='center', va='center', transform=axes[0, 2].transAxes,
                       fontsize=24, weight='bold')
        axes[0, 2].set_title('État Actuel des Puits')
    
    # Pannes par bloc
    if 'failures_by_block' in failure_kpis and failure_kpis['failures_by_block']:
        blocks = list(failure_kpis['failures_by_block'].keys())
        failures = list(failure_kpis['failures_by_block'].values())
        
        axes[1, 0].bar(blocks, failures, color='red', alpha=0.7)
        axes[1, 0].set_title('Pannes par Bloc')
        axes[1, 0].set_ylabel('Nombre de Pannes')
    
    # MTBF
    if 'mtbf_days' in failure_kpis:
        axes[1, 1].text(0.5, 0.5, f"{failure_kpis['mtbf_days']:.0f}\nJours\n(MTBF)", 
                       ha='center', va='center', transform=axes[1, 1].transAxes,
                       fontsize=20, weight='bold', color='orange')
        axes[1, 1].set_title('Temps Moyen Entre Pannes')
    
    # Total des pannes
    if 'total_failures' in failure_kpis:
        axes[1, 2].text(0.5, 0.5, f"{failure_kpis['total_failures']}\nPannes\nTotales", 
                       ha='center', va='center', transform=axes[1, 2].transAxes,
                       fontsize=20, weight='bold', color='darkred')
        axes[1, 2].set_title('Historique des Pannes')
    
    # Supprimer les axes vides
    for ax in axes.flat:
        if not ax.has_data():
            ax.axis('off')
    
    plt.tight_layout()
    return fig