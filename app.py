

import streamlit as st
import pandas as pd
import urllib.request
import plotly.express as px

st.set_page_config(page_title="Marché Immobilier Paris 2023", layout="wide")

# ── CHARGEMENT ET NETTOYAGE ──
@st.cache_data
def load_data():
    url = "https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/75.csv.gz"
    urllib.request.urlretrieve(url, "dvf_paris_2023.csv.gz")
    df = pd.read_csv("dvf_paris_2023.csv.gz", compression="gzip", low_memory=False)
    
    colonnes_utiles = ['date_mutation','nature_mutation','valeur_fonciere','code_postal',
                       'nom_commune','type_local','surface_reelle_bati',
                       'nombre_pieces_principales','longitude','latitude']
    df = df[colonnes_utiles].copy()
    df = df[df['type_local'].isin(['Appartement', 'Maison'])]
    df = df.dropna(subset=['valeur_fonciere', 'longitude', 'latitude', 'code_postal'])
    df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
    df = df[(df['prix_m2'] >= 1000) & (df['prix_m2'] <= 50000)]
    df['date_mutation'] = pd.to_datetime(df['date_mutation'])
    df['mois'] = df['date_mutation'].dt.to_period('M').astype(str)
    df['arrondissement'] = df['code_postal'].astype(float).astype(int).astype(str).str[-2:].astype(int)
    return df

df = load_data()

# ── SIDEBAR ──
st.sidebar.title("Filtres")
arr_list = sorted(df['arrondissement'].unique())
selected_arr = st.sidebar.multiselect("Arrondissement", arr_list, default=arr_list)
prix_min, prix_max = st.sidebar.slider("Prix au m² (€)", 1000, 50000, (1000, 50000), step=500)

df_filtered = df[
    (df['arrondissement'].isin(selected_arr)) &
    (df['prix_m2'] >= prix_min) &
    (df['prix_m2'] <= prix_max)
]

# ── TITRE ──
st.title("🏠 Marché Immobilier Parisien — DVF 2023")
st.markdown("Analyse de **{:,}** transactions immobilières à Paris".format(len(df_filtered)))

# ── KPIs ──
col1, col2, col3 = st.columns(3)
col1.metric("Transactions", f"{len(df_filtered):,}")
col2.metric("Prix médian au m²", f"{int(df_filtered['prix_m2'].median()):,}€")
col3.metric("Arrondissement le + cher", 
            f"Paris {df_filtered.groupby('arrondissement')['prix_m2'].median().idxmax()}")

st.divider()

# ── GRAPHE 1 : EVOLUTION ──
st.subheader("Évolution du prix médian au m²")
evolution = df_filtered.groupby('mois')['prix_m2'].median().reset_index()
fig1 = px.line(evolution, x='mois', y='prix_m2', markers=True,
               color_discrete_sequence=['#E84A2F'],
               labels={'mois': 'Mois', 'prix_m2': 'Prix médian (€/m²)'})
fig1.update_traces(line=dict(width=3), marker=dict(size=8, color='white', line=dict(width=2.5, color='#E84A2F')))
fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                   yaxis=dict(ticksuffix='€', gridcolor='#EEEEEE'),
                   xaxis=dict(showgrid=False))
st.plotly_chart(fig1, use_container_width=True)

# ── GRAPHE 2+3 : ARRONDISSEMENT + DISTRIBUTION ──
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Prix par arrondissement")
    arrond = df_filtered.groupby('arrondissement')['prix_m2'].median().reset_index()
    arrond = arrond.sort_values('prix_m2', ascending=True)
    fig2 = px.bar(arrond, x='prix_m2', y='arrondissement', orientation='h',
                  color='prix_m2', color_continuous_scale='YlOrRd',
                  labels={'prix_m2': '€/m²', 'arrondissement': 'Arrondissement'})
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       coloraxis_showscale=False,
                       yaxis=dict(tickprefix='Paris '),
                       xaxis=dict(showgrid=False))
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    st.subheader("Distribution des prix au m²")
    fig3 = px.histogram(df_filtered, x='prix_m2', nbins=60,
                        color_discrete_sequence=['#E84A2F'],
                        labels={'prix_m2': '€/m²'})
    fig3.add_vline(x=df_filtered['prix_m2'].median(), line_dash='dash',
                   line_color='#1F3864', line_width=2,
                   annotation_text=f"Médiane : {int(df_filtered['prix_m2'].median()):,}€",
                   annotation_font_color='#1F3864')
    fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       xaxis=dict(ticksuffix='€', showgrid=False),
                       yaxis=dict(gridcolor='#EEEEEE'))
    st.plotly_chart(fig3, use_container_width=True)

# ── GRAPHE 4 : CARTE ──
st.subheader("Carte des transactions")
fig4 = px.scatter_mapbox(df_filtered, lat='latitude', lon='longitude',
                         color='prix_m2', size='prix_m2',
                         color_continuous_scale='YlOrRd', size_max=8,
                         zoom=11, center={"lat": 48.8566, "lon": 2.3522},
                         labels={'prix_m2': 'Prix au m²'},
                         hover_data={'code_postal': True, 'prix_m2': ':,.0f',
                                     'latitude': False, 'longitude': False})
fig4.update_layout(mapbox_style="carto-positron", height=600,
                   margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig4, use_container_width=True)

# ── FOOTER ──
st.markdown("---")
st.markdown("*Source : data.gouv.fr — Demandes de Valeurs Foncières 2023*")
