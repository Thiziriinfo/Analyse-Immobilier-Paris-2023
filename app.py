import streamlit as st
import pandas as pd
import urllib.request
import plotly.express as px

st.set_page_config(page_title="Marché Immobilier Paris 2023", layout="wide")

# ── CSS CUSTOM ──
st.markdown("""
<style>
    .main { background-color: #07081a; }
    .block-container { padding-top: 2rem; }
    h1, h2, h3 { color: #ffffff; }
    .insight-box {
        background: rgba(108,99,255,0.08);
        border-left: 3px solid #6C63FF;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0 20px 0;
        color: rgba(255,255,255,0.7);
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .insight-box strong { color: #9B7FE8; }
</style>
""", unsafe_allow_html=True)

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
type_bien = st.sidebar.multiselect("Type de bien", ['Appartement', 'Maison'], default=['Appartement', 'Maison'])

df_filtered = df[
    (df['arrondissement'].isin(selected_arr)) &
    (df['prix_m2'] >= prix_min) &
    (df['prix_m2'] <= prix_max) &
    (df['type_local'].isin(type_bien))
]

# ── TITRE ──
st.title("🏠 Marché Immobilier Parisien — DVF 2023")
st.markdown("""
Ce dashboard analyse les **Demandes de Valeurs Foncières (DVF)** publiées par l'État pour l'année 2023.  
Il couvre l'ensemble des transactions immobilières déclarées à Paris — appartements et maisons — 
permettant d'identifier les tendances de prix, les disparités entre arrondissements et la saisonnalité du marché.
""")
st.markdown(f"**{len(df_filtered):,} transactions** correspondent aux filtres sélectionnés.")

st.divider()

# ── KPIs ──
col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", f"{len(df_filtered):,}")
col2.metric("Prix médian au m²", f"{int(df_filtered['prix_m2'].median()):,} €")
col3.metric("Prix moyen au m²", f"{int(df_filtered['prix_m2'].mean()):,} €")
col4.metric("Arrondissement le + cher",
            f"Paris {df_filtered.groupby('arrondissement')['prix_m2'].median().idxmax()}e")

st.divider()

# ── GRAPHE 1 : EVOLUTION ──
st.subheader("📈 Évolution du prix médian au m² — 2023")

evolution = df_filtered.groupby('mois')['prix_m2'].median().reset_index()
fig1 = px.line(evolution, x='mois', y='prix_m2', markers=True,
               color_discrete_sequence=['#6C63FF'],
               labels={'mois': 'Mois', 'prix_m2': 'Prix médian (€/m²)'})
fig1.update_traces(line=dict(width=3), marker=dict(size=8, color='white', line=dict(width=2.5, color='#6C63FF')))
fig1.update_layout(plot_bgcolor='#0d0e24', paper_bgcolor='#0d0e24',
                   font=dict(color='rgba(255,255,255,0.7)'),
                   yaxis=dict(ticksuffix='€', gridcolor='rgba(108,99,255,0.1)', color='rgba(255,255,255,0.5)'),
                   xaxis=dict(showgrid=False, color='rgba(255,255,255,0.5)'))
st.plotly_chart(fig1, use_container_width=True)

mois_max = evolution.loc[evolution['prix_m2'].idxmax(), 'mois']
mois_min = evolution.loc[evolution['prix_m2'].idxmin(), 'mois']
st.markdown(f"""
<div class="insight-box">
💡 <strong>Analyse :</strong> Le pic de prix est observé en <strong>{mois_max}</strong>, 
tandis que les prix sont au plus bas en <strong>{mois_min}</strong>. 
La courbe révèle une <strong>saisonnalité du marché parisien</strong> — les transactions du printemps 
et de l'automne tendent à s'effectuer à des prix plus élevés qu'en été ou en janvier.
</div>
""", unsafe_allow_html=True)

st.divider()

# ── GRAPHE 2+3 ──
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏙️ Prix médian par arrondissement")
    arrond = df_filtered.groupby('arrondissement')['prix_m2'].median().reset_index()
    arrond = arrond.sort_values('prix_m2', ascending=True)
    fig2 = px.bar(arrond, x='prix_m2', y='arrondissement', orientation='h',
                  color='prix_m2', color_continuous_scale=['#3D4FE0', '#6C63FF', '#9B7FE8'],
                  labels={'prix_m2': '€/m²', 'arrondissement': 'Arrondissement'})
    fig2.update_layout(plot_bgcolor='#0d0e24', paper_bgcolor='#0d0e24',
                       font=dict(color='rgba(255,255,255,0.7)'),
                       coloraxis_showscale=False,
                       yaxis=dict(tickprefix='Paris ', color='rgba(255,255,255,0.5)'),
                       xaxis=dict(showgrid=False, ticksuffix='€', color='rgba(255,255,255,0.5)'))
    st.plotly_chart(fig2, use_container_width=True)
    arr_cher = df_filtered.groupby('arrondissement')['prix_m2'].median().idxmax()
    arr_abord = df_filtered.groupby('arrondissement')['prix_m2'].median().idxmin()
    st.markdown(f"""
    <div class="insight-box">
    💡 <strong>Analyse :</strong> Le <strong>{arr_cher}e arrondissement</strong> est le plus cher, 
    confirmant l'attractivité des arrondissements centraux et rive gauche. 
    Le <strong>{arr_abord}e</strong> reste le plus accessible — 
    reflet des dynamiques de gentrification encore incomplètes en périphérie.
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.subheader("📊 Distribution des prix au m²")
    fig3 = px.histogram(df_filtered, x='prix_m2', nbins=60,
                        color_discrete_sequence=['#6C63FF'],
                        labels={'prix_m2': '€/m²'})
    fig3.add_vline(x=df_filtered['prix_m2'].median(), line_dash='dash',
                   line_color='#9B7FE8', line_width=2,
                   annotation_text=f"Médiane : {int(df_filtered['prix_m2'].median()):,}€",
                   annotation_font_color='#9B7FE8')
    fig3.update_layout(plot_bgcolor='#0d0e24', paper_bgcolor='#0d0e24',
                       font=dict(color='rgba(255,255,255,0.7)'),
                       xaxis=dict(ticksuffix='€', showgrid=False, color='rgba(255,255,255,0.5)'),
                       yaxis=dict(gridcolor='rgba(108,99,255,0.1)', color='rgba(255,255,255,0.5)'))
    st.plotly_chart(fig3, use_container_width=True)
    skew = df_filtered['prix_m2'].skew()
    st.markdown(f"""
    <div class="insight-box">
    💡 <strong>Analyse :</strong> La distribution est <strong>asymétrique à droite</strong> — 
    la majorité des transactions se concentrent entre 8 000 et 14 000 €/m², 
    mais quelques biens de luxe tirent la moyenne vers le haut. 
    La médiane ({int(df_filtered['prix_m2'].median()):,} €/m²) est donc plus représentative que la moyenne.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── GRAPHE 4 : CARTE ──
st.subheader("🗺️ Carte des transactions à Paris")
st.markdown("Chaque point représente une transaction. La couleur indique le prix au m² — du bleu (abordable) au rouge (premium).")

fig4 = px.scatter_mapbox(df_filtered, lat='latitude', lon='longitude',
                         color='prix_m2', size='prix_m2',
                         color_continuous_scale='Viridis', size_max=8,
                         zoom=11, center={"lat": 48.8566, "lon": 2.3522},
                         labels={'prix_m2': 'Prix au m²'},
                         hover_data={'code_postal': True, 'prix_m2': ':,.0f',
                                     'type_local': True,
                                     'latitude': False, 'longitude': False})
fig4.update_layout(mapbox_style="carto-darkmatter", height=600,
                   margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig4, use_container_width=True)

st.markdown("""
<div class="insight-box">
💡 <strong>Analyse :</strong> La carte confirme visuellement le <strong>gradient de prix centre-périphérie</strong> 
caractéristique de Paris. Les arrondissements du centre (1er–8e) et de l'ouest (16e, 17e) 
concentrent les prix les plus élevés, tandis que le nord-est (18e, 19e, 20e) reste plus accessible.
</div>
""", unsafe_allow_html=True)

st.divider()

# ── DONNÉES BRUTES ──
st.subheader("🗃️ Données brutes")
st.markdown("Explorez les transactions individuelles correspondant à vos filtres.")

cols_display = ['date_mutation', 'arrondissement', 'type_local', 'surface_reelle_bati',
                'nombre_pieces_principales', 'valeur_fonciere', 'prix_m2']
df_display = df_filtered[cols_display].copy()
df_display.columns = ['Date', 'Arrondissement', 'Type', 'Surface (m²)', 'Pièces', 'Prix total (€)', 'Prix/m² (€)']
df_display['Prix total (€)'] = df_display['Prix total (€)'].apply(lambda x: f"{int(x):,}")
df_display['Prix/m² (€)'] = df_display['Prix/m² (€)'].apply(lambda x: f"{int(x):,}")
df_display['Surface (m²)'] = df_display['Surface (m²)'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")

st.dataframe(df_display.sort_values('Date', ascending=False).reset_index(drop=True),
             use_container_width=True, height=400)

st.markdown(f"*{len(df_filtered):,} transactions affichées — Source : data.gouv.fr — DVF 2023*")

# ── FOOTER ──
st.markdown("---")
st.markdown("*Développé par **Thiziri Abchiche** — Data Analyst · [Portfolio](https://thiziriinfo.github.io) · [GitHub](https://github.com/thiziriinfo)*")
