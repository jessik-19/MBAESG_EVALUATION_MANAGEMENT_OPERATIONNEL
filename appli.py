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

# --- Filtres au niveau du siebar ---
if df is not None:
    st.sidebar.markdown("## 🎛️ Filtres dynamiques")
    marques = sorted(df['brand'].dropna().unique())
    types = sorted(df['car_body_type'].dropna().unique())

    filtre_marques = st.sidebar.multiselect("Marques", options=marques, default=marques)
    filtre_types = st.sidebar.multiselect("Types de carrosserie", options=types, default=types)

    df_filtré = df[(df['brand'].isin(filtre_marques)) & (df['car_body_type'].isin(filtre_types))]
else:
    df_filtré = pd.DataFrame()


# --- PAGE 1 : TABLEAU DE BORD ---
if page == "Tableau de bord":
    st.markdown("<h1>⚡ Tableau de bord des Véhicules Électriques</h1>", unsafe_allow_html=True)

    if not df_filtré.empty:
        # --- KPIs ---
        autonomie_moy = round(df_filtré['range_km'].mean(), 1)
        modele_eco_row = df_filtré[['model', 'efficiency_wh_per_km']].dropna().sort_values('efficiency_wh_per_km').head(1)
        modele_nom = modele_eco_row.iloc[0]['model']
        conso = modele_eco_row.iloc[0]['efficiency_wh_per_km']
        type_top = df_filtré['car_body_type'].mode()[0]
        nb_type = df_filtré['car_body_type'].value_counts().iloc[0]
        nb_modeles = df_filtré['model'].nunique()
        
