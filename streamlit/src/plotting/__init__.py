"""Package de fonctions de visualisation pour l'application Tchad Petroleum."""

# Import des modules de plotting
from .basic_plots import (
    plot_daily_production,
    plot_failures_by_block,
    plot_watercut_evolution,
    plot_wells_activity
)

from .model_plots import (
    plot_model_performance_metrics,
    plot_confusion_matrix,
    plot_roc_curve,
    plot_feature_importance,
    plot_prediction_vs_actual,
    plot_learning_curves,
    plot_residuals_distribution
)

from .timeseries_plots import (
    plot_time_series_forecast,
    plot_failure_probability_timeline,
    plot_production_components,
    plot_seasonal_decomposition,
    plot_forecast_with_confidence,
    plot_anomaly_detection
)

from .dashboard_plots import (
    plot_kpi_dashboard,
    plot_trend_analysis,
    plot_correlation_heatmap
)

from .download_utils import (
    add_download_button,
    add_plotly_download_button,
    create_download_section,
    display_plot_with_download,
    create_batch_download
)

# Export de toutes les fonctions
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
    'plot_correlation_heatmap',
    
    # Download utilities
    'add_download_button',
    'add_plotly_download_button',
    'create_download_section',
    'display_plot_with_download',
    'create_batch_download'
]