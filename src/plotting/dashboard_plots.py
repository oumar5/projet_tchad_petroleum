import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from typing import Dict, Any, Optional

# Configuration du style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def plot_kpi_dashboard(production_kpis: Dict[str, Any], failure_kpis: Dict[str, Any]):
    """
    Crée un dashboard complet des KPIs.
    
    Args:
        production_kpis: KPIs de production
        failure_kpis: KPIs de maintenance
        
    Returns:
        Figure matplotlib
    """
    fig = plt.figure(figsize=(16, 12))
    
    # Créer une grille de sous-graphiques
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Titre principal
    fig.suptitle('Dashboard des Indicateurs de Performance', fontsize=20, fontweight='bold')
    
    # 1. Production totale (gauge)
    ax1 = fig.add_subplot(gs[0, 0])
    if 'oil_production' in production_kpis:
        oil_kpis = production_kpis['oil_production']
        _plot_gauge(ax1, oil_kpis['total'], 'Production Totale\n(barils)', 
                   max_val=oil_kpis['total'] * 1.2, unit='bbl')
    
    # 2. Production moyenne journalière
    ax2 = fig.add_subplot(gs[0, 1])
    if 'oil_production' in production_kpis:
        _plot_gauge(ax2, oil_kpis['average_daily'], 'Production Moyenne\n(barils/jour)', 
                   max_val=oil_kpis['max_daily'] * 1.1, unit='bbl/j')
    
    # 3. Watercut actuel
    ax3 = fig.add_subplot(gs[0, 2])
    if 'watercut' in production_kpis:
        wc_kpis = production_kpis['watercut']
        _plot_gauge(ax3, wc_kpis['current'], 'Watercut Actuel', 
                   max_val=100, unit='%', critical_threshold=80)
    
    # 4. Graphique en barres des KPIs de production
    ax4 = fig.add_subplot(gs[1, :])
    _plot_production_kpis_bars(ax4, production_kpis)
    
    # 5. MTBF et pannes
    ax5 = fig.add_subplot(gs[2, 0])
    if failure_kpis and 'mtbf_days' in failure_kpis:
        _plot_gauge(ax5, failure_kpis['mtbf_days'], 'MTBF\n(jours)', 
                   max_val=365, unit='jours', critical_threshold=30, reverse_critical=True)
    
    # 6. Répartition des pannes par bloc
    ax6 = fig.add_subplot(gs[2, 1:])
    if failure_kpis and 'failures_by_block' in failure_kpis:
        _plot_failures_pie(ax6, failure_kpis['failures_by_block'])
    
    return fig

def _plot_gauge(ax, value: float, title: str, max_val: float, unit: str = '', 
               critical_threshold: Optional[float] = None, reverse_critical: bool = False):
    """
    Crée un graphique en forme de jauge.
    
    Args:
        ax: Axes matplotlib
        value: Valeur à afficher
        title: Titre de la jauge
        max_val: Valeur maximale
        unit: Unité de mesure
        critical_threshold: Seuil critique
        reverse_critical: Si True, les valeurs faibles sont critiques
    """
    # Normaliser la valeur
    normalized_value = min(value / max_val, 1.0)
    
    # Déterminer la couleur selon le seuil critique
    if critical_threshold is not None:
        normalized_threshold = critical_threshold / max_val
        if reverse_critical:
            color = 'red' if normalized_value < normalized_threshold else 'green'
        else:
            color = 'red' if normalized_value > normalized_threshold else 'green'
    else:
        color = 'blue'
    
    # Créer la jauge (demi-cercle)
    theta = np.linspace(0, np.pi, 100)
    r_outer = 1
    r_inner = 0.7
    
    # Fond de la jauge
    ax.fill_between(theta, r_inner, r_outer, color='lightgray', alpha=0.3)
    
    # Partie remplie
    theta_filled = np.linspace(0, np.pi * normalized_value, 100)
    ax.fill_between(theta_filled, r_inner, r_outer, color=color, alpha=0.7)
    
    # Aiguille
    needle_angle = np.pi * (1 - normalized_value)
    needle_x = [0, 0.9 * np.cos(needle_angle)]
    needle_y = [0, 0.9 * np.sin(needle_angle)]
    ax.plot(needle_x, needle_y, color='black', linewidth=3)
    ax.scatter([0], [0], color='black', s=50, zorder=5)
    
    # Texte
    ax.text(0, -0.3, f'{value:.1f} {unit}', ha='center', va='center', 
           fontsize=12, fontweight='bold')
    ax.text(0, -0.5, title, ha='center', va='center', fontsize=10)
    
    # Configuration des axes
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.6, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')

def _plot_production_kpis_bars(ax, production_kpis: Dict[str, Any]):
    """
    Crée un graphique en barres des KPIs de production.
    
    Args:
        ax: Axes matplotlib
        production_kpis: KPIs de production
    """
    if not production_kpis:
        ax.text(0.5, 0.5, 'Aucune donnée de production disponible', 
               ha='center', va='center', transform=ax.transAxes)
        return
    
    kpis_data = []
    
    if 'oil_production' in production_kpis:
        oil_kpis = production_kpis['oil_production']
        kpis_data.extend([
            ('Production Totale', oil_kpis['total'], 'bbl'),
            ('Prod. Moyenne/jour', oil_kpis['average_daily'], 'bbl/j'),
            ('Prod. Max/jour', oil_kpis['max_daily'], 'bbl/j')
        ])
    
    if 'watercut' in production_kpis:
        wc_kpis = production_kpis['watercut']
        kpis_data.extend([
            ('Watercut Actuel', wc_kpis['current'], '%'),
            ('Watercut Moyen', wc_kpis['average'], '%')
        ])
    
    if not kpis_data:
        ax.text(0.5, 0.5, 'Aucune donnée KPI disponible', 
               ha='center', va='center', transform=ax.transAxes)
        return
    
    # Séparer les données
    labels, values, units = zip(*kpis_data)
    
    # Normaliser les valeurs pour l'affichage (différentes échelles)
    normalized_values = []
    colors = []
    
    for i, (label, value, unit) in enumerate(kpis_data):
        if 'Watercut' in label:
            normalized_values.append(value)  # Déjà en %
            colors.append('red' if value > 80 else 'orange' if value > 60 else 'green')
        else:
            normalized_values.append(value / 1000)  # Diviser par 1000 pour l'affichage
            colors.append('blue')
    
    # Créer le graphique en barres
    bars = ax.bar(range(len(labels)), normalized_values, color=colors, alpha=0.7)
    
    # Ajouter les valeurs sur les barres
    for i, (bar, value, unit) in enumerate(zip(bars, values, units)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(normalized_values) * 0.01,
               f'{value:.1f} {unit}', ha='center', va='bottom', fontweight='bold')
    
    ax.set_title('Indicateurs de Performance de Production', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel('Valeur Normalisée')
    ax.grid(True, alpha=0.3, axis='y')

def _plot_failures_pie(ax, failures_by_block: Dict[str, int]):
    """
    Crée un graphique en secteurs des pannes par bloc.
    
    Args:
        ax: Axes matplotlib
        failures_by_block: Dictionnaire des pannes par bloc
    """
    if not failures_by_block:
        ax.text(0.5, 0.5, 'Aucune donnée de panne disponible', 
               ha='center', va='center', transform=ax.transAxes)
        return
    
    blocks = list(failures_by_block.keys())
    counts = list(failures_by_block.values())
    
    # Couleurs pour chaque bloc
    colors = plt.cm.Set3(np.linspace(0, 1, len(blocks)))
    
    # Créer le graphique en secteurs
    wedges, texts, autotexts = ax.pie(counts, labels=blocks, colors=colors, 
                                     autopct='%1.1f%%', startangle=90)
    
    # Améliorer l'apparence du texte
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Répartition des Pannes par Bloc', fontsize=14, fontweight='bold')

def plot_trend_analysis(df: pd.DataFrame, columns: list, 
                       title: str = "Analyse des Tendances"):
    """
    Crée un graphique d'analyse des tendances pour plusieurs colonnes.
    
    Args:
        df: DataFrame contenant les données
        columns: Liste des colonnes à analyser
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, axes = plt.subplots(len(columns), 1, figsize=(15, 4 * len(columns)))
    if len(columns) == 1:
        axes = [axes]
    
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    
    for i, column in enumerate(columns):
        ax = axes[i]
        color = colors[i % len(colors)]
        
        # Tracer la série temporelle
        ax.plot(df['Date'], df[column], color=color, linewidth=2, alpha=0.7)
        
        # Ajouter une ligne de tendance
        try:
            from scipy import stats
            x_numeric = np.arange(len(df))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, df[column].dropna())
            trend_line = slope * x_numeric + intercept
            ax.plot(df['Date'], trend_line, color='red', linestyle='--', linewidth=2, 
                   label=f'Tendance (R²={r_value**2:.3f})')
        except:
            pass
        
        ax.set_title(f'{column}', fontsize=12, fontweight='bold')
        ax.set_ylabel('Valeur')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Rotation des dates
        ax.tick_params(axis='x', rotation=45)
    
    axes[-1].set_xlabel('Date')
    plt.tight_layout()
    
    return fig

def plot_correlation_heatmap(df: pd.DataFrame, columns: list = None,
                           title: str = "Matrice de Corrélation"):
    """
    Crée une heatmap de corrélation.
    
    Args:
        df: DataFrame contenant les données
        columns: Liste des colonnes à inclure (toutes si None)
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    if columns is None:
        # Sélectionner uniquement les colonnes numériques
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'Date' in numeric_columns:
            numeric_columns.remove('Date')
        columns = numeric_columns
    
    # Calculer la matrice de corrélation
    corr_matrix = df[columns].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Créer la heatmap
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, ax=ax, cbar_kws={'shrink': 0.8})
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    return fig