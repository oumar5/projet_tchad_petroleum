import streamlit as st
from src.data_loader import load_pump_failures_data
from src.plotting import plot_failures_by_block

st.title("🔧 Analyse des Pannes de Pompes")

df_failures = load_pump_failures_data()

if not df_failures.empty:
    st.header("Répartition des pannes par bloc")
    st.pyplot(plot_failures_by_block(df_failures))
    
    st.header("Historique des pannes")
    st.dataframe(df_failures)