import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Chemin vers le dossier des données
DATA_PATH = './data/'

@st.cache_data
def load_production_data():
    """Charge et nettoie les données de production."""
    column_names = [
        "Date", "Nombre total des puits", "Nombre des puits actifs",
        "Production journaliere d'huile bbl", "Production journaliere d'eau bbl",
        "Teneur en eau (Watercut)", "Water Oil Ratio",
        "Production journaliere d'eau en kilo baril jour"
    ]
    try:
        df = pd.read_excel(
            DATA_PATH + 'Données de production Rev.xlsx',
            sheet_name='Prod YOM BlocsFaillés X, Y et Z',
            skiprows=4,
            header=None,
            names=column_names
        )
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        st.error("Fichier de production non trouvé dans le dossier `data/`.")
        return pd.DataFrame()

@st.cache_data
def load_pump_failures_data():
    """Charge les données sur les pannes de pompes."""
    try:
        df = pd.read_excel(
            DATA_PATH + "Données de production Rev.xlsx",
            sheet_name="Historiq Pannes pompes"
        )
        df["Date de notification d'endomagement de la pompe"] = pd.to_datetime(df["Date de notification d'endomagement de la pompe"])
        return df
    except FileNotFoundError:
        st.error("Fichier des pannes de pompes non trouvé dans le dossier `data/`.")
        return pd.DataFrame()

@st.cache_data
def load_interventions_data():
    """Charge les données sur les interventions."""
    try:
        df = pd.read_excel(
            DATA_PATH + "Données de production Rev.xlsx",
            sheet_name="Interventions"
        )
        # Convertir les colonnes de date si elles existent
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'Date' in col]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except Exception as e:
        st.warning(f"Impossible de charger les données d'interventions: {e}")
        return pd.DataFrame()

@st.cache_data
def load_well_data():
    """Charge les données des puits si disponibles."""
    try:
        df = pd.read_excel(
            DATA_PATH + "Données de production Rev.xlsx",
            sheet_name="Puits"
        )
        return df
    except Exception as e:
        st.warning(f"Impossible de charger les données des puits: {e}")
        return pd.DataFrame()

def split_data_for_validation(df, validation_years=2):
    """Divise les données en utilisant les N dernières années pour la validation."""
    if df.empty:
        return df, pd.DataFrame()
    
    # Assurer que la colonne Date est en datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Calculer la date de coupure
        max_date = df['Date'].max()
        cutoff_date = max_date - pd.DateOffset(years=validation_years)
        
        # Diviser les données
        train_data = df[df['Date'] <= cutoff_date].copy()
        validation_data = df[df['Date'] > cutoff_date].copy()
        
        return train_data, validation_data
    else:
        # Si pas de colonne Date, diviser par index
        split_idx = int(len(df) * (1 - validation_years/10))  # Approximation
        return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()

def get_data_summary(df):
    """Retourne un résumé des données."""
    if df.empty:
        return {}
    
    summary = {
        'total_records': len(df),
        'date_range': None,
        'missing_values': df.isnull().sum().to_dict(),
        'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
        'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
    }
    
    if 'Date' in df.columns:
        summary['date_range'] = {
            'start': df['Date'].min(),
            'end': df['Date'].max(),
            'days': (df['Date'].max() - df['Date'].min()).days
        }
    
    return summary

def prepare_data_for_modeling(production_df, failures_df=None, interventions_df=None):
    """Prépare les données pour la modélisation prédictive."""
    # Nettoyer les données de production
    prod_clean = production_df.copy()
    prod_clean['Date'] = pd.to_datetime(prod_clean['Date'])
    prod_clean = prod_clean.sort_values('Date')
    
    # Supprimer les valeurs aberrantes (optionnel)
    numeric_cols = prod_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != 'Date':
            Q1 = prod_clean[col].quantile(0.25)
            Q3 = prod_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            prod_clean[col] = prod_clean[col].clip(lower=lower_bound, upper=upper_bound)
    
    # Interpoler les valeurs manquantes
    prod_clean = prod_clean.interpolate(method='linear')
    
    result = {'production': prod_clean}
    
    if failures_df is not None and not failures_df.empty:
        failures_clean = failures_df.copy()
        failures_clean["Date de notification d'endomagement de la pompe"] = pd.to_datetime(
            failures_clean["Date de notification d'endomagement de la pompe"]
        )
        result['failures'] = failures_clean
    
    if interventions_df is not None and not interventions_df.empty:
        result['interventions'] = interventions_df.copy()
    
    return result

def calculate_production_kpis(df):
    """Calcule les KPIs de production."""
    if df.empty:
        return {}
    
    kpis = {}
    
    if "Production journaliere d'huile bbl" in df.columns:
        oil_prod = df["Production journaliere d'huile bbl"]
        kpis['oil_production'] = {
            'total': oil_prod.sum(),
            'average_daily': oil_prod.mean(),
            'max_daily': oil_prod.max(),
            'min_daily': oil_prod.min(),
            'std_daily': oil_prod.std()
        }
    
    if "Production journaliere d'eau bbl" in df.columns:
        water_prod = df["Production journaliere d'eau bbl"]
        kpis['water_production'] = {
            'total': water_prod.sum(),
            'average_daily': water_prod.mean(),
            'max_daily': water_prod.max(),
            'min_daily': water_prod.min()
        }
    
    if "Teneur en eau (Watercut)" in df.columns:
        watercut = df["Teneur en eau (Watercut)"]
        kpis['watercut'] = {
            'average': watercut.mean(),
            'max': watercut.max(),
            'min': watercut.min(),
            'current': watercut.iloc[-1] if len(watercut) > 0 else None
        }
    
    if "Nombre des puits actifs" in df.columns:
        active_wells = df["Nombre des puits actifs"]
        kpis['active_wells'] = {
            'average': active_wells.mean(),
            'max': active_wells.max(),
            'min': active_wells.min(),
            'current': active_wells.iloc[-1] if len(active_wells) > 0 else None
        }
    
    return kpis

def calculate_failure_kpis(df):
    """Calcule les KPIs de pannes."""
    if df.empty:
        return {}
    
    kpis = {
        'total_failures': len(df),
        'failures_by_block': df['Bloc Faillé'].value_counts().to_dict() if 'Bloc Faillé' in df.columns else {},
        'failures_by_year': df["Date de notification d'endomagement de la pompe"].dt.year.value_counts().to_dict() if "Date de notification d'endomagement de la pompe" in df.columns else {}
    }
    
    # Calculer MTBF (Mean Time Between Failures) si possible
    if "Date de notification d'endomagement de la pompe" in df.columns and len(df) > 1:
        dates = df["Date de notification d'endomagement de la pompe"].sort_values()
        time_between_failures = dates.diff().dt.days.dropna()
        kpis['mtbf_days'] = time_between_failures.mean()
        kpis['mtbf_std'] = time_between_failures.std()
    
    return kpis