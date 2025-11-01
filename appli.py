import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px

# --- CONFIG PAGE ---
st.set_page_config(page_title="⚡ Tableau de bord VE", layout="wide")
# --- CSS DESIGN MODERNE ---
st.markdown("""
<style>
/* -------- PAGE GLOBALE -------- */
body {
   font-family: 'Segoe UI', sans-serif;
   background-color: #f8fafc;
   color: #222;
}
h1, h2, h3 {
   text-align: center;
   color: #0a4d8c;
   margin-bottom: 0.5rem;
}
/* -------- KPI CARDS -------- */
.kpi-container {
   display: flex;
   justify-content: space-between;
   flex-wrap: wrap;
   gap: 1rem;
   margin-top: 1rem;
}
.kpi-card {
   flex: 1;
   min-width: 180px;
   background-color: white;
   border-radius: 14px;
   box-shadow: 0 4px 12px rgba(0,0,0,0.08);
   padding: 1.2rem;
   text-align: center;
   transition: transform 0.2s ease-in-out;
}
.kpi-card:hover { transform: translateY(-5px); }
.kpi-title {
   font-size: 0.9rem;
   font-weight: 600;
   color: #666;
   margin-bottom: 0.4rem;
}
.kpi-value {
   font-size: 1.7rem;
   font-weight: bold;
}
.kpi-sub {
   font-size: 0.95rem;
   color: #777;
}
/* Couleurs */
.blue-top { border-top: 6px solid #0072c6; }
.green-top { border-top: 6px solid #2e8b57; }
.orange-top { border-top: 6px solid #f57c00; }
.purple-top { border-top: 6px solid #6a1b9a; }
/* -------- TABLE -------- */
.dataframe {
   margin-top: 1rem;
   border-radius: 10px !important;
   overflow: hidden;
   box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}
/* -------- SIDEBAR -------- */
[data-testid="stSidebar"] {
   background-color: #ffffff;
   border-right: 1px solid #e6e6e6;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
   color: #0a4d8c;
}
</style>
""", unsafe_allow_html=True)
# --- SIDEBAR ---
st.sidebar.title("📑 Navigation")
page = st.sidebar.radio("Choisissez une page :", ["Tableau de bord", "Visualisations"])
st.sidebar.markdown("---")
st.sidebar.title("📁 Import de données")
fichier = st.sidebar.file_uploader("Téléverser un CSV", type=["csv"])
# --- Connexion DB ---
con = duckdb.connect(database='vehicules_electriques.duckdb', read_only=False)
# --- Chargement ---
if fichier:
   df = pd.read_csv(fichier)
   con.execute("DROP TABLE IF EXISTS vehicules")
   con.execute("CREATE TABLE vehicules AS SELECT * FROM df")
   st.sidebar.success("✅ Données enregistrées dans DuckDB")
elif 'vehicules' in con.execute("SHOW TABLES").fetchdf()['name'].values:
   df = con.execute("SELECT * FROM vehicules").fetchdf()
else:
   df = None

if st.sidebar.button("🗑️ Réinitialiser les données"):
   con.execute("DROP TABLE IF EXISTS vehicules")
   st.sidebar.success("✅ Table supprimée — rechargez un fichier pour recommencer.")

# --- FILTRES ---
if df is not None:
   st.sidebar.markdown("## 🎛️ Filtres dynamiques")
   marques = sorted(df['brand'].dropna().unique())
   types = sorted(df['car_body_type'].dropna().unique())
   filtre_marques = st.sidebar.multiselect("Marques :", options=marques, default=marques)
   filtre_types = st.sidebar.multiselect("Types de carrosserie :", options=types, default=types)
   df_filtré = df[(df['brand'].isin(filtre_marques)) & (df['car_body_type'].isin(filtre_types))]
else:
   df_filtré = pd.DataFrame()


# --- PAGE TABLEAU DE BORD ---
if page == "Tableau de bord":
   st.markdown("<h1>⚡ Tableau de bord des Véhicules Électriques</h1>", unsafe_allow_html=True)
   st.markdown("<h3>\n Indicateurs clés</h3>", unsafe_allow_html=True)
   if not df_filtré.empty:
       con.execute("DROP VIEW IF EXISTS vehicules_filtres")
       con.register("vehicules_filtres", df_filtré)
       autonomie_moy = con.execute("""
           SELECT ROUND(AVG(range_km), 1) FROM vehicules_filtres WHERE range_km IS NOT NULL
       """).fetchone()[0]
       modele_eco = con.execute("""
           SELECT model, efficiency_wh_per_km
           FROM vehicules_filtres
           WHERE efficiency_wh_per_km IS NOT NULL
           ORDER BY efficiency_wh_per_km ASC
           LIMIT 1
       """).fetchdf()
       modele_nom = modele_eco.loc[0, 'model']
       conso = modele_eco.loc[0, 'efficiency_wh_per_km']
       type_dom = con.execute("""
           SELECT car_body_type, COUNT(*) AS nombre
           FROM vehicules_filtres
           WHERE car_body_type IS NOT NULL
           GROUP BY car_body_type
           ORDER BY nombre DESC
           LIMIT 1
       """).fetchdf()
       type_top = type_dom.loc[0, 'car_body_type']
       nb_type = type_dom.loc[0, 'nombre']
       nb_modeles = con.execute("""
           SELECT COUNT(DISTINCT model)
           FROM vehicules_filtres
           WHERE model IS NOT NULL
       """).fetchone()[0]
       # === KPI Layout ===

       st.markdown("""
<style>
.chart-card { background:#fff; border-radius:16px; padding:18px 18px 10px;
             box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
.card-head { display:flex; align-items:center; margin-bottom:12px; }
.chip { display:inline-block; padding:6px 12px; border-radius:999px;
       font-weight:600; font-size:.95rem; color:#0a4d8c; background:#eaf3ff;
       border:1px solid #cfe3ff; }
.blue-top   { border-top:6px solid #0072c6; }
.green-top  { border-top:6px solid #2e8b57; }
.orange-top { border-top:6px solid #f57c00; }
.purple-top { border-top:6px solid #6a1b9a; }
</style>
""", unsafe_allow_html=True)

       st.markdown("""
<div class='kpi-container'>
<div class='kpi-card blue-top'>
<div class='kpi-title'>⚡ Autonomie moyenne</div>
<div class='kpi-value'>{} km</div>
</div>
<div class='kpi-card green-top'>
<div class='kpi-title'>Modèle économe</div>
<div class='kpi-value'>{}</div>
<div class='kpi-sub'>{} Wh/km</div>
</div>
<div class='kpi-card orange-top'>
<div class='kpi-title'>🚘 Type dominant</div>
<div class='kpi-value'>{} ({})</div>
</div>
<div class='kpi-card purple-top'>
<div class='kpi-title'>📋 Modèles analysés</div>
<div class='kpi-value'>{}</div>
</div>
</div>
       """.format(autonomie_moy, modele_nom, conso, type_top, nb_type, nb_modeles),
       unsafe_allow_html=True)
       st.write("")
       st.write("")
       st.write("")
       st.markdown("### 🔍 Aperçu des données")
       st.write("")
       st.dataframe(df_filtré, use_container_width=True)
   else:
       st.warning("📂 Aucune donnée disponible.")

# --- PAGE VISUALISATIONS ---

# --- PAGE VISUALISATIONS ---

elif page == "Visualisations":

    if df is not None:

        # --- TITRE DE LA PAGE ---

        st.markdown("<h1>📊 Visualisations interactives</h1>", unsafe_allow_html=True)

        st.markdown("<p style='text-align:center; color:#555;'>Analyse visuelle des performances et caractéristiques des véhicules électriques</p>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # --- STYLES DES CARTES ET BADGES ---

        st.markdown("""
<style>

/* -------- PAGE GLOBALE -------- */

body {

  font-family: 'Segoe UI', sans-serif;

  background-color: #f8fafc;

  color: #222;

  margin: 0;

  padding: 0;

}

/* -------- TITRES -------- */

h1, h2, h3 {

  text-align: center;

  color: #0a4d8c;

  margin-bottom: 0.6rem;

  line-height: 1.3;

}

/* -------- KPI CONTAINER -------- */

.kpi-container {

  display: grid;

  grid-template-columns: repeat(4, 1fr);

  gap: 1rem;

  margin: 1rem auto;

  width: 90%;

  max-width: 1500px;

  box-sizing: border-box;

}

/* -------- KPI CARD -------- */

.kpi-card {

  background-color: white;

  border-radius: 14px;

  box-shadow: 0 4px 12px rgba(0,0,0,0.08);

  padding: 1rem;

  text-align: center;

  transition: transform 0.2s ease-in-out;

  display: flex;

  flex-direction: column;

  justify-content: center;

  height: 20px;

}

.kpi-card:hover {

  transform: translateY(-5px);

}

.kpi-title {

  font-size: 0.9rem;

  font-weight: 300;

  color: #666;

  margin-bottom: 0.3rem;

  word-wrap: break-word;

  white-space: normal;

}

.kpi-value {

  font-size: 1.6rem;

  font-weight: bold;

  color: #111;

  line-height: 1.1;

}

.kpi-sub {

  font-size: 0.9rem;

  color: #777;

  margin-top: 0.3rem;

}

/* -------- COULEURS -------- */

.blue-top   { border-top: 5px solid #0072c6; }

.green-top  { border-top: 5px solid #2e8b57; }

.orange-top { border-top: 5px solid #f57c00; }

.purple-top { border-top: 5px solid #6a1b9a; }

/* -------- TABLE -------- */

.dataframe {

  margin-top: 1rem;

  border-radius: 10px !important;

  overflow: hidden;

  box-shadow: 0 3px 10px rgba(0,0,0,0.05);

}

/* -------- SIDEBAR -------- */

[data-testid="stSidebar"] {

  background-color: #ffffff;

  border-right: 1px solid #e6e6e6;

}

/* -------- RESPONSIVE -------- */

/* 2 cartes par ligne sur écran moyen */

@media (max-width: 1100px) {

  .kpi-container {

    grid-template-columns: repeat(2, 1fr);

  }

}

/* 1 carte par ligne sur petit écran */

@media (max-width: 700px) {

  .kpi-container {

    grid-template-columns: 1fr;

  }

  .kpi-card {

    height: auto;

    padding: 1rem;

  }

  .kpi-value {

    font-size: 1.4rem;

  }

  h1 {

    font-size: 1.6rem;

  }

}
</style>

""", unsafe_allow_html=True)
 


 

        # --- 1️⃣ AUTONOMIE MOYENNE PAR SEGMENT ---

        top_segments = con.execute("""

            SELECT segment, ROUND(AVG(range_km), 1) AS autonomie_moyenne

            FROM vehicules

            WHERE segment IS NOT NULL AND range_km IS NOT NULL

            GROUP BY segment

            ORDER BY autonomie_moyenne DESC

        """).fetchdf()

        # nettoyage des valeurs nulles

        top_segments = top_segments.dropna(subset=["segment", "autonomie_moyenne"])

        top_segments["autonomie_moyenne"] = top_segments["autonomie_moyenne"].fillna(0)

        top3 = top_segments.head(3)["segment"].tolist()

        top_segments["couleur"] = top_segments["segment"].apply(lambda x: "#F5B041" if x in top3 else "#AED6F1")

        fig = px.bar(

            top_segments,

            x="segment",

            y="autonomie_moyenne",

            color="couleur",

            color_discrete_map="identity",

            text="autonomie_moyenne"

        )

        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")

        fig.update_layout(title=None, showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

        # --- 2️⃣ MODÈLES LES PLUS ÉCONOMES ---

        df_eco = con.execute("""

            SELECT model, efficiency_wh_per_km

            FROM vehicules

            WHERE model IS NOT NULL AND efficiency_wh_per_km IS NOT NULL

            ORDER BY efficiency_wh_per_km ASC

            LIMIT 6

        """).fetchdf()

        df_eco = df_eco.dropna(subset=["model", "efficiency_wh_per_km"])

        df_eco["efficiency_wh_per_km"] = df_eco["efficiency_wh_per_km"].fillna(0)

        couleurs_personnalisees = ["#0072C6", "#0072C6", "#0098D1", "#00B8A9", "#63C132", "#A3E635"]

        df_eco['couleur'] = couleurs_personnalisees

        fig2 = px.bar(

            df_eco,

            x='efficiency_wh_per_km',

            y='model',

            orientation='h',

            color='couleur',

            color_discrete_map='identity',

            labels={'efficiency_wh_per_km': 'Wh/km', 'model': 'Modèle'}

        )

        fig2.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')), texttemplate="%{x:.0f}", textposition="outside")

        fig2.update_layout(title=None, showlegend=False, plot_bgcolor="rgba(0,0,0,0)")

        # --- LIGNE 1 : DEUX GRAPHIQUES ---

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("<div class='chart-card blue-top'>"

                        "<div class='card-head'><span class='chip'>⚡ Autonomie moyenne par segment</span></div>",

                        unsafe_allow_html=True)

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col2:

            st.markdown("<div class='chart-card green-top'>"

                        "<div class='card-head'><span class='chip'>🔋 Modèles les plus économes (Wh/km)</span></div>",

                        unsafe_allow_html=True)

            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # --- 3️⃣ RÉPARTITION DES TYPES DE CARROSSERIE ---

        df_carro = con.execute("""

            SELECT car_body_type AS Type, COUNT(*) AS Nombre

            FROM vehicules

            WHERE car_body_type IS NOT NULL

            GROUP BY car_body_type

            ORDER BY Nombre DESC

        """).fetchdf()

        df_carro = df_carro.dropna(subset=["Type", "Nombre"])

        df_carro["Nombre"] = df_carro["Nombre"].fillna(0)

        fig3 = px.pie(

            df_carro,

            values='Nombre',

            names='Type',

            hole=0.45,

            color_discrete_sequence=px.colors.qualitative.Pastel

        )

        fig3.update_layout(title=None, showlegend=True, title_x=0.5)

        # --- 4️⃣ NUAGE DE POINTS MARQUES ---

        df_scatter = con.execute("""

            SELECT brand, COUNT(DISTINCT model) AS nb_modeles, ROUND(AVG(range_km), 1) AS autonomie_moy

            FROM vehicules

            WHERE brand IS NOT NULL AND range_km IS NOT NULL

            GROUP BY brand

        """).fetchdf()

        df_scatter = df_scatter.dropna(subset=["brand", "nb_modeles"])

        df_scatter["nb_modeles"] = df_scatter["nb_modeles"].fillna(0)

        df_scatter["autonomie_moy"] = df_scatter["autonomie_moy"].fillna(0)

        top_3 = df_scatter.nlargest(3, 'nb_modeles')['brand'].tolist()

        flop_3 = df_scatter.nsmallest(3, 'nb_modeles')['brand'].tolist()

        def couleur_marque(brand):

            if brand in top_3:

                return '#F39C12'

            elif brand in flop_3:

                return '#E74C3C'

            else:

                return '#85C1E9'

        df_scatter['couleur'] = df_scatter['brand'].apply(couleur_marque)

        fig4 = px.scatter(

            df_scatter,

            x='brand',

            y='nb_modeles',

            size='autonomie_moy',

            color='couleur',

            color_discrete_map='identity',

            labels={'brand': 'Marque', 'nb_modeles': 'Nb modèles'}

        )

        fig4.update_traces(marker=dict(opacity=0.85, line=dict(width=1, color='DarkSlateGrey')))

        fig4.update_layout(title=None, showlegend=False, xaxis_tickangle=-45, plot_bgcolor="rgba(0,0,0,0)")

        # --- LIGNE 2 : DEUX AUTRES GRAPHIQUES ---

        st.write("\n\n\n")

        col3, col4 = st.columns(2)

        with col3:

            st.markdown("<div class='chart-card orange-top'>"

                        "<div class='card-head'><span class='chip'>🚘 Répartition des types de carrosserie</span></div>",

                        unsafe_allow_html=True)

            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col4:

            st.markdown("<div class='chart-card purple-top'>"

                        "<div class='card-head'><span class='chip'>📍 Marques : nombre de modèles & autonomie</span></div>",

                        unsafe_allow_html=True)

            st.plotly_chart(fig4, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

    else:

        st.warning("📂 Aucune donnée à afficher pour les visualisations.")

