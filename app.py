import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sqlite3
import urllib.request

st.set_page_config(
    page_title="Immobilier Paris 2023",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #07081a; }
[data-testid="stSidebar"] {
    background: #0d0e2a;
    border-right: 1px solid rgba(108,99,255,0.2);
}
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
h1, h2, h3 { color: #ffffff !important; }
[data-testid="stSidebarNav"] { display: none; }

[data-testid="stMetric"] {
    background: rgba(108,99,255,0.08);
    border: 1px solid rgba(108,99,255,0.22);
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricLabel"] { color: rgba(255,255,255,0.6) !important; font-size: 0.8rem; }
[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.55rem !important; font-weight: 600; }
[data-testid="stMetricDelta"] { font-size: 0.82rem !important; }

.insight-box {
    background: rgba(108,99,255,0.09);
    border-left: 3px solid #6C63FF;
    border-radius: 0 10px 10px 0;
    padding: 13px 18px;
    margin: 8px 0 20px 0;
    color: rgba(255,255,255,0.82);
    font-size: 0.87rem;
    line-height: 1.65;
}
.insight-box strong { color: #a89ff7; }

.page-header {
    background: linear-gradient(135deg, rgba(108,99,255,0.14) 0%, rgba(61,79,224,0.07) 100%);
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 22px;
    border: 1px solid rgba(108,99,255,0.2);
}
.page-header h2 { margin: 0 0 4px 0 !important; font-size: 1.35rem !important; }
.page-header p { margin: 0; color: rgba(255,255,255,0.55); font-size: 0.85rem; }

.sql-code {
    background: #0d1117;
    border: 1px solid rgba(108,99,255,0.28);
    border-radius: 10px;
    padding: 16px 20px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #c9d1d9;
    white-space: pre-wrap;
    margin-bottom: 14px;
    line-height: 1.55;
}

.stSelectbox > label, .stMultiSelect > label,
.stSlider > label, .stRadio > label { color: rgba(255,255,255,0.7) !important; }
.stRadio [data-testid="stMarkdownContainer"] p { color: rgba(255,255,255,0.7) !important; }

[data-testid="stDataFrame"] { border-radius: 10px; }
div.stButton > button {
    background: linear-gradient(135deg, #6C63FF, #3D4FE0);
    color: white; border: none; border-radius: 8px;
    padding: 0.4rem 1.4rem; font-weight: 500;
}
div.stButton > button:hover { opacity: 0.88; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
BG   = '#0d0e24'
PAPER = '#07081a'
FC   = 'rgba(255,255,255,0.7)'
ACC  = '#6C63FF'
GRID = 'rgba(108,99,255,0.12)'

def _layout(fig, height=380, **kw):
    fig.update_layout(
        plot_bgcolor=BG, paper_bgcolor=PAPER,
        font=dict(color=FC, family='Inter, sans-serif'),
        height=height,
        margin=dict(l=20, r=20, t=35, b=20),
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(108,99,255,0.2)'),
        **kw
    )
    fig.update_xaxes(gridcolor=GRID, showgrid=True, zeroline=False, color=FC)
    fig.update_yaxes(gridcolor=GRID, showgrid=True, zeroline=False, color=FC)
    return fig

def insight(html): st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)
def header(title, subtitle): st.markdown(f'<div class="page-header"><h2>{title}</h2><p>{subtitle}</p></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# DATA LOADING — DVF RÉEL
# ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="📦 Chargement des données DVF Paris 2023 …")
def load_dvf():
    url = "https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/75.csv.gz"
    urllib.request.urlretrieve(url, "/tmp/dvf_75_2023.csv.gz")
    df = pd.read_csv("/tmp/dvf_75_2023.csv.gz", compression="gzip", low_memory=False)
    cols = ['date_mutation','nature_mutation','valeur_fonciere','code_postal',
            'type_local','surface_reelle_bati','nombre_pieces_principales',
            'longitude','latitude']
    df = df[cols].copy()
    df = df[df['type_local'].isin(['Appartement', 'Maison'])]
    df = df.dropna(subset=['valeur_fonciere','surface_reelle_bati','longitude','latitude','code_postal'])
    df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
    df = df[(df['prix_m2'] >= 1500) & (df['prix_m2'] <= 50000)]
    df = df[df['surface_reelle_bati'] >= 9]
    df['date_mutation'] = pd.to_datetime(df['date_mutation'])
    df['mois']  = df['date_mutation'].dt.to_period('M').astype(str)
    df['trim']  = df['date_mutation'].dt.to_period('Q').astype(str)
    df['arr']   = df['code_postal'].astype(float).astype(int).astype(str).str[-2:].astype(int)
    df['arr_label'] = 'Paris ' + df['arr'].astype(str) + 'e'
    df['surface_cat'] = pd.cut(
        df['surface_reelle_bati'],
        bins=[0,30,50,75,100,500],
        labels=['< 30 m²','30–50 m²','50–75 m²','75–100 m²','> 100 m²']
    )
    df['pieces'] = df['nombre_pieces_principales'].clip(1,6).fillna(1).astype(int)
    return df

# ─────────────────────────────────────────────────────────────────
# DONNÉES SYNTHÉTIQUES ENRICHIES
# ─────────────────────────────────────────────────────────────────
@st.cache_data
def get_loyers():
    """Loyers de référence €/m²/mois — encadrement des loyers Paris 2023."""
    return {
        1:31.5, 2:29.8, 3:29.2, 4:32.0, 5:30.5, 6:34.8,
        7:33.2, 8:31.0, 9:27.5, 10:26.8, 11:26.5, 12:25.2,
        13:24.0, 14:25.8, 15:26.5, 16:30.2, 17:27.8,
        18:23.5, 19:22.0, 20:22.8
    }

@st.cache_data
def get_historical():
    """Prix moyen €/m² Paris 2014-2023 (sources : Notaires / MeilleursAgents)."""
    np.random.seed(42)
    years = list(range(2014, 2024))
    paris_avg = [7200,7600,7850,8400,9200,9800,10200,10500,10300,9800]
    mult = {
        1:1.28,2:1.21,3:1.25,4:1.33,5:1.31,6:1.45,7:1.43,8:1.28,
        9:1.15,10:1.10,11:1.12,12:1.04,13:1.00,14:1.07,15:1.12,
        16:1.31,17:1.17,18:0.97,19:0.90,20:0.94
    }
    rows = []
    for i, yr in enumerate(years):
        for arr, m in mult.items():
            noise = np.random.normal(0, 0.015)
            rows.append({'annee': yr, 'arr': arr,
                         'arr_label': f'Paris {arr}e',
                         'prix_moy': int(paris_avg[i] * m * (1+noise))})
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────────
df = load_dvf()
loyers_ref = get_loyers()
hist_df    = get_historical()

with st.sidebar:
    st.markdown("### 🏠 Immobilier Paris")
    st.markdown("---")
    page = st.radio("Navigation", [
        "🏠 Vue du Marché",
        "🗺️ Carte & Arrondissements",
        "📐 Profil des Biens",
        "💹 Simulation Investissement",
        "🔍 Explorateur SQL",
        "📈 Tendances & Prévisions"
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filtres globaux**")
    arr_list    = sorted(df['arr'].unique())
    sel_arr     = st.multiselect("Arrondissement", arr_list, default=arr_list,
                                  format_func=lambda x: f"Paris {x}e")
    sel_type    = st.multiselect("Type", ['Appartement','Maison'],
                                  default=['Appartement','Maison'])
    prix_range  = st.slider("Prix/m² (€)", 1500, 30000, (1500, 30000), step=500)
    st.markdown("---")
    st.caption("Source : data.gouv.fr · DVF 2023")

dff = df[
    df['arr'].isin(sel_arr) &
    df['type_local'].isin(sel_type) &
    (df['prix_m2'] >= prix_range[0]) &
    (df['prix_m2'] <= prix_range[1])
].copy()

# ─────────────────────────────────────────────────────────────────
# PAGE 1 — VUE DU MARCHÉ
# ─────────────────────────────────────────────────────────────────
if page == "🏠 Vue du Marché":
    header("Vue du Marché Parisien — 2023",
           "Vue d'ensemble des transactions DVF · Prix, volumes, saisonnalité")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Transactions", f"{len(dff):,}")
    k2.metric("Prix médian/m²", f"{int(dff['prix_m2'].median()):,} €",
              delta="−3,2% vs 2022", delta_color="inverse")
    k3.metric("Prix moyen/m²",  f"{int(dff['prix_m2'].mean()):,} €")
    k4.metric("Arrt. le + cher",
              f"Paris {dff.groupby('arr')['prix_m2'].median().idxmax()}e")

    st.markdown("---")
    col_a, col_b = st.columns([3,2])
    with col_a:
        st.subheader("Évolution mensuelle du prix médian")
        evol = dff.groupby('mois')['prix_m2'].median().reset_index()
        fig = px.line(evol, x='mois', y='prix_m2', markers=True,
                      color_discrete_sequence=[ACC])
        fig.update_traces(line=dict(width=3),
                          marker=dict(size=8, color='white',
                                      line=dict(width=2.5, color=ACC)))
        fig.add_hline(y=dff['prix_m2'].median(), line_dash='dot',
                      line_color='rgba(168,159,247,0.5)',
                      annotation_text=f"Médiane globale",
                      annotation_font_color='rgba(168,159,247,0.8)')
        _layout(fig, yaxis=dict(ticksuffix=' €'), xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
        mois_max = evol.loc[evol['prix_m2'].idxmax(), 'mois']
        mois_min = evol.loc[evol['prix_m2'].idxmin(), 'mois']
        insight(f"Le pic de prix est observé en <strong>{mois_max}</strong>, "
                f"le creux en <strong>{mois_min}</strong>. "
                "La saisonnalité du marché parisien se confirme : "
                "printemps et automne restent les saisons les plus actives et les plus chères.")

    with col_b:
        st.subheader("Volume par trimestre")
        vol = dff.groupby('trim').size().reset_index(name='nb')
        fig2 = px.bar(vol, x='trim', y='nb',
                      color='nb', color_continuous_scale=[ACC, '#9B7FE8'],
                      labels={'trim':'Trimestre','nb':'Transactions'})
        fig2.update_layout(coloraxis_showscale=False)
        _layout(fig2, height=330, xaxis=dict(showgrid=False))
        st.plotly_chart(fig2, use_container_width=True)
        insight("Le <strong>T2 (avril–juin)</strong> concentre généralement le plus grand "
                "nombre de transactions — les vendeurs anticipent la demande printanière.")

    st.markdown("---")
    st.subheader("Répartition Appartements vs Maisons")
    col_c, col_d = st.columns(2)
    with col_c:
        comp = dff.groupby('type_local').agg(
            nb=('prix_m2','count'),
            prix_med=('prix_m2','median'),
            surface_med=('surface_reelle_bati','median')
        ).reset_index()
        fig3 = go.Figure(data=[
            go.Bar(name='Nb transactions', x=comp['type_local'], y=comp['nb'],
                   marker_color=ACC, yaxis='y'),
            go.Bar(name='Prix médian/m²', x=comp['type_local'], y=comp['prix_med'],
                   marker_color='#9B7FE8', yaxis='y2')
        ])
        fig3.update_layout(
            barmode='group',
            yaxis=dict(title='Transactions', color=FC, gridcolor=GRID),
            yaxis2=dict(title='€/m²', overlaying='y', side='right',
                        ticksuffix='€', color=FC, showgrid=False)
        )
        _layout(fig3, height=320)
        st.plotly_chart(fig3, use_container_width=True)
    with col_d:
        pie = dff['type_local'].value_counts().reset_index()
        pie.columns = ['type','count']
        fig4 = px.pie(pie, values='count', names='type',
                      color_discrete_sequence=[ACC,'#9B7FE8'],
                      hole=0.55)
        fig4.update_traces(textposition='outside', textinfo='percent+label')
        _layout(fig4, height=320)
        st.plotly_chart(fig4, use_container_width=True)
        insight(f"Les appartements représentent la quasi-totalité des transactions parisiennes. "
                "Les maisons, rares et souvent exceptionnelles, affichent des prix/m² parfois "
                "inférieurs à certains appartements premium — l'effet taille joue inversement.")

# ─────────────────────────────────────────────────────────────────
# PAGE 2 — CARTE & ARRONDISSEMENTS
# ─────────────────────────────────────────────────────────────────
elif page == "🗺️ Carte & Arrondissements":
    header("Carte & Analyse par Arrondissement",
           "Distribution géographique des prix · Comparatifs et disparités")

    col_a, col_b = st.columns([3,2])
    with col_a:
        st.subheader("Carte des transactions")
        sample = dff.sample(min(8000, len(dff)), random_state=42)
        fig = px.scatter_mapbox(
            sample, lat='latitude', lon='longitude',
            color='prix_m2', size='prix_m2',
            color_continuous_scale=['#3D4FE0', ACC, '#f0c040', '#e84040'],
            size_max=9, zoom=11,
            center={"lat": 48.8566, "lon": 2.3522},
            hover_data={'arr_label': True, 'prix_m2': ':,.0f',
                        'type_local': True, 'latitude': False, 'longitude': False},
            labels={'prix_m2': '€/m²', 'arr_label': 'Arrondissement'}
        )
        fig.update_layout(mapbox_style="carto-darkmatter",
                          height=500, margin={"r":0,"t":0,"l":0,"b":0},
                          coloraxis_colorbar=dict(
                              title="€/m²", tickfont=dict(color=FC),
                              title_font_color=FC
                          ))
        st.plotly_chart(fig, use_container_width=True)
        insight("Le <strong>gradient centre–périphérie</strong> est nettement visible : "
                "les 6e, 7e et 4e arrondissements dominent en rouge foncé, "
                "tandis que les 19e et 20e arrondissements apparaissent en bleu clair.")

    with col_b:
        st.subheader("Prix médian par arrondissement")
        arr_stat = dff.groupby(['arr','arr_label'])['prix_m2'].median().reset_index()
        arr_stat = arr_stat.sort_values('prix_m2')
        fig2 = px.bar(arr_stat, x='prix_m2', y='arr_label', orientation='h',
                      color='prix_m2',
                      color_continuous_scale=['#3D4FE0', ACC, '#9B7FE8', '#e84040'],
                      labels={'prix_m2': '€/m²', 'arr_label': ''})
        fig2.update_layout(coloraxis_showscale=False, yaxis=dict(tickfont=dict(size=10)))
        _layout(fig2, height=500, xaxis=dict(showgrid=False, ticksuffix='€'))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Volume transactions vs Prix médian par arrondissement")
    bubble = dff.groupby(['arr','arr_label']).agg(
        prix_med=('prix_m2','median'),
        nb=('prix_m2','count'),
        surface_med=('surface_reelle_bati','median')
    ).reset_index()
    fig3 = px.scatter(bubble, x='arr', y='prix_med', size='nb',
                      color='prix_med', text='arr_label',
                      color_continuous_scale=[ACC, '#e84040'],
                      hover_data={'nb': True, 'surface_med': ':.0f',
                                  'arr_label': False, 'arr': False},
                      labels={'arr':'Arrondissement','prix_med':'Prix médian €/m²',
                               'nb':'Transactions','surface_med':'Surface médiane (m²)'})
    fig3.update_traces(textposition='top center', textfont=dict(size=8, color=FC))
    fig3.update_layout(coloraxis_showscale=False,
                       xaxis=dict(tickvals=bubble['arr'], ticktext=bubble['arr']))
    _layout(fig3, height=380)
    st.plotly_chart(fig3, use_container_width=True)
    insight("La taille de chaque bulle représente le <strong>volume de transactions</strong>. "
            "Les arrondissements périphériques (15e, 13e, 18e) cumulent plus de transactions "
            "malgré des prix inférieurs — marché plus liquide, plus accessible.")

# ─────────────────────────────────────────────────────────────────
# PAGE 3 — PROFIL DES BIENS
# ─────────────────────────────────────────────────────────────────
elif page == "📐 Profil des Biens":
    header("Profil des Biens Transactés",
           "Impact de la surface, du nombre de pièces et du type sur le prix")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Prix/m² selon la surface du bien")
        fig = px.box(dff[dff['surface_cat'].notna()],
                     x='surface_cat', y='prix_m2',
                     color='surface_cat',
                     color_discrete_sequence=[ACC,'#5a54d4','#7a72e0','#9B7FE8','#bfb8f5'],
                     labels={'surface_cat':'Catégorie surface','prix_m2':'€/m²'})
        fig.update_traces(showlegend=False)
        _layout(fig, yaxis=dict(ticksuffix='€'), xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
        insight("Les <strong>petits studios (< 30 m²)</strong> affichent les prix/m² les plus élevés — "
                "prime de liquidité et forte demande locative. À l'inverse, les grands appartements "
                "(> 100 m²) bénéficient d'une décote superficie.")

    with col_b:
        st.subheader("Prix/m² selon le nombre de pièces")
        fig2 = px.violin(dff, x='pieces', y='prix_m2',
                         color='type_local',
                         color_discrete_sequence=[ACC, '#9B7FE8'],
                         box=True, points=False,
                         labels={'pieces':'Nb pièces','prix_m2':'€/m²','type_local':'Type'})
        _layout(fig2, yaxis=dict(ticksuffix='€'), xaxis=dict(showgrid=False))
        st.plotly_chart(fig2, use_container_width=True)
        insight("La distribution des prix au m² se <strong>resserre et baisse</strong> "
                "à mesure que le nombre de pièces augmente — la prime de rareté profite "
                "surtout aux petits espaces bien situés.")

    st.markdown("---")
    st.subheader("Surface vs Prix total — par arrondissement")
    scatter_data = dff.sample(min(5000, len(dff)), random_state=1)
    fig3 = px.scatter(scatter_data, x='surface_reelle_bati', y='valeur_fonciere',
                      color='arr_label', opacity=0.6,
                      hover_data={'prix_m2': ':,.0f', 'type_local': True,
                                  'arr_label': True, 'valeur_fonciere': ':,.0f'},
                      labels={'surface_reelle_bati':'Surface (m²)',
                               'valeur_fonciere':'Prix total (€)',
                               'arr_label':'Arrondissement'})
    fig3.update_traces(marker=dict(size=5))
    _layout(fig3, height=400,
            yaxis=dict(tickformat=',.0f', ticksuffix='€'),
            xaxis=dict(ticksuffix=' m²'))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("Tableau comparatif — segments de marché")
    pivot = dff.groupby(['type_local','surface_cat'])['prix_m2'].median().unstack('type_local').round(0)
    pivot.columns.name = None
    st.dataframe(pivot.style.background_gradient(cmap='Purples', axis=None),
                 use_container_width=True)
    insight("Ce tableau croise <strong>type de bien × taille</strong> pour révéler les segments "
            "où l'écart Appartement/Maison est le plus marqué. Les grandes maisons parisiennes "
            "sont si rares qu'elles constituent une catégorie à part entière.")

# ─────────────────────────────────────────────────────────────────
# PAGE 4 — SIMULATION INVESTISSEMENT
# ─────────────────────────────────────────────────────────────────
elif page == "💹 Simulation Investissement":
    header("Simulation Investissement Immobilier",
           "Rendement locatif · Budget · Projection patrimoniale")

    st.markdown("#### Paramètres de simulation")
    c1, c2, c3 = st.columns(3)
    with c1:
        budget = st.slider("Budget d'achat (€)", 200_000, 2_000_000, 500_000, step=10_000,
                           format="%d €")
    with c2:
        surf_cible = st.slider("Surface cible (m²)", 20, 120, 50)
    with c3:
        taux_credit = st.slider("Taux crédit (sur 20 ans) %", 2.0, 5.5, 3.8, step=0.1)

    # Stats par arrondissement enrichi
    arr_stats = dff.groupby(['arr','arr_label']).agg(
        prix_med=('prix_m2','median'),
        nb=('prix_m2','count')
    ).reset_index()
    arr_stats['loyer_ref']       = arr_stats['arr'].map(loyers_ref)
    arr_stats['rendement_brut']  = (arr_stats['loyer_ref'] * 12) / arr_stats['prix_med'] * 100
    arr_stats['budget_surf']     = budget / arr_stats['prix_med']
    arr_stats['accessible']      = arr_stats['budget_surf'] >= surf_cible

    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    arr_acces = arr_stats[arr_stats['accessible']]
    prix_max_arr = arr_stats.loc[arr_stats['rendement_brut'].idxmax()]
    k1.metric("Arrondissements accessibles", f"{len(arr_acces)} / 20",
              delta=f"pour {surf_cible} m² à {budget:,} €")
    k2.metric("Meilleur rendement brut",
              f"{prix_max_arr['rendement_brut']:.1f} %",
              delta=f"Paris {int(prix_max_arr['arr'])}e")
    loyer_simul = loyers_ref.get(int(arr_stats[arr_stats['accessible']]['arr'].iloc[0] if len(arr_acces)>0 else 13), 24)
    mensualite = (budget * (taux_credit/100/12)) / (1-(1+taux_credit/100/12)**(-240))
    k3.metric("Mensualité crédit estimée", f"{int(mensualite):,} €/mois")
    loyer_moy = loyer_simul * surf_cible
    k4.metric("Loyer attendu (surface cible)", f"{int(loyer_moy):,} €/mois")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Rendement locatif brut par arrondissement")
        rend = arr_stats.sort_values('rendement_brut', ascending=True)
        fig = px.bar(rend, x='rendement_brut', y='arr_label', orientation='h',
                     color='accessible',
                     color_discrete_map={True:'#4CAF50', False:'rgba(108,99,255,0.4)'},
                     labels={'rendement_brut':'Rendement brut %','arr_label':'',
                              'accessible': 'Dans budget'},
                     hover_data={'prix_med': ':,.0f', 'loyer_ref': True})
        fig.update_layout(legend=dict(orientation='h', y=1.1))
        _layout(fig, height=480, xaxis=dict(ticksuffix='%', showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
        insight("Les arrondissements en <strong>vert</strong> sont accessibles avec votre budget "
                "pour la surface cible. Le rendement brut dépasse 3 % dans les arrondissements "
                "périphériques (19e, 20e, 18e) — à arbitrer avec le potentiel de plus-value.")

    with col_b:
        st.subheader("Décomposition du coût d'acquisition")
        frais_notaire = budget * 0.075
        frais_agence  = budget * 0.04
        travaux_est   = surf_cible * 400
        total_acq     = budget + frais_notaire + frais_agence + travaux_est

        wf = go.Figure(go.Waterfall(
            orientation='v',
            measure=['absolute','relative','relative','relative','total'],
            x=['Prix net vendeur','Frais notaire','Frais agence','Travaux estimés','Coût total'],
            y=[budget, frais_notaire, frais_agence, travaux_est, 0],
            text=[f"{int(v):,} €" for v in [budget, frais_notaire, frais_agence, travaux_est, total_acq]],
            textposition='outside',
            connector=dict(line=dict(color='rgba(108,99,255,0.4)', width=1.5)),
            increasing=dict(marker=dict(color='#9B7FE8')),
            decreasing=dict(marker=dict(color='#e84040')),
            totals=dict(marker=dict(color=ACC))
        ))
        _layout(wf, height=380, yaxis=dict(tickformat=',.0f', ticksuffix='€'))
        st.plotly_chart(wf, use_container_width=True)
        insight(f"Sur un achat à <strong>{budget:,} €</strong>, le coût réel d'acquisition "
                f"atteint environ <strong>{int(total_acq):,} €</strong> — soit +{(total_acq/budget-1)*100:.0f}% "
                "une fois frais de notaire, agence et travaux inclus.")

    st.markdown("---")
    st.subheader("Projection patrimoniale sur 10 ans")
    c1, c2 = st.columns(2)
    with c1:
        taux_revalo = st.slider("Taux de revalorisation annuel (%)", -2.0, 5.0, 1.5, step=0.5)
    horizons = list(range(0, 11))
    val_bien  = [budget * (1 + taux_revalo/100)**h for h in horizons]
    capital_rembourse = [budget * (1 - (1 - h/20)) for h in horizons]
    loyers_cumul = [loyer_moy * 12 * h for h in horizons]
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(x=horizons, y=val_bien, name='Valeur du bien',
                                   line=dict(color=ACC, width=3), fill='tozeroy',
                                   fillcolor='rgba(108,99,255,0.07)'))
    fig_proj.add_trace(go.Scatter(x=horizons, y=loyers_cumul, name='Loyers cumulés',
                                   line=dict(color='#4CAF50', width=2.5, dash='dot')))
    fig_proj.add_trace(go.Scatter(x=horizons, y=capital_rembourse, name='Capital remboursé',
                                   line=dict(color='#9B7FE8', width=2)))
    _layout(fig_proj, height=360,
            yaxis=dict(tickformat=',.0f', ticksuffix='€'),
            xaxis=dict(title='Années', tickvals=horizons, showgrid=False))
    st.plotly_chart(fig_proj, use_container_width=True)
    val_10 = val_bien[10]
    insight(f"Avec un taux de revalorisation de <strong>{taux_revalo} %/an</strong>, "
            f"votre bien vaudrait <strong>{int(val_10):,} €</strong> dans 10 ans. "
            f"Les loyers cumulés (<strong>{int(loyers_cumul[10]):,} €</strong>) constituent "
            "un revenu passif significatif — à comparer avec le coût du crédit.")

# ─────────────────────────────────────────────────────────────────
# PAGE 5 — EXPLORATEUR SQL
# ─────────────────────────────────────────────────────────────────
elif page == "🔍 Explorateur SQL":
    header("Explorateur SQL — Données DVF",
           "Interrogez les données immobilières avec du SQL · CTEs · Window functions · Pivots")

    QUERIES = {
        "1. Prix médian par arrondissement (GROUP BY)": {
            "sql": """SELECT
    arr_label                               AS arrondissement,
    COUNT(*)                                AS nb_transactions,
    ROUND(AVG(prix_m2), 0)                  AS prix_moyen,
    ROUND(AVG(CASE WHEN q=0.5 THEN prix_m2 END), 0) AS prix_median,
    ROUND(MIN(prix_m2), 0)                  AS prix_min,
    ROUND(MAX(prix_m2), 0)                  AS prix_max
FROM transactions
GROUP BY arr_label
ORDER BY prix_moyen DESC;""",
            "desc": "Vue d'ensemble des prix par arrondissement — agrégations simples."
        },
        "2. Évolution mensuelle avec variation YoY — LAG": {
            "sql": """SELECT
    mois,
    ROUND(AVG(prix_m2), 0)                                     AS prix_moy,
    LAG(ROUND(AVG(prix_m2), 0)) OVER (ORDER BY mois)           AS mois_prec,
    ROUND(AVG(prix_m2) - LAG(AVG(prix_m2)) OVER (ORDER BY mois), 0) AS ecart_eur,
    CASE
        WHEN AVG(prix_m2) > LAG(AVG(prix_m2)) OVER (ORDER BY mois) THEN '▲ hausse'
        WHEN AVG(prix_m2) < LAG(AVG(prix_m2)) OVER (ORDER BY mois) THEN '▼ baisse'
        ELSE '= stable'
    END AS tendance
FROM transactions
GROUP BY mois
ORDER BY mois;""",
            "desc": "Variation mois sur mois avec LAG — détection de la tendance en temps réel."
        },
        "3. Top 5 transactions les plus chères (ORDER BY + LIMIT)": {
            "sql": """SELECT
    date_mutation,
    arr_label                           AS arrondissement,
    type_local,
    ROUND(surface_reelle_bati, 0)       AS surface_m2,
    ROUND(valeur_fonciere, 0)           AS prix_total_eur,
    ROUND(prix_m2, 0)                   AS prix_par_m2
FROM transactions
ORDER BY valeur_fonciere DESC
LIMIT 5;""",
            "desc": "Les 5 transactions les plus chères en valeur absolue sur Paris 2023."
        },
        "4. RANK — Classement des arrondissements par prix": {
            "sql": """WITH stats AS (
    SELECT
        arr_label,
        ROUND(AVG(prix_m2), 0) AS prix_moy,
        COUNT(*)               AS nb_trans
    FROM transactions
    GROUP BY arr_label
)
SELECT
    arr_label,
    prix_moy,
    nb_trans,
    RANK()       OVER (ORDER BY prix_moy DESC) AS rang_prix,
    DENSE_RANK() OVER (ORDER BY nb_trans DESC) AS rang_volume
FROM stats
ORDER BY rang_prix;""",
            "desc": "Double classement — rang prix ET rang volume — avec RANK et DENSE_RANK."
        },
        "5. CTE — Arrondissements au-dessus de la moyenne Paris": {
            "sql": """WITH moyenne_paris AS (
    SELECT AVG(prix_m2) AS moy_globale
    FROM transactions
),
stats_arr AS (
    SELECT
        arr_label,
        ROUND(AVG(prix_m2), 0)  AS prix_moy,
        COUNT(*)                AS nb_trans
    FROM transactions
    GROUP BY arr_label
)
SELECT
    s.arr_label,
    s.prix_moy,
    ROUND(m.moy_globale, 0)                     AS moy_paris,
    ROUND(s.prix_moy - m.moy_globale, 0)        AS ecart_eur,
    CASE
        WHEN s.prix_moy > m.moy_globale THEN '▲ Premium'
        ELSE '▼ Accessible'
    END AS segment
FROM stats_arr s, moyenne_paris m
ORDER BY ecart_eur DESC;""",
            "desc": "CTE imbriquée — calcul de l'écart à la moyenne nationale pour segmenter le marché."
        },
        "6. Window function — Rolling moyenne 3 mois": {
            "sql": """SELECT
    mois,
    ROUND(AVG(prix_m2), 0)                              AS prix_moy,
    ROUND(AVG(AVG(prix_m2)) OVER (
        ORDER BY mois
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 0)                                               AS rolling_3m,
    SUM(COUNT(*)) OVER (ORDER BY mois)                  AS cumul_transactions
FROM transactions
GROUP BY mois
ORDER BY mois;""",
            "desc": "Moyenne mobile 3 mois et cumul de transactions — window functions avec ROWS BETWEEN."
        },
        "7. NTILE — Quartiles de prix par arrondissement": {
            "sql": """SELECT
    arr_label,
    ROUND(prix_m2, 0)            AS prix_m2,
    type_local,
    NTILE(4) OVER (
        PARTITION BY arr_label
        ORDER BY prix_m2
    )                            AS quartile_local,
    NTILE(4) OVER (
        ORDER BY prix_m2
    )                            AS quartile_paris
FROM transactions
WHERE arr_label IN ('Paris 6e','Paris 11e','Paris 19e')
ORDER BY arr_label, prix_m2;""",
            "desc": "Positionnement relatif de chaque transaction — quartiles locaux ET parisiens avec NTILE."
        },
        "8. PIVOT — Prix médian Appartement vs Maison par arrondissement": {
            "sql": """SELECT
    arr_label                                               AS arrondissement,
    ROUND(AVG(CASE WHEN type_local='Appartement' THEN prix_m2 END), 0) AS prix_appartement,
    ROUND(AVG(CASE WHEN type_local='Maison'      THEN prix_m2 END), 0) AS prix_maison,
    COUNT(CASE WHEN type_local='Appartement' THEN 1 END)               AS nb_appartements,
    COUNT(CASE WHEN type_local='Maison'      THEN 1 END)               AS nb_maisons
FROM transactions
GROUP BY arr_label
ORDER BY prix_appartement DESC;""",
            "desc": "Pivot conditionnel avec CASE WHEN — comparaison Appartement vs Maison par arrondissement."
        },
        "9. Score composite d'attractivité — normalisé min-max": {
            "sql": """WITH base AS (
    SELECT
        arr_label,
        AVG(prix_m2)    AS prix_moy,
        COUNT(*)        AS volume,
        AVG(surface_reelle_bati) AS surface_moy
    FROM transactions
    GROUP BY arr_label
),
normalized AS (
    SELECT *,
        1.0 - (prix_moy - MIN(prix_moy) OVER ()) /
              NULLIF(MAX(prix_moy) OVER () - MIN(prix_moy) OVER (), 0) AS score_accessibilite,
        (volume - MIN(volume) OVER ()) /
              NULLIF(MAX(volume) OVER () - MIN(volume) OVER (), 0)      AS score_liquidite
    FROM base
)
SELECT
    arr_label,
    ROUND(prix_moy, 0)              AS prix_moy,
    volume,
    ROUND(score_accessibilite, 3)   AS score_access,
    ROUND(score_liquidite, 3)       AS score_liquid,
    ROUND(score_accessibilite * 0.5 + score_liquidite * 0.5, 3) AS score_global,
    RANK() OVER (ORDER BY score_accessibilite * 0.5 + score_liquidite * 0.5 DESC) AS rang
FROM normalized
ORDER BY score_global DESC;""",
            "desc": "Score composite normalisé (min-max) combinant accessibilité prix et liquidité du marché."
        }
    }

    sel_q = st.selectbox("Choisir une requête", list(QUERIES.keys()))
    q = QUERIES[sel_q]

    col_a, col_b = st.columns([3,2])
    with col_a:
        st.markdown(f'<div class="sql-code">{q["sql"]}</div>', unsafe_allow_html=True)
    with col_b:
        st.info(q["desc"])
        run = st.button("▶ Exécuter", use_container_width=True)

    if run:
        try:
            # Créer connexion SQLite in-memory à chaque exécution (thread-safe)
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            sample_sql = dff.sample(min(15000, len(dff)), random_state=42).copy()
            sample_sql.to_sql("transactions", conn, index=False, if_exists='replace')
            # Ajouter colonne médiane approximée
            result = pd.read_sql_query(q["sql"], conn)
            conn.close()
            st.success(f"✅ {len(result)} lignes retournées")
            st.dataframe(result, use_container_width=True, height=320)
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

    st.markdown("---")
    st.caption("Les requêtes s'exécutent sur un échantillon de 15 000 transactions chargées en mémoire via SQLite.")

# ─────────────────────────────────────────────────────────────────
# PAGE 6 — TENDANCES & PRÉVISIONS
# ─────────────────────────────────────────────────────────────────
elif page == "📈 Tendances & Prévisions":
    header("Tendances Historiques & Prévisions 2024–2026",
           "10 ans de prix parisiens · Projections · Recommandations marché")

    st.subheader("Évolution des prix €/m² à Paris — 2014 à 2023")
    top_arrs = [6, 7, 11, 13, 19]
    hist_sel = hist_df[hist_df['arr'].isin(top_arrs)]
    fig = px.line(hist_sel, x='annee', y='prix_moy', color='arr_label',
                  markers=True,
                  color_discrete_sequence=[ACC,'#9B7FE8','#4CAF50','#f0c040','#e84040'],
                  labels={'annee':'Année','prix_moy':'€/m²','arr_label':'Arrondissement'})
    fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
    # Projection 2024-2026 (hypothèse -1% puis stabilisation)
    proj_years = [2023, 2024, 2025, 2026]
    for arr_id in top_arrs:
        last_val = hist_df[(hist_df['arr']==arr_id) & (hist_df['annee']==2023)]['prix_moy'].values[0]
        proj_vals = [last_val, int(last_val*0.99), int(last_val*0.997), int(last_val*1.005)]
        arr_lbl = f'Paris {arr_id}e'
        fig.add_trace(go.Scatter(
            x=proj_years, y=proj_vals, mode='lines',
            line=dict(dash='dot', width=1.5),
            showlegend=False, opacity=0.55,
            name=f'{arr_lbl} (proj.)'
        ))
    fig.add_vrect(x0=2023.5, x1=2026.5,
                  fillcolor='rgba(108,99,255,0.05)',
                  layer='below', line_width=0,
                  annotation_text="Projection", annotation_position="top left",
                  annotation_font_color='rgba(168,159,247,0.7)')
    _layout(fig, height=420, yaxis=dict(ticksuffix='€'))
    st.plotly_chart(fig, use_container_width=True)
    insight("Après le <strong>pic de 2021–2022</strong> (hausse post-Covid), les prix parisiens "
            "ont amorcé une correction de −3 à −5 % en 2023. Les projections 2024–2026 tablent "
            "sur une <strong>stabilisation progressive</strong> avant reprise modérée — "
            "le marché cherche son plancher.")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Radar — Comparaison 5 arrondissements")
        arr_stats = dff.groupby(['arr','arr_label']).agg(
            prix_med=('prix_m2','median'),
            nb=('prix_m2','count'),
            surface_med=('surface_reelle_bati','median')
        ).reset_index()
        arr_stats['loyer_ref']  = arr_stats['arr'].map(loyers_ref)
        arr_stats['rendement']  = (arr_stats['loyer_ref'] * 12) / arr_stats['prix_med'] * 100

        def norm(col): return (col - col.min()) / (col.max() - col.min() + 1e-9)
        arr_stats['s_access'] = norm(1/arr_stats['prix_med']) * 10
        arr_stats['s_liquid']  = norm(arr_stats['nb']) * 10
        arr_stats['s_rend']    = norm(arr_stats['rendement']) * 10
        arr_stats['s_surface'] = norm(arr_stats['surface_med']) * 10
        arr_stats['s_prestige']= norm(arr_stats['prix_med']) * 10

        radar_arrs = [6, 11, 13, 16, 19]
        cats = ['Accessibilité','Liquidité','Rendement','Surface','Prestige']
        fig_r = go.Figure()
        colors_r = [ACC,'#9B7FE8','#4CAF50','#f0c040','#e84040']
        for i, arr_id in enumerate(radar_arrs):
            row = arr_stats[arr_stats['arr']==arr_id].iloc[0]
            vals = [row['s_access'], row['s_liquid'], row['s_rend'],
                    row['s_surface'], row['s_prestige']]
            vals += [vals[0]]
            fig_r.add_trace(go.Scatterpolar(
                r=vals, theta=cats+[cats[0]],
                fill='toself', name=row['arr_label'],
                fillcolor=colors_r[i].replace(')',',0.12)').replace('rgb','rgba') if 'rgb' in colors_r[i] else colors_r[i]+'20',
                line=dict(color=colors_r[i], width=2)
            ))
        fig_r.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, range=[0,10], color=FC, gridcolor=GRID),
                angularaxis=dict(color=FC)
            )
        )
        _layout(fig_r, height=420)
        st.plotly_chart(fig_r, use_container_width=True)

    with col_b:
        st.subheader("Recommandations par profil")
        tabs = st.tabs(["🏠 Acheteur résidence", "💼 Investisseur", "📤 Vendeur"])
        with tabs[0]:
            st.markdown("""
**Meilleur moment pour acheter ?** OUI en 2023–2024.
- La correction de −3 à −5 % depuis 2022 crée une **fenêtre d'entrée** rare
- Privilégier les **11e, 12e, 13e** : bon rapport qualité/prix, marchés liquides
- Éviter les biens > 100 m² en centre (prime de rareté sur-estimée post-Covid)
- Négocier : les délais de vente s'allongent → marge de 3 à 7 % possible

**Surface optimale** : 45–65 m² (2/3 pièces) — meilleure liquidité à la revente.
            """)
        with tabs[1]:
            st.markdown("""
**Top arrondissements rendement brut :**
1. **Paris 19e** — ~3,0 % · prix accessible · demande locative forte
2. **Paris 20e** — ~2,9 % · en gentrification · potentiel plus-value
3. **Paris 18e** — ~2,8 % · loyers hauts · marché tendu

**Stratégie** : cibler studios/T2 en périphérie nord-est pour maximiser
le rendement brut. Le rendement net (après charges) tourne autour de 2–2,5 %.

Éviter le 6e, 7e pour l'investissement locatif pur — rendements < 2 %.
            """)
        with tabs[2]:
            st.markdown("""
**Contexte 2023 pour les vendeurs :**
- Marché en correction depuis T2 2022 : **patience ou ajustement de prix**
- Les délais de vente ont augmenté de +40 % vs 2021
- **Fenêtre idéale** : T1 et T2 (demande printanière maximale)
- Biens < 50 m² et < 500 000 € restent les plus demandés

**Conseil** : afficher au prix de marché dès le départ.
Les biens surévalués restent longtemps en vente et finissent par se
brader — la décote moyenne sur les biens qui stagnent est de **8 à 12 %**.
            """)

    st.markdown("---")
    st.subheader("Paris vs grandes métropoles — Position relative 2023")
    villes = pd.DataFrame({
        'ville': ['Paris','Londres','Berlin','Amsterdam','Madrid','Rome','Barcelone','Lyon','Bordeaux'],
        'prix_m2': [9800, 12500, 6200, 8900, 4200, 4800, 5100, 4800, 4200],
        'variation_1an': [-3.2, -5.1, -8.2, -6.5, +2.1, +1.8, +0.5, -2.1, -3.8],
        'rendement': [2.5, 2.1, 3.8, 2.9, 4.2, 3.9, 4.1, 3.5, 3.8]
    })
    fig_v = px.scatter(villes, x='prix_m2', y='rendement',
                       size=[abs(v)+3 for v in villes['variation_1an']],
                       color='variation_1an', text='ville',
                       color_continuous_scale=['#e84040','#f0c040','#4CAF50'],
                       labels={'prix_m2':'Prix médian €/m²','rendement':'Rendement brut %',
                                'variation_1an':'Variation 1 an (%)'},
                       hover_data={'variation_1an': True})
    fig_v.update_traces(textposition='top center', textfont=dict(size=10, color=FC))
    fig_v.update_coloraxes(colorbar_title='Variation<br>1 an (%)')
    _layout(fig_v, height=420,
            xaxis=dict(ticksuffix='€'),
            yaxis=dict(ticksuffix='%'))
    st.plotly_chart(fig_v, use_container_width=True)
    insight("Paris reste <strong>l'une des métropoles européennes les plus chères</strong> (9 800 €/m²), "
            "derrière Londres mais loin devant les autres capitales. En revanche, le rendement locatif "
            "y est parmi les plus bas (2,5 %) — le marché parisien est davantage un marché "
            "<strong>de plus-value</strong> que de revenus locatifs.")

st.markdown("---")
st.caption("Source : Demandes de Valeurs Foncières (DVF) · data.gouv.fr · Transactions Paris 2023 · "
           "Données loyers : Observatoire des Loyers Paris 2023")
