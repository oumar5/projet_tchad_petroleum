import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score, mean_absolute_error
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

class PredictiveMaintenanceModel:
    """Modèle de maintenance prédictive pour prédire les pannes de pompes."""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.feature_importance = None
        
    def prepare_features(self, production_df, failures_df):
        """Prépare les features pour la prédiction de pannes."""
        # Créer des features basées sur la production
        production_features = production_df.copy()
        production_features['Date'] = pd.to_datetime(production_features['Date'])
        production_features = production_features.sort_values('Date')
        
        # Features dérivées
        production_features['Production_MA_7'] = production_features["Production journaliere d'huile bbl"].rolling(window=7).mean()
        production_features['Production_MA_30'] = production_features["Production journaliere d'huile bbl"].rolling(window=30).mean()
        production_features['Production_Std_7'] = production_features["Production journaliere d'huile bbl"].rolling(window=7).std()
        production_features['Watercut_MA_7'] = production_features["Teneur en eau (Watercut)"].rolling(window=7).mean()
        production_features['Production_Trend'] = production_features["Production journaliere d'huile bbl"].diff()
        production_features['Days_Since_Start'] = (production_features['Date'] - production_features['Date'].min()).dt.days
        
        # Préparer les labels de pannes
        failures_df['Date de notification d\'endomagement de la pompe'] = pd.to_datetime(failures_df['Date de notification d\'endomagement de la pompe'])
        failure_dates = set(failures_df['Date de notification d\'endomagement de la pompe'].dt.date)
        
        # Créer le label binaire (1 si panne dans les 7 prochains jours, 0 sinon)
        production_features['Failure_Next_7_Days'] = 0
        for i, row in production_features.iterrows():
            current_date = row['Date'].date()
            for j in range(1, 8):  # Vérifier les 7 prochains jours
                future_date = current_date + pd.Timedelta(days=j)
                if future_date in failure_dates:
                    production_features.loc[i, 'Failure_Next_7_Days'] = 1
                    break
        
        # Supprimer les lignes avec des NaN
        production_features = production_features.dropna()
        
        return production_features
    
    def train(self, production_df, failures_df, test_size=0.2):
        """Entraîne le modèle de maintenance prédictive."""
        # Préparer les données
        data = self.prepare_features(production_df, failures_df)
        
        # Sélectionner les features
        feature_columns = [
            "Production journaliere d'huile bbl",
            "Production journaliere d'eau bbl",
            "Teneur en eau (Watercut)",
            "Nombre des puits actifs",
            'Production_MA_7',
            'Production_MA_30',
            'Production_Std_7',
            'Watercut_MA_7',
            'Production_Trend',
            'Days_Since_Start'
        ]
        
        X = data[feature_columns]
        y = data['Failure_Next_7_Days']
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
        
        # Normaliser les features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entraîner le modèle
        self.model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Métriques
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0)
        }
        
        # Importance des features
        self.feature_importance = pd.DataFrame({
            'feature': feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.is_trained = True
        return metrics, X_test, y_test, y_pred
    
    def predict_failure_probability(self, production_data):
        """Prédit la probabilité de panne."""
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions.")
        
        # Préparer les features
        features_scaled = self.scaler.transform(production_data)
        probabilities = self.model.predict_proba(features_scaled)[:, 1]
        
        return probabilities

class ProductionForecastModel:
    """Modèle de prévision de production d'huile."""
    
    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_time_series_features(self, df, target_col, lookback_days=30):
        """Prépare les features pour la prévision de série temporelle."""
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Features temporelles
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Day'] = df['Date'].dt.day
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['DayOfYear'] = df['Date'].dt.dayofyear
        
        # Features de lag
        for lag in [1, 7, 14, 30]:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        # Moyennes mobiles
        for window in [7, 14, 30]:
            df[f'{target_col}_MA_{window}'] = df[target_col].rolling(window=window).mean()
            df[f'{target_col}_Std_{window}'] = df[target_col].rolling(window=window).std()
        
        # Tendances
        df[f'{target_col}_Trend_7'] = df[target_col].diff(7)
        df[f'{target_col}_Trend_30'] = df[target_col].diff(30)
        
        # Supprimer les NaN
        df = df.dropna()
        
        return df
    
    def train(self, production_df, target_col="Production journaliere d'huile bbl", test_size=0.2):
        """Entraîne le modèle de prévision de production."""
        # Préparer les données
        data = self.prepare_time_series_features(production_df, target_col)
        
        # Sélectionner les features
        feature_columns = [
            'Year', 'Month', 'Day', 'DayOfWeek', 'DayOfYear',
            "Nombre des puits actifs",
            "Production journaliere d'eau bbl",
            "Teneur en eau (Watercut)"
        ]
        
        # Ajouter les features de lag et moyennes mobiles
        lag_features = [col for col in data.columns if '_lag_' in col or '_MA_' in col or '_Std_' in col or '_Trend_' in col]
        feature_columns.extend(lag_features)
        
        X = data[feature_columns]
        y = data[target_col]
        
        # Diviser les données (chronologiquement)
        split_idx = int(len(data) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Normaliser les features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entraîner le modèle
        self.model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Métriques
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred)
        }
        
        self.is_trained = True
        return metrics, X_test, y_test, y_pred, data.iloc[split_idx:]['Date']
    
    def forecast(self, production_data, days_ahead=30):
        """Prévoit la production pour les prochains jours."""
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prévisions.")
        
        # Préparer les features
        features_scaled = self.scaler.transform(production_data)
        forecast = self.model.predict(features_scaled)
        
        return forecast

class WaterInjectionOptimizer:
    """Modèle d'optimisation de l'injection d'eau."""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_injection_features(self, production_df):
        """Prépare les features pour l'optimisation de l'injection d'eau."""
        df = production_df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Calculer l'efficacité de l'injection (production d'huile / production d'eau)
        df['Oil_Water_Efficiency'] = df["Production journaliere d'huile bbl"] / (df["Production journaliere d'eau bbl"] + 1)
        
        # Features dérivées
        df['Watercut_Change'] = df["Teneur en eau (Watercut)"].diff()
        df['Production_Change'] = df["Production journaliere d'huile bbl"].diff()
        df['Water_Production_Ratio'] = df["Production journaliere d'eau bbl"] / df["Production journaliere d'huile bbl"]
        
        # Moyennes mobiles
        for col in ["Production journaliere d'huile bbl", "Production journaliere d'eau bbl", "Teneur en eau (Watercut)"]:
            df[f'{col}_MA_7'] = df[col].rolling(window=7).mean()
            df[f'{col}_MA_30'] = df[col].rolling(window=30).mean()
        
        df = df.dropna()
        return df
    
    def train(self, production_df, test_size=0.2):
        """Entraîne le modèle d'optimisation de l'injection d'eau."""
        # Préparer les données
        data = self.prepare_injection_features(production_df)
        
        # Features pour prédire l'efficacité optimale
        feature_columns = [
            "Production journaliere d'huile bbl",
            "Production journaliere d'eau bbl",
            "Teneur en eau (Watercut)",
            "Nombre des puits actifs",
            'Watercut_Change',
            'Production_Change',
            'Water_Production_Ratio'
        ]
        
        # Ajouter les moyennes mobiles
        ma_features = [col for col in data.columns if '_MA_' in col]
        feature_columns.extend(ma_features)
        
        X = data[feature_columns]
        y = data['Oil_Water_Efficiency']  # Target: efficacité de l'injection
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
        # Normaliser les features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entraîner le modèle
        self.model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Métriques
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred)
        }
        
        self.is_trained = True
        return metrics, X_test, y_test, y_pred
    
    def optimize_injection(self, current_conditions):
        """Recommande les paramètres d'injection optimaux."""
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des recommandations.")
        
        # Prédire l'efficacité avec les conditions actuelles
        features_scaled = self.scaler.transform(current_conditions)
        efficiency = self.model.predict(features_scaled)
        
        return efficiency

class ModelEvaluator:
    """Classe pour évaluer et comparer les modèles."""
    
    @staticmethod
    def evaluate_classification_model(y_true, y_pred, y_prob=None):
        """Évalue un modèle de classification."""
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0)
        }
        
        if y_prob is not None:
            from sklearn.metrics import roc_auc_score
            try:
                metrics['auc_roc'] = roc_auc_score(y_true, y_prob)
            except:
                metrics['auc_roc'] = 0.0
        
        return metrics
    
    @staticmethod
    def evaluate_regression_model(y_true, y_pred):
        """Évalue un modèle de régression."""
        metrics = {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }
        
        return metrics
    
    @staticmethod
    def cross_validate_model(model, X, y, cv=5, scoring='accuracy'):
        """Effectue une validation croisée."""
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
        return {
            'mean_score': scores.mean(),
            'std_score': scores.std(),
            'scores': scores
        }