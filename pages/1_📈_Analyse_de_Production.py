import streamlit as st
from src.data_loader import load_production_data
from src.plotting import plot_daily_production

st.title("📈 Analyse de la Production")

# Charger les données
df_prod = load_production_data()

if not df_prod.empty:
    st.header("Visualisation de la production d'huile")

    # Ajouter des filtres interactifs
    min_date = df_prod['Date'].min().date()
    max_date = df_prod['Date'].max().date()
    
    start_date, end_date = st.slider(
        "Sélectionnez une plage de dates",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="DD/MM/YYYY"
    )
    
    # Filtrer le dataframe en fonction de la sélection
    mask = (df_prod['Date'].dt.date >= start_date) & (df_prod['Date'].dt.date <= end_date)
    filtered_df = df_prod.loc[mask]

    # Afficher le graphique
    st.pyplot(plot_daily_production(filtered_df))

    # Afficher les données brutes
    st.header("Données de production brutes")
    st.dataframe(filtered_df)