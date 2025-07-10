import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px

# --- Configuration de la page ---
st.set_page_config(page_title="VE Dashboard", page_icon="⚡", layout="wide")

# --- CSS pour la mise en forme des kpis et sidebar  ---
st.markdown("""
<style>
h1, h2, h3 {
    text-align: center;
    color: #0a4d8c;
}
.card {
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("📑 Navigation")
page = st.sidebar.radio("Choisissez une page", ["Tableau de bord", "Visualisations"])

# --- Import CSV ---
st.sidebar.title("📁 Import de données")
fichier = st.sidebar.file_uploader("Téléverser un CSV", type=["csv"])

# --- Connexion à DuckDB ---
con = duckdb.connect(database='vehicules_electriques.duckdb', read_only=False)

# --- Chargement des données ---
if fichier:
    df = pd.read_csv(fichier)
    con.execute("DROP TABLE IF EXISTS vehicules")
    con.execute("CREATE TABLE vehicules AS SELECT * FROM df")
    st.sidebar.success("✅ Données enregistrées dans DuckDB")
elif 'vehicules' in con.execute("SHOW TABLES").fetchdf()['name'].values:
    df = con.execute("SELECT * FROM vehicules").fetchdf()
else:
    df = None
