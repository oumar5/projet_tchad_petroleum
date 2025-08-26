import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from typing import Optional

# Configuration du style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def plot_time_series_forecast(dates, y_true, y_pred, 
                             title: str = "Prévision de Série Temporelle"):
    """
    Crée un graphique de prévision de série temporelle.
    
    Args:
        dates: Dates correspondantes
        y_true: Valeurs réelles
        y_pred: Prédictions
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Tracer les valeurs réelles et prédites
    ax.plot(dates, y_true, label='Valeurs Réelles', color='blue', linewidth=2, marker='o', markersize=4)
    ax.plot(dates, y_pred, label='Prédictions', color='red', linewidth=2, marker='s', markersize=4, linestyle='--')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Valeur', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Rotation des dates
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_failure_probability_timeline(dates, probabilities, 
                                     title: str = "Probabilités de Panne dans le Temps"):
    """
    Crée un graphique des probabilités de panne dans le temps.
    
    Args:
        dates: Dates correspondantes
        probabilities: Probabilités de panne
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Tracer les probabilités
    ax.plot(dates, probabilities, color='red', linewidth=3, marker='o', markersize=6)
    
    # Zones de couleur pour les seuils
    ax.axhline(y=0.7, color='red', linestyle='--', alpha=0.7, label='Seuil critique (70%)')
    ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='Seuil d\'attention (50%)')
    
    # Remplir les zones selon les seuils
    ax.fill_between(dates, probabilities, 0.7, 
                   where=(probabilities >= 0.7), color='red', alpha=0.3, label='Zone critique')
    ax.fill_between(dates, probabilities, 0.5, 
                   where=((probabilities >= 0.5) & (probabilities < 0.7)), 
                   color='orange', alpha=0.3, label='Zone d\'attention')
    ax.fill_between(dates, probabilities, 0, 
                   where=(probabilities < 0.5), color='green', alpha=0.3, label='Zone normale')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Probabilité de Panne', fontsize=12)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Format des probabilités en pourcentage sur l'axe y
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_production_components(df: pd.DataFrame, 
                             title: str = "Composantes de la Production"):
    """
    Crée un graphique multi-panneaux des composantes de production.
    
    Args:
        df: DataFrame contenant les données de production
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    fig.suptitle(title, fontsize=18, fontweight='bold')
    
    # Production d'huile
    axes[0].plot(df['Date'], df["Production journaliere d'huile bbl"], 
                color='green', linewidth=2, marker='o', markersize=3)
    axes[0].set_title('Production d\'Huile', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Barils/jour', fontsize=12)
    axes[0].grid(True, alpha=0.3)
    axes[0].fill_between(df['Date'], df["Production journaliere d'huile bbl"], 
                        alpha=0.3, color='green')
    
    # Production d'eau et Watercut
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    
    # Production d'eau (barres)
    ax2.bar(df['Date'], df["Production journaliere d'eau bbl"], 
           alpha=0.6, color='lightblue', label='Production d\'eau')
    ax2.set_ylabel('Production d\'eau (bbl/jour)', fontsize=12, color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    # Watercut (ligne)
    ax2_twin.plot(df['Date'], df["Teneur en eau (Watercut)"], 
                 color='red', linewidth=2, marker='s', markersize=3, label='Watercut')
    ax2_twin.set_ylabel('Watercut (%)', fontsize=12, color='red')
    ax2_twin.tick_params(axis='y', labelcolor='red')
    
    axes[1].set_title('Production d\'Eau et Watercut', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    # Nombre de puits actifs
    axes[2].plot(df['Date'], df["Nombre des puits actifs"], 
                color='purple', linewidth=2, marker='d', markersize=4)
    axes[2].set_title('Nombre de Puits Actifs', fontsize=14, fontweight='bold')
    axes[2].set_xlabel('Date', fontsize=12)
    axes[2].set_ylabel('Nombre de Puits', fontsize=12)
    axes[2].grid(True, alpha=0.3)
    axes[2].fill_between(df['Date'], df["Nombre des puits actifs"], 
                        alpha=0.3, color='purple')
    
    # Rotation des dates pour tous les sous-graphiques
    for ax in axes:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def plot_seasonal_decomposition(df: pd.DataFrame, column: str, 
                               title: str = "Décomposition Saisonnière"):
    """
    Crée un graphique de décomposition saisonnière.
    
    Args:
        df: DataFrame contenant les données
        column: Nom de la colonne à décomposer
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    try:
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        # Préparer les données
        ts_data = df.set_index('Date')[column].dropna()
        
        # Décomposition saisonnière
        decomposition = seasonal_decompose(ts_data, model='additive', period=30)  # Période mensuelle
        
        fig, axes = plt.subplots(4, 1, figsize=(15, 12))
        fig.suptitle(f'{title} - {column}', fontsize=16, fontweight='bold')
        
        # Série originale
        decomposition.observed.plot(ax=axes[0], color='blue', linewidth=2)
        axes[0].set_title('Série Originale', fontsize=12, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        
        # Tendance
        decomposition.trend.plot(ax=axes[1], color='green', linewidth=2)
        axes[1].set_title('Tendance', fontsize=12, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        
        # Saisonnalité
        decomposition.seasonal.plot(ax=axes[2], color='orange', linewidth=2)
        axes[2].set_title('Saisonnalité', fontsize=12, fontweight='bold')
        axes[2].grid(True, alpha=0.3)
        
        # Résidus
        decomposition.resid.plot(ax=axes[3], color='red', linewidth=1)
        axes[3].set_title('Résidus', fontsize=12, fontweight='bold')
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
        
    except ImportError:
        # Fallback si statsmodels n'est pas disponible
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df['Date'], df[column], linewidth=2)
        ax.set_title(f'{title} - {column} (Décomposition non disponible)', fontsize=14)
        ax.set_xlabel('Date')
        ax.set_ylabel(column)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

def plot_forecast_with_confidence(dates, y_true, y_pred, 
                                 confidence_lower: Optional[np.ndarray] = None,
                                 confidence_upper: Optional[np.ndarray] = None,
                                 title: str = "Prévision avec Intervalles de Confiance"):
    """
    Crée un graphique de prévision avec intervalles de confiance.
    
    Args:
        dates: Dates correspondantes
        y_true: Valeurs réelles
        y_pred: Prédictions
        confidence_lower: Borne inférieure de l'intervalle de confiance
        confidence_upper: Borne supérieure de l'intervalle de confiance
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Tracer les valeurs réelles et prédites
    ax.plot(dates, y_true, label='Valeurs Réelles', color='blue', linewidth=2, marker='o', markersize=4)
    ax.plot(dates, y_pred, label='Prédictions', color='red', linewidth=2, marker='s', markersize=4, linestyle='--')
    
    # Ajouter les intervalles de confiance si disponibles
    if confidence_lower is not None and confidence_upper is not None:
        ax.fill_between(dates, confidence_lower, confidence_upper, 
                       alpha=0.3, color='red', label='Intervalle de confiance')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Valeur', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_anomaly_detection(dates, values, anomalies_mask, 
                          title: str = "Détection d'Anomalies"):
    """
    Crée un graphique de détection d'anomalies.
    
    Args:
        dates: Dates correspondantes
        values: Valeurs de la série temporelle
        anomalies_mask: Masque booléen indiquant les anomalies
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Tracer la série temporelle normale
    normal_mask = ~anomalies_mask
    ax.plot(dates[normal_mask], values[normal_mask], 
           color='blue', linewidth=2, marker='o', markersize=3, label='Valeurs normales')
    
    # Mettre en évidence les anomalies
    if anomalies_mask.any():
        ax.scatter(dates[anomalies_mask], values[anomalies_mask], 
                  color='red', s=100, marker='x', linewidth=3, label='Anomalies')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Valeur', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig