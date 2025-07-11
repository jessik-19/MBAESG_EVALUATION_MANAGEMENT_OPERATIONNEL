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
        con.execute("DROP VIEW IF EXISTS vehicules_filtres")
        con.register("vehicules_filtres", df_filtré)

        # --- KPI 1 : Autonomie moyenne ---
        autonomie_moy = con.execute("""
            SELECT ROUND(AVG(range_km), 1) AS autonomie_moyenne
            FROM vehicules_filtres
            WHERE range_km IS NOT NULL
        """).fetchone()[0]

        # --- KPI 2 : Modèle le plus économe ---
        modele_eco_row = con.execute("""
            SELECT model, efficiency_wh_per_km
            FROM vehicules_filtres
           WHERE efficiency_wh_per_km IS NOT NULL
            ORDER BY efficiency_wh_per_km ASC
            LIMIT 1
        """).fetchdf()

        modele_nom = modele_eco_row.loc[0, 'model']
        conso = modele_eco_row.loc[0, 'efficiency_wh_per_km']

        # --- KPI 3 : Type dominant de carrosserie ---
        carro_row = con.execute("""
            SELECT car_body_type, COUNT(*) AS nombre
            FROM vehicules_filtres
            WHERE car_body_type IS NOT NULL
            GROUP BY car_body_type
            ORDER BY nombre DESC
            LIMIT 1
        """).fetchdf()

        type_top = carro_row.loc[0, 'car_body_type']
        nb_type = carro_row.loc[0, 'nombre']

        # --- KPI 4 : Nombre de modèles uniques ---
        nb_modeles = con.execute("""
            SELECT COUNT(DISTINCT model)
            FROM vehicules_filtres
            WHERE model IS NOT NULL
        """).fetchone()[0]


        st.subheader("📌 Indicateurs clés")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.markdown(f"""
                <div class='card' style='background-color:#e0f2ff;'>
                    <h4>⚡ Autonomie moyenne</h4>
                    <h2 style='color:#0072c6;'>{autonomie_moy} km</h2>
                </div>
            """, unsafe_allow_html=True)

        with kpi2:
            st.markdown(f"""
                <div class='card' style='background-color:#e8fff2;'>
                    <h4> Modèle économe</h4>
                    <p><strong>{modele_nom}</strong></p>
                    <h3 style='color:#2e8b57;'>{conso} Wh/km</h3>
                </div>
            """, unsafe_allow_html=True)

        with kpi3:
            st.markdown(f"""
                <div class='card' style='background-color:#fff3e6;'>
                    <h4>🚘 Type voiture dominant</h4>
                    <h2 style='color:#f57c00;'>{type_top} ({nb_type})</h2>
                </div>
            """, unsafe_allow_html=True)

        with kpi4:
            st.markdown(f"""
                <div class='card' style='background-color:#f0e6ff;'>
                    <h4>📋 Modèles analysés</h4>
                    <h2 style='color:#6a1b9a;'>{nb_modeles}</h2>
                </div>
            """, unsafe_allow_html=True)


        st.subheader("📄 Aperçu des données")
        st.dataframe(df_filtré, use_container_width=True)

    else:
        st.warning("📂 Aucune donnée disponible.")



        
