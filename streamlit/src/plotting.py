"""Module de compatibilité pour les imports de plotting.

Ce module maintient la compatibilité avec l'ancien système d'imports
en réexportant toutes les fonctions des modules spécialisés.
"""

# Imports depuis les modules spécialisés
from .plotting.basic_plots import (
    plot_daily_production,
    plot_failures_by_block,
    plot_watercut_evolution,
    plot_wells_activity
)

from .plotting.model_plots import (
    plot_model_performance_metrics,
    plot_confusion_matrix,
    plot_roc_curve,
    plot_feature_importance,
    plot_prediction_vs_actual,
    plot_learning_curves,
    plot_residuals_distribution
)

from .plotting.timeseries_plots import (
    plot_time_series_forecast,
    plot_failure_probability_timeline,
    plot_production_components,
    plot_seasonal_decomposition,
    plot_forecast_with_confidence,
    plot_anomaly_detection
)

from .plotting.dashboard_plots import (
    plot_kpi_dashboard,
    plot_trend_analysis,
    plot_correlation_heatmap
)

# Réexporter toutes les fonctions pour maintenir la compatibilité
__all__ = [
    # Basic plots
    'plot_daily_production',
    'plot_failures_by_block',
    'plot_watercut_evolution',
    'plot_wells_activity',
    
    # Model plots
    'plot_model_performance_metrics',
    'plot_confusion_matrix',
    'plot_roc_curve',
    'plot_feature_importance',
    'plot_prediction_vs_actual',
    'plot_learning_curves',
    'plot_residuals_distribution',
    
    # Time series plots
    'plot_time_series_forecast',
    'plot_failure_probability_timeline',
    'plot_production_components',
    'plot_seasonal_decomposition',
    'plot_forecast_with_confidence',
    'plot_anomaly_detection',
    
    # Dashboard plots
    'plot_kpi_dashboard',
    'plot_trend_analysis',
    'plot_correlation_heatmap'
]