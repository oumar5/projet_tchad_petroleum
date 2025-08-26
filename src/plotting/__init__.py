"""Package des fonctions de visualisation pour l'application."""

from .basic_plots import plot_daily_production, plot_failures_by_block
from .model_plots import (
    plot_model_performance_metrics, plot_confusion_matrix, plot_roc_curve,
    plot_feature_importance, plot_prediction_vs_actual
)
from .timeseries_plots import (
    plot_time_series_forecast, plot_failure_probability_timeline,
    plot_production_components
)
from .dashboard_plots import plot_kpi_dashboard

__all__ = [
    # Basic plots
    'plot_daily_production',
    'plot_failures_by_block',
    
    # Model plots
    'plot_model_performance_metrics',
    'plot_confusion_matrix',
    'plot_roc_curve',
    'plot_feature_importance',
    'plot_prediction_vs_actual',
    
    # Time series plots
    'plot_time_series_forecast',
    'plot_failure_probability_timeline',
    'plot_production_components',
    
    # Dashboard plots
    'plot_kpi_dashboard'
]