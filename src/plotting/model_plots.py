import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc
from typing import Dict, Any, Optional

# Configuration du style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def plot_model_performance_metrics(metrics: Dict[str, Any], model_name: str = "Modèle"):
    """
    Crée un graphique des métriques de performance d'un modèle.
    
    Args:
        metrics: Dictionnaire contenant les métriques
        model_name: Nom du modèle
        
    Returns:
        Figure matplotlib
    """
    # Déterminer le type de modèle basé sur les métriques disponibles
    is_classification = 'accuracy' in metrics
    
    if is_classification:
        return _plot_classification_metrics(metrics, model_name)
    else:
        return _plot_regression_metrics(metrics, model_name)

def _plot_classification_metrics(metrics: Dict[str, Any], model_name: str):
    """Graphique des métriques de classification."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Métriques de Performance - {model_name}', fontsize=16, fontweight='bold')
    
    # Métriques principales
    main_metrics = ['accuracy', 'precision', 'recall', 'f1_score']
    metric_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    colors = ['skyblue', 'lightgreen', 'lightcoral', 'lightsalmon']
    
    for i, (metric, name, color) in enumerate(zip(main_metrics, metric_names, colors)):
        row, col = i // 2, i % 2
        ax = axes[row, col]
        
        value = metrics.get(metric, 0)
        
        # Graphique en barres
        bar = ax.bar([name], [value], color=color, alpha=0.7, edgecolor='black')
        ax.set_ylim(0, 1)
        ax.set_ylabel('Score')
        ax.set_title(f'{name}: {value:.3f}')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Ajouter la valeur sur la barre
        ax.text(0, value + 0.02, f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    return fig

def _plot_regression_metrics(metrics: Dict[str, Any], model_name: str):
    """Graphique des métriques de régression."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Métriques de Performance - {model_name}', fontsize=16, fontweight='bold')
    
    # Métriques principales
    main_metrics = ['r2', 'rmse', 'mae', 'mape']
    metric_names = ['R²', 'RMSE', 'MAE', 'MAPE (%)']
    colors = ['lightblue', 'lightcoral', 'lightgreen', 'lightsalmon']
    
    for i, (metric, name, color) in enumerate(zip(main_metrics, metric_names, colors)):
        row, col = i // 2, i % 2
        ax = axes[row, col]
        
        value = metrics.get(metric, 0)
        
        # Graphique en barres
        bar = ax.bar([name], [value], color=color, alpha=0.7, edgecolor='black')
        
        if metric == 'r2':
            ax.set_ylim(0, 1)
        else:
            ax.set_ylim(0, max(value * 1.2, 0.1))
        
        ax.set_ylabel('Valeur')
        ax.set_title(f'{name}: {value:.3f}')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Ajouter la valeur sur la barre
        ax.text(0, value + max(value * 0.05, 0.01), f'{value:.3f}', 
               ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    return fig

def plot_confusion_matrix(y_true, y_pred, class_names: Optional[list] = None, 
                         title: str = "Matrice de Confusion"):
    """
    Crée une matrice de confusion.
    
    Args:
        y_true: Vraies étiquettes
        y_pred: Prédictions
        class_names: Noms des classes
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    cm = confusion_matrix(y_true, y_pred)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Utiliser seaborn pour une belle heatmap
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=class_names or ['Classe 0', 'Classe 1'],
                yticklabels=class_names or ['Classe 0', 'Classe 1'])
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Prédictions', fontsize=12)
    ax.set_ylabel('Valeurs Réelles', fontsize=12)
    
    plt.tight_layout()
    return fig

def plot_roc_curve(y_true, y_prob, title: str = "Courbe ROC"):
    """
    Crée une courbe ROC.
    
    Args:
        y_true: Vraies étiquettes
        y_prob: Probabilités prédites
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(fpr, tpr, color='darkorange', lw=2, 
           label=f'Courbe ROC (AUC = {roc_auc:.3f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', 
           label='Aléatoire (AUC = 0.5)')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('Taux de Faux Positifs', fontsize=12)
    ax.set_ylabel('Taux de Vrais Positifs', fontsize=12)
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_feature_importance(feature_importance_df: pd.DataFrame, 
                          title: str = "Importance des Features", top_n: int = 15):
    """
    Crée un graphique d'importance des features.
    
    Args:
        feature_importance_df: DataFrame avec colonnes 'feature' et 'importance'
        title: Titre du graphique
        top_n: Nombre de features à afficher
        
    Returns:
        Figure matplotlib
    """
    # Prendre les top N features
    top_features = feature_importance_df.head(top_n)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Graphique en barres horizontales
    bars = ax.barh(range(len(top_features)), top_features['importance'], 
                  color='viridis', alpha=0.7)
    
    # Personnaliser l'axe y
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features['feature'])
    ax.invert_yaxis()  # Pour avoir la feature la plus importante en haut
    
    ax.set_xlabel('Importance', fontsize=12)
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Ajouter les valeurs sur les barres
    for i, (bar, importance) in enumerate(zip(bars, top_features['importance'])):
        ax.text(importance + 0.001, i, f'{importance:.3f}', 
               va='center', fontweight='bold')
    
    plt.tight_layout()
    return fig

def plot_prediction_vs_actual(y_true, y_pred, title: str = "Prédictions vs Valeurs Réelles"):
    """
    Crée un graphique prédictions vs valeurs réelles.
    
    Args:
        y_true: Valeurs réelles
        y_pred: Prédictions
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Scatter plot
    axes[0].scatter(y_true, y_pred, alpha=0.6, color='blue', s=50)
    
    # Ligne parfaite
    min_val = min(min(y_true), min(y_pred))
    max_val = max(max(y_true), max(y_pred))
    axes[0].plot([min_val, max_val], [min_val, max_val], 
                'r--', lw=2, label='Prédiction parfaite')
    
    axes[0].set_xlabel('Valeurs Réelles', fontsize=12)
    axes[0].set_ylabel('Prédictions', fontsize=12)
    axes[0].set_title('Prédictions vs Réalité', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Graphique des résidus
    residuals = y_pred - y_true
    axes[1].scatter(y_pred, residuals, alpha=0.6, color='green', s=50)
    axes[1].axhline(y=0, color='r', linestyle='--', lw=2)
    
    axes[1].set_xlabel('Prédictions', fontsize=12)
    axes[1].set_ylabel('Résidus', fontsize=12)
    axes[1].set_title('Graphique des Résidus', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    fig.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    return fig

def plot_learning_curves(train_scores: list, val_scores: list, 
                        title: str = "Courbes d'Apprentissage"):
    """
    Crée un graphique des courbes d'apprentissage.
    
    Args:
        train_scores: Scores d'entraînement
        val_scores: Scores de validation
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    epochs = range(1, len(train_scores) + 1)
    
    ax.plot(epochs, train_scores, 'b-', label='Score d\'entraînement', linewidth=2)
    ax.plot(epochs, val_scores, 'r-', label='Score de validation', linewidth=2)
    
    ax.set_xlabel('Époques', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_residuals_distribution(residuals, title: str = "Distribution des Résidus"):
    """
    Crée un graphique de distribution des résidus.
    
    Args:
        residuals: Résidus du modèle
        title: Titre du graphique
        
    Returns:
        Figure matplotlib
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Histogramme
    axes[0].hist(residuals, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0].axvline(x=0, color='red', linestyle='--', linewidth=2)
    axes[0].set_xlabel('Résidus', fontsize=12)
    axes[0].set_ylabel('Fréquence', fontsize=12)
    axes[0].set_title('Histogramme des Résidus', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Q-Q plot
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=axes[1])
    axes[1].set_title('Q-Q Plot (Normalité)', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    fig.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    return fig