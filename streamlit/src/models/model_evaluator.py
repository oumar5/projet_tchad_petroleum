import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc, precision_recall_curve
)
from .model_utils import ModelTrainer
import warnings
warnings.filterwarnings('ignore')

class ModelEvaluator:
    """Classe centralisée pour l'évaluation et la visualisation des modèles."""
    
    def __init__(self):
        self.evaluation_results = {}
        
    def evaluate_model(self, model, X_test: pd.DataFrame, y_test: pd.Series, 
                      model_name: str = None, **kwargs) -> Dict[str, Any]:
        """
        Évalue un modèle de façon complète.
        
        Args:
            model: Instance du modèle à évaluer
            X_test: Features de test
            y_test: Cible de test
            model_name: Nom du modèle (optionnel)
            **kwargs: Arguments supplémentaires
            
        Returns:
            Dictionnaire complet des résultats d'évaluation
        """
        if model_name is None:
            model_name = model.model_name if hasattr(model, 'model_name') else 'Unknown'
        
        # Prédictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
        
        # Évaluation selon le type de modèle
        if model.model_type == 'classification':
            metrics = self._evaluate_classification(y_test, y_pred, y_prob, model_name)
        elif model.model_type == 'regression':
            metrics = self._evaluate_regression(y_test, y_pred, model_name)
        elif model.model_type == 'timeseries':
            metrics = self._evaluate_timeseries(y_test, y_pred, model_name)
        else:
            raise ValueError(f"Type de modèle non supporté: {model.model_type}")
        
        # Ajouter des informations sur le modèle
        metrics['model_info'] = {
            'model_name': model_name,
            'model_type': model.model_type,
            'feature_count': len(model.feature_names) if hasattr(model, 'feature_names') and model.feature_names else 0,
            'is_trained': model.is_trained if hasattr(model, 'is_trained') else False
        }
        
        # Importance des features si disponible
        if hasattr(model, 'get_feature_importance'):
            feature_importance = model.get_feature_importance()
            if feature_importance is not None:
                metrics['feature_importance'] = feature_importance
        
        # Stocker les résultats
        self.evaluation_results[model_name] = metrics
        
        return metrics
    
    def _evaluate_classification(self, y_true: pd.Series, y_pred: np.ndarray, 
                               y_prob: Optional[np.ndarray], model_name: str) -> Dict[str, Any]:
        """Évalue un modèle de classification."""
        # Métriques de base utilisant les utilitaires communs
        metrics = ModelTrainer.calculate_metrics(y_true, y_pred, model_type='classification')
        
        # Matrice de confusion
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm
        
        # Rapport de classification détaillé
        class_report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        metrics['classification_report'] = class_report
        
        # Métriques pour classification binaire
        if len(np.unique(y_true)) == 2 and y_prob is not None:
            if y_prob.ndim > 1:
                y_prob_binary = y_prob[:, 1]
            else:
                y_prob_binary = y_prob
            
            # ROC-AUC
            try:
                fpr, tpr, _ = roc_curve(y_true, y_prob_binary)
                roc_auc = auc(fpr, tpr)
                metrics['roc_auc'] = roc_auc
                metrics['roc_curve'] = {'fpr': fpr, 'tpr': tpr}
            except Exception:
                metrics['roc_auc'] = 0.0
            
            # Precision-Recall curve
            try:
                precision, recall, _ = precision_recall_curve(y_true, y_prob_binary)
                pr_auc = auc(recall, precision)
                metrics['pr_auc'] = pr_auc
                metrics['pr_curve'] = {'precision': precision, 'recall': recall}
            except Exception:
                metrics['pr_auc'] = 0.0
        
        return metrics
    
    def _evaluate_regression(self, y_true: pd.Series, y_pred: np.ndarray, model_name: str) -> Dict[str, Any]:
        """Évalue un modèle de régression."""
        # Métriques de base utilisant les utilitaires communs
        metrics = ModelTrainer.calculate_metrics(y_true, y_pred, model_type='regression')
        
        # MAPE (Mean Absolute Percentage Error)
        try:
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            metrics['mape'] = mape if not np.isnan(mape) and not np.isinf(mape) else 0.0
        except:
            metrics['mape'] = 0.0
        
        # Résidus
        residuals = y_pred - y_true
        metrics['residuals'] = {
            'mean': np.mean(residuals),
            'std': np.std(residuals),
            'min': np.min(residuals),
            'max': np.max(residuals)
        }
        
        return metrics
    
    def _evaluate_timeseries(self, y_true: pd.Series, y_pred: np.ndarray, model_name: str) -> Dict[str, Any]:
        """Évalue un modèle de série temporelle."""
        # Commencer par les métriques de régression
        metrics = self._evaluate_regression(y_true, y_pred, model_name)
        
        # Métriques spécifiques aux séries temporelles
        try:
            # Directional Accuracy
            if len(y_true) > 1:
                true_direction = np.diff(y_true) > 0
                pred_direction = np.diff(y_pred) > 0
                directional_accuracy = np.mean(true_direction == pred_direction)
                metrics['directional_accuracy'] = directional_accuracy
            
            # Theil's U statistic
            if np.sum(y_true**2) > 0:
                theil_u = np.sqrt(np.mean((y_pred - y_true)**2)) / np.sqrt(np.mean(y_true**2))
                metrics['theil_u'] = theil_u if not np.isnan(theil_u) else 0.0
            
            # Mean Absolute Scaled Error (MASE)
            if len(y_true) > 1:
                naive_forecast_error = np.mean(np.abs(np.diff(y_true)))
                if naive_forecast_error > 0:
                    mase = np.mean(np.abs(y_true - y_pred)) / naive_forecast_error
                    metrics['mase'] = mase if not np.isnan(mase) else 0.0
        
        except Exception as e:
            print(f"Erreur lors du calcul des métriques de série temporelle: {e}")
        
        return metrics
    
    def plot_confusion_matrix(self, model_name: str, figsize: Tuple[int, int] = (8, 6), 
                            class_names: Optional[List[str]] = None) -> plt.Figure:
        """Crée un graphique de matrice de confusion."""
        if model_name not in self.evaluation_results:
            raise ValueError(f"Modèle {model_name} non trouvé dans les résultats.")
        
        results = self.evaluation_results[model_name]
        if 'confusion_matrix' not in results:
            raise ValueError(f"Matrice de confusion non disponible pour {model_name}.")
        
        cm = results['confusion_matrix']
        
        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                    xticklabels=class_names or ['Classe 0', 'Classe 1'],
                    yticklabels=class_names or ['Classe 0', 'Classe 1'])
        
        ax.set_title(f'Matrice de Confusion - {model_name}')
        ax.set_xlabel('Prédictions')
        ax.set_ylabel('Valeurs Réelles')
        
        plt.tight_layout()
        return fig
    
    def plot_roc_curve(self, model_names: List[str] = None, figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """Crée un graphique des courbes ROC."""
        if model_names is None:
            model_names = list(self.evaluation_results.keys())
        
        fig, ax = plt.subplots(figsize=figsize)
        
        for model_name in model_names:
            if model_name not in self.evaluation_results:
                continue
            
            results = self.evaluation_results[model_name]
            if 'roc_curve' not in results:
                continue
            
            fpr = results['roc_curve']['fpr']
            tpr = results['roc_curve']['tpr']
            roc_auc = results.get('roc_auc', 0)
            
            ax.plot(fpr, tpr, lw=2, label=f'{model_name} (AUC = {roc_auc:.3f})')
        
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Aléatoire')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('Taux de Faux Positifs')
        ax.set_ylabel('Taux de Vrais Positifs')
        ax.set_title('Courbes ROC')
        ax.legend(loc="lower right")
        ax.grid(True)
        
        plt.tight_layout()
        return fig
    
    def plot_prediction_vs_actual(self, model_name: str, y_true: pd.Series, y_pred: np.ndarray,
                                 figsize: Tuple[int, int] = (12, 5)) -> plt.Figure:
        """Crée un graphique prédictions vs valeurs réelles."""
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Scatter plot
        axes[0].scatter(y_true, y_pred, alpha=0.6, color='blue')
        axes[0].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 
                    'r--', lw=2, label='Ligne parfaite')
        axes[0].set_xlabel('Valeurs Réelles')
        axes[0].set_ylabel('Prédictions')
        axes[0].set_title(f'Prédictions vs Réalité - {model_name}')
        axes[0].legend()
        axes[0].grid(True)
        
        # Résidus
        residuals = y_pred - y_true
        axes[1].scatter(y_pred, residuals, alpha=0.6, color='green')
        axes[1].axhline(y=0, color='r', linestyle='--')
        axes[1].set_xlabel('Prédictions')
        axes[1].set_ylabel('Résidus')
        axes[1].set_title(f'Graphique des Résidus - {model_name}')
        axes[1].grid(True)
        
        plt.tight_layout()
        return fig
    
    def plot_feature_importance(self, model_name: str, top_n: int = 15, 
                              figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """Crée un graphique d'importance des features."""
        if model_name not in self.evaluation_results:
            raise ValueError(f"Modèle {model_name} non trouvé dans les résultats.")
        
        results = self.evaluation_results[model_name]
        if 'feature_importance' not in results:
            raise ValueError(f"Importance des features non disponible pour {model_name}.")
        
        feature_importance = results['feature_importance'].head(top_n)
        
        fig, ax = plt.subplots(figsize=figsize)
        sns.barplot(data=feature_importance, x='importance', y='feature', ax=ax, palette='viridis')
        
        ax.set_title(f'Top {top_n} Features les Plus Importantes - {model_name}')
        ax.set_xlabel('Importance')
        ax.set_ylabel('Features')
        
        # Ajouter les valeurs sur les barres
        for i, v in enumerate(feature_importance['importance']):
            ax.text(v + 0.001, i, f'{v:.3f}', va='center')
        
        plt.tight_layout()
        return fig
    
    def plot_model_comparison(self, metric: str = 'accuracy', figsize: Tuple[int, int] = (12, 6)) -> plt.Figure:
        """Compare les performances de plusieurs modèles."""
        if not self.evaluation_results:
            raise ValueError("Aucun résultat d'évaluation disponible.")
        
        # Extraire les métriques
        model_names = []
        metric_values = []
        
        for name, results in self.evaluation_results.items():
            if metric in results:
                model_names.append(name)
                metric_values.append(results[metric])
        
        if not model_names:
            raise ValueError(f"Métrique {metric} non trouvée dans les résultats.")
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=figsize)
        bars = ax.bar(model_names, metric_values, color='skyblue', alpha=0.7)
        
        # Ajouter les valeurs sur les barres
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{value:.3f}', ha='center', va='bottom')
        
        ax.set_title(f'Comparaison des Modèles - {metric.upper()}')
        ax.set_ylabel(metric.upper())
        ax.set_xlabel('Modèles')
        plt.xticks(rotation=45)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def generate_report(self, model_name: str) -> str:
        """Génère un rapport textuel détaillé pour un modèle."""
        if model_name not in self.evaluation_results:
            raise ValueError(f"Modèle {model_name} non trouvé dans les résultats.")
        
        results = self.evaluation_results[model_name]
        model_info = results.get('model_info', {})
        
        report = f"\n{'='*50}\n"
        report += f"RAPPORT D'ÉVALUATION - {model_name.upper()}\n"
        report += f"{'='*50}\n\n"
        
        # Informations du modèle
        report += "INFORMATIONS DU MODÈLE:\n"
        report += f"- Type: {model_info.get('model_type', 'N/A')}\n"
        report += f"- Nombre de features: {model_info.get('feature_count', 'N/A')}\n"
        report += f"- Statut: {'Entraîné' if model_info.get('is_trained', False) else 'Non entraîné'}\n\n"
        
        # Métriques selon le type
        if model_info.get('model_type') == 'classification':
            report += "MÉTRIQUES DE CLASSIFICATION:\n"
            report += f"- Accuracy: {results.get('accuracy', 0):.4f}\n"
            report += f"- Precision: {results.get('precision', 0):.4f}\n"
            report += f"- Recall: {results.get('recall', 0):.4f}\n"
            report += f"- F1-Score: {results.get('f1_score', 0):.4f}\n"
            if 'roc_auc' in results:
                report += f"- ROC-AUC: {results['roc_auc']:.4f}\n"
        
        elif model_info.get('model_type') in ['regression', 'timeseries']:
            report += "MÉTRIQUES DE RÉGRESSION:\n"
            report += f"- R²: {results.get('r2', 0):.4f}\n"
            report += f"- RMSE: {results.get('rmse', 0):.4f}\n"
            report += f"- MAE: {results.get('mae', 0):.4f}\n"
            report += f"- MAPE: {results.get('mape', 0):.2f}%\n"
            
            if model_info.get('model_type') == 'timeseries':
                report += "\nMÉTRIQUES SPÉCIFIQUES AUX SÉRIES TEMPORELLES:\n"
                if 'directional_accuracy' in results:
                    report += f"- Précision directionnelle: {results['directional_accuracy']:.4f}\n"
                if 'theil_u' in results:
                    report += f"- Theil's U: {results['theil_u']:.4f}\n"
        
        # Top features si disponible
        if 'feature_importance' in results:
            report += "\nTOP 10 FEATURES LES PLUS IMPORTANTES:\n"
            top_features = results['feature_importance'].head(10)
            for idx, row in top_features.iterrows():
                report += f"- {row['feature']}: {row['importance']:.4f}\n"
        
        report += f"\n{'='*50}\n"
        
        return report
    
    def export_results(self, filepath: str, format: str = 'json'):
        """Exporte les résultats d'évaluation."""
        if format == 'json':
            import json
            # Convertir les arrays numpy en listes pour la sérialisation JSON
            exportable_results = {}
            for model_name, results in self.evaluation_results.items():
                exportable_results[model_name] = self._make_json_serializable(results)
            
            with open(filepath, 'w') as f:
                json.dump(exportable_results, f, indent=2)
        
        elif format == 'csv':
            # Créer un DataFrame avec les métriques principales
            metrics_data = []
            for model_name, results in self.evaluation_results.items():
                row = {'model_name': model_name}
                # Ajouter les métriques numériques
                for key, value in results.items():
                    if isinstance(value, (int, float)):
                        row[key] = value
                metrics_data.append(row)
            
            df = pd.DataFrame(metrics_data)
            df.to_csv(filepath, index=False)
        
        else:
            raise ValueError(f"Format non supporté: {format}. Utilisez 'json' ou 'csv'.")
    
    def _make_json_serializable(self, obj):
        """Convertit les objets non sérialisables en JSON."""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        else:
            return obj
    
    def clear_results(self):
        """Efface tous les résultats d'évaluation."""
        self.evaluation_results.clear()
    
    def get_best_model(self, metric: str = 'accuracy') -> Optional[str]:
        """Retourne le nom du meilleur modèle selon une métrique."""
        if not self.evaluation_results:
            return None
        
        best_score = float('-inf')
        best_model = None
        
        for model_name, results in self.evaluation_results.items():
            if metric in results:
                score = results[metric]
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        return best_model