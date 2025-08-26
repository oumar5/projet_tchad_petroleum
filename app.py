import streamlit as st

st.set_page_config(
    page_title="TPC - Optimisation & Digitalisation",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Projet de Digitalisation pour Tchad Petroleum Company")

st.header("Bienvenue sur la plateforme d'analyse et de modélisation prédictive.")

st.markdown("""
Cette application a pour but de centraliser les analyses de données de production et de maintenance,
et d'intégrer des modèles prédictifs pour optimiser les processus internes.

**👈 Utilisez le menu de navigation sur la gauche pour explorer les différentes sections :**

- **Analyse de Production :** Visualisez les tendances de production.
- **Analyse des Pannes :** Explorez les statistiques sur les pannes de pompes.
- **Modélisation Prédictive :** Accédez aux modèles de prévision.
""")