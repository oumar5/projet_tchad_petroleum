import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Configuration du style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def plot_daily_production(df: pd.DataFrame, title: str = "Production Journalière d'Huile"):
    """
    Crée un graphique de la production journalière d'huile.
    
    Args:
        df: DataFrame contenant les données de production
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['Date'], df["Production journaliere d'huile bbl"], 
           color='green', linewidth=2, marker='o', markersize=3)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Production (barils/jour)', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Rotation des dates pour une meilleure lisibilité
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_failures_by_block(failures_df: pd.DataFrame, title: str = "Répartition des Pannes par Bloc"):
    """
    Crée un graphique en barres des pannes par bloc.
    
    Args:
        failures_df: DataFrame contenant les données de pannes
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    if failures_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Aucune donnée de panne disponible', 
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title)
        return fig
    
    # Compter les pannes par bloc
    if 'Bloc Faillé' in failures_df.columns:
        block_counts = failures_df['Bloc Faillé'].value_counts()
    elif 'Bloc' in failures_df.columns:
        block_counts = failures_df['Bloc'].value_counts()
    else:
        # Fallback si aucune colonne de bloc n'est trouvée
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Aucune colonne de bloc trouvée dans les données', 
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title)
        return fig
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(block_counts.index, block_counts.values, 
                 color='coral', alpha=0.7, edgecolor='black')
    
    # Ajouter les valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
               f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Bloc', fontsize=12)
    ax.set_ylabel('Nombre de Pannes', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    return fig

def plot_watercut_evolution(df: pd.DataFrame, title: str = "Évolution du Watercut"):
    """
    Crée un graphique de l'évolution du watercut.
    
    Args:
        df: DataFrame contenant les données de production
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['Date'], df["Teneur en eau (Watercut)"], 
           color='red', linewidth=2, marker='o', markersize=3)
    
    # Ajouter des zones de couleur pour les seuils critiques
    ax.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Seuil critique (80%)')
    ax.axhline(y=60, color='orange', linestyle='--', alpha=0.7, label='Seuil d\'attention (60%)')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Watercut (%)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Rotation des dates
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_wells_activity(df: pd.DataFrame, title: str = "Activité des Puits"):
    """
    Crée un graphique de l'activité des puits.
    
    Args:
        df: DataFrame contenant les données de production
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['Date'], df["Nombre des puits actifs"], 
           color='blue', linewidth=2, marker='s', markersize=4)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Nombre de Puits Actifs', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Remplir l'aire sous la courbe
    ax.fill_between(df['Date'], df["Nombre des puits actifs"], alpha=0.3, color='blue')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig