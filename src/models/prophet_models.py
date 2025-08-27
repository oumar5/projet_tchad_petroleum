import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from .base_model import BaseModel
from .model_utils import (
    DataValidator, FeatureEngineer, ModelTrainer, PredictionValidator,
    log_model_info, validate_model_requirements, get_default_hyperparameters
)
import warnings
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

try:
    from neuralprophet import NeuralProphet
    NEURALPROPHET_AVAILABLE = True
except ImportError:
    NEURALPROPHET_AVAILABLE = False
    NeuralProphet = None

class ProphetModels(BaseModel):
    """Implémentation des modèles Prophet et NeuralProphet pour les séries temporelles."""
    
    def __init__(self, algorithm: str = 'prophet'):
        """
        Initialise le modèle Prophet.
        
        Args:
            algorithm: Type d'algorithme ('prophet' ou 'neuralprophet')
        """
        if algorithm == 'prophet' and not PROPHET_AVAILABLE:
            raise ImportError("Prophet n'est pas installé. Installez-le avec: pip install prophet")
        elif algorithm == 'neuralprophet' and not NEURALPROPHET_AVAILABLE:
            raise ImportError("NeuralProphet n'est pas installé. Installez-le avec: pip install neuralprophet")
        
        model_name = f"{algorithm}_timeseries"
        super().__init__(model_name, 'timeseries')
        self.algorithm = algorithm
        self.original_data = None
        self.forecast_data = None
        
    def prepare_data(self, df: pd.DataFrame, target_col: str, date_col: str = 'Date', **kwargs) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prépare les données pour Prophet/NeuralProphet.
        
        Args:
            df: DataFrame contenant les données
            target_col: Nom de la colonne cible
            date_col: Nom de la colonne de date
            **kwargs: Arguments supplémentaires
            
        Returns:
            Tuple contenant les données formatées pour Prophet (ds, y)
        """
        # Validation des données d'entrée
        DataValidator.validate_input_data(df, target_col, min_samples=10)
        
        # Copier et nettoyer les données
        data = df.copy()
        data[date_col] = pd.to_datetime(data[date_col])
        data = data.sort_values(date_col)
        
        # Format Prophet: colonnes 'ds' (date) et 'y' (valeur)
        prophet_data = pd.DataFrame({
            'ds': data[date_col],
            'y': data[target_col]
        })
        
        # Nettoyer les valeurs manquantes
        prophet_data = DataValidator.clean_nan_values(prophet_data, strategy='median')
        
        # Ajouter des régresseurs externes si spécifiés
        external_regressors = kwargs.get('external_regressors', [])
        for regressor in external_regressors:
            if regressor in data.columns:
                prophet_data[regressor] = data[regressor].values[:len(prophet_data)]
        
        self.target_name = target_col
        self.original_data = prophet_data.copy()
        
        return prophet_data, prophet_data['y']
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, Any]:
        """
        Entraîne le modèle Prophet/NeuralProphet.
        
        Args:
            X: Données formatées pour Prophet (avec colonnes ds, y)
            y: Série cible (non utilisée directement)
            **kwargs: Arguments supplémentaires
            
        Returns:
            Dictionnaire contenant les métriques d'entraînement
        """
        # Diviser les données chronologiquement
        test_size = kwargs.get('test_size', 0.2)
        split_idx = int(len(X) * (1 - test_size))
        
        train_data = X.iloc[:split_idx].copy()
        test_data = X.iloc[split_idx:].copy()
        
        # Créer et configurer le modèle
        if self.algorithm == 'prophet':
            self.model = self._create_prophet_model(**kwargs)
            
            # Ajouter des régresseurs externes
            external_regressors = kwargs.get('external_regressors', [])
            for regressor in external_regressors:
                if regressor in train_data.columns:
                    self.model.add_regressor(regressor)
            
            # Entraîner le modèle
            self.model.fit(train_data)
            
        elif self.algorithm == 'neuralprophet':
            self.model = self._create_neuralprophet_model(**kwargs)
            
            # Entraîner le modèle (NeuralProphet n'utilise pas freq dans fit)
            try:
                metrics = self.model.fit(train_data)
            except Exception as e:
                raise ValueError(f"Erreur lors de l'entraînement NeuralProphet: {e}")
        
        # Faire des prédictions sur les données de test
        test_periods = len(test_data)
        
        try:
            if self.algorithm == 'prophet':
                future = self.model.make_future_dataframe(periods=test_periods, freq='D')
            else:  # neuralprophet
                future = self.model.make_future_dataframe(periods=test_periods)
        except Exception as e:
            # Fallback : créer le future dataframe manuellement
            last_date = train_data['ds'].max()
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=test_periods, freq='D')
            all_dates = pd.concat([train_data['ds'], pd.Series(future_dates)])
            future = pd.DataFrame({'ds': all_dates})
        
        # Ajouter les régresseurs externes pour les prédictions
        external_regressors = kwargs.get('external_regressors', [])
        for regressor in external_regressors:
            if regressor in X.columns and len(X[regressor]) >= len(future):
                future[regressor] = X[regressor].values[:len(future)]
        
        # Prédictions
        if self.algorithm == 'prophet':
            forecast = self.model.predict(future)
            y_pred_train = forecast['yhat'].iloc[:split_idx].values
            y_pred_test = forecast['yhat'].iloc[split_idx:].values
        else:  # neuralprophet
            forecast = self.model.predict(future)
            y_pred_train = forecast['yhat1'].iloc[:split_idx].values
            y_pred_test = forecast['yhat1'].iloc[split_idx:].values
        
        # Évaluation
        y_train = train_data['y'].values
        y_test = test_data['y'].values
        
        self.training_metrics = self.evaluate_timeseries(y_train, y_pred_train)
        self.validation_metrics = self.evaluate_timeseries(y_test, y_pred_test)
        
        self.is_trained = True
        self.forecast_data = forecast
        
        return {
            'training_metrics': self.training_metrics,
            'validation_metrics': self.validation_metrics,
            'forecast': forecast,
            'train_data': train_data,
            'test_data': test_data,
            'y_pred_train': y_pred_train,
            'y_pred_test': y_pred_test
        }
    
    def _create_prophet_model(self, **kwargs):
        """Crée un modèle Prophet avec les paramètres spécifiés."""
        return Prophet(
            growth=kwargs.get('growth', 'linear'),
            changepoints=kwargs.get('changepoints', None),
            n_changepoints=kwargs.get('n_changepoints', 25),
            changepoint_range=kwargs.get('changepoint_range', 0.8),
            yearly_seasonality=kwargs.get('yearly_seasonality', 'auto'),
            weekly_seasonality=kwargs.get('weekly_seasonality', 'auto'),
            daily_seasonality=kwargs.get('daily_seasonality', 'auto'),
            holidays=kwargs.get('holidays', None),
            seasonality_mode=kwargs.get('seasonality_mode', 'additive'),
            seasonality_prior_scale=kwargs.get('seasonality_prior_scale', 10.0),
            holidays_prior_scale=kwargs.get('holidays_prior_scale', 10.0),
            changepoint_prior_scale=kwargs.get('changepoint_prior_scale', 0.05),
            mcmc_samples=kwargs.get('mcmc_samples', 0),
            interval_width=kwargs.get('interval_width', 0.80),
            uncertainty_samples=kwargs.get('uncertainty_samples', 1000)
        )
    
    def _create_neuralprophet_model(self, **kwargs):
        """Crée un modèle NeuralProphet avec les paramètres spécifiés."""
        # Paramètres compatibles avec NeuralProphet v0.5+
        model_params = {
            'growth': kwargs.get('growth', 'linear'),
            'n_changepoints': kwargs.get('n_changepoints', 10),
            'changepoints_range': kwargs.get('changepoints_range', 0.8),
            'trend_reg': kwargs.get('trend_reg', 0),
            'yearly_seasonality': kwargs.get('yearly_seasonality', 'auto'),
            'weekly_seasonality': kwargs.get('weekly_seasonality', 'auto'),
            'daily_seasonality': kwargs.get('daily_seasonality', 'auto'),
            'seasonality_mode': kwargs.get('seasonality_mode', 'additive'),
            'seasonality_reg': kwargs.get('seasonality_reg', 0),
            'n_forecasts': kwargs.get('n_forecasts', 1),
            'n_lags': kwargs.get('n_lags', 0),
            'normalize': kwargs.get('normalize', 'auto'),
            'impute_missing': kwargs.get('impute_missing', True)
        }
        
        # Ajouter les paramètres optionnels seulement s'ils sont fournis
        optional_params = ['learning_rate', 'epochs', 'batch_size']
        for param in optional_params:
            if kwargs.get(param) is not None:
                model_params[param] = kwargs[param]
        
        return NeuralProphet(**model_params)
    
    def predict(self, periods: int = 30, **kwargs) -> np.ndarray:
        """
        Fait des prédictions futures.
        
        Args:
            periods: Nombre de périodes à prédire
            **kwargs: Arguments supplémentaires
            
        Returns:
            Array des prédictions
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions.")
        
        # Valider le paramètre periods
        if periods is None:
            periods = 30
        if not isinstance(periods, int) or periods <= 0:
            raise ValueError(f"periods doit être un entier positif, reçu: {periods}")
        
        # Créer le dataframe futur
        try:
            if self.algorithm == 'prophet':
                future = self.model.make_future_dataframe(periods=periods, freq='D')
            else:  # neuralprophet
                # NeuralProphet n'utilise pas le paramètre freq
                future = self.model.make_future_dataframe(periods=periods)
        except Exception as e:
            raise ValueError(f"Erreur lors de la création du dataframe futur: {e}")
        
        # Ajouter les régresseurs externes si nécessaire
        external_regressors = kwargs.get('external_regressors', {})
        for regressor, values in external_regressors.items():
            if len(values) >= len(future):
                future[regressor] = values[:len(future)]
        
        # Prédictions
        forecast = self.model.predict(future)
        
        if self.algorithm == 'prophet':
            predictions = forecast['yhat'].tail(periods).values
        else:  # neuralprophet
            predictions = forecast['yhat1'].tail(periods).values
        
        return predictions
    
    def get_forecast_components(self) -> Optional[pd.DataFrame]:
        """
        Retourne les composantes de la prévision (tendance, saisonnalité, etc.).
        
        Returns:
            DataFrame avec les composantes ou None
        """
        if not self.is_trained or self.forecast_data is None:
            return None
        
        if self.algorithm == 'prophet':
            components = self.model.predict(self.original_data)
            return components[['ds', 'yhat', 'trend', 'yearly', 'weekly']]
        else:
            # NeuralProphet a une structure différente
            return self.forecast_data
    
    def plot_forecast(self, **kwargs):
        """
        Crée un graphique de la prévision.
        
        Returns:
            Figure matplotlib
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de créer des graphiques.")
        
        if self.algorithm == 'prophet':
            fig = self.model.plot(self.forecast_data, **kwargs)
            return fig
        else:
            # Pour NeuralProphet, utiliser leur méthode de plotting
            fig = self.model.plot(self.forecast_data, **kwargs)
            return fig
    
    def plot_components(self, **kwargs):
        """
        Crée un graphique des composantes de la prévision.
        
        Returns:
            Figure matplotlib
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de créer des graphiques.")
        
        if self.algorithm == 'prophet':
            fig = self.model.plot_components(self.forecast_data, **kwargs)
            return fig
        else:
            # NeuralProphet a sa propre méthode
            fig = self.model.plot_components(self.forecast_data, **kwargs)
            return fig
    
    def cross_validation(self, initial: str = '730 days', period: str = '180 days', 
                        horizon: str = '365 days', **kwargs) -> pd.DataFrame:
        """
        Effectue une validation croisée temporelle.
        
        Args:
            initial: Période initiale d'entraînement
            period: Période entre les cutoffs
            horizon: Horizon de prévision
            **kwargs: Arguments supplémentaires
            
        Returns:
            DataFrame avec les résultats de validation croisée
        """
        if not self.is_trained or self.algorithm != 'prophet':
            raise ValueError("La validation croisée n'est disponible que pour Prophet entraîné.")
        
        from prophet.diagnostics import cross_validation, performance_metrics
        
        # Validation croisée
        df_cv = cross_validation(
            self.model, 
            initial=initial, 
            period=period, 
            horizon=horizon,
            **kwargs
        )
        
        # Métriques de performance
        df_p = performance_metrics(df_cv)
        
        return df_cv, df_p
    
    def detect_anomalies(self, threshold: float = 0.95) -> pd.DataFrame:
        """
        Détecte les anomalies dans les données.
        
        Args:
            threshold: Seuil de confiance pour la détection d'anomalies
            
        Returns:
            DataFrame avec les anomalies détectées
        """
        if not self.is_trained or self.forecast_data is None:
            raise ValueError("Le modèle doit être entraîné pour détecter les anomalies.")
        
        forecast = self.forecast_data.copy()
        
        if self.algorithm == 'prophet':
            # Calculer les bornes de confiance
            forecast['anomaly'] = (
                (self.original_data['y'] < forecast['yhat_lower']) |
                (self.original_data['y'] > forecast['yhat_upper'])
            )
        else:
            # Pour NeuralProphet, utiliser l'écart-type
            residuals = self.original_data['y'] - forecast['yhat1']
            std_residuals = residuals.std()
            threshold_value = std_residuals * 2  # 2 sigma
            
            forecast['anomaly'] = np.abs(residuals) > threshold_value
        
        # Retourner seulement les anomalies
        anomalies = forecast[forecast['anomaly']].copy()
        return anomalies

class ProductionProphetModel(ProphetModels):
    """Modèle Prophet spécialisé pour la prévision de production."""
    
    def __init__(self, algorithm: str = 'prophet'):
        super().__init__(algorithm)
    
    def prepare_production_data(self, df: pd.DataFrame, target_col: str = "Production journaliere d'huile bbl") -> pd.DataFrame:
        """
        Prépare les données de production pour Prophet.
        
        Args:
            df: DataFrame de production
            target_col: Colonne cible
            
        Returns:
            DataFrame formaté pour Prophet
        """
        # Préparer les données de base
        prophet_data, _ = self.prepare_data(df, target_col)
        
        # Ajouter des régresseurs spécifiques à la production
        if "Nombre des puits actifs" in df.columns:
            prophet_data['active_wells'] = df["Nombre des puits actifs"].values[:len(prophet_data)]
        
        if "Teneur en eau (Watercut)" in df.columns:
            prophet_data['watercut'] = df["Teneur en eau (Watercut)"].values[:len(prophet_data)]
        
        if "Production journaliere d'eau bbl" in df.columns:
            prophet_data['water_production'] = df["Production journaliere d'eau bbl"].values[:len(prophet_data)]
        
        return prophet_data
    
    def add_custom_seasonalities(self):
        """
        Ajoute des saisonnalités personnalisées pour la production pétrolière.
        """
        if self.algorithm == 'prophet' and self.model is not None:
            # Saisonnalité mensuelle
            self.model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            
            # Saisonnalité trimestrielle
            self.model.add_seasonality(name='quarterly', period=91.25, fourier_order=3)
    
    def add_production_holidays(self, holidays_df: pd.DataFrame):
        """
        Ajoute des jours fériés/événements spécifiques à la production.
        
        Args:
            holidays_df: DataFrame avec les colonnes 'holiday' et 'ds'
        """
        if self.algorithm == 'prophet' and self.model is not None:
            self.model.holidays = holidays_df