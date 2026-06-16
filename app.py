import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geobr

st.set_page_config(layout="wide", page_title="Eleições Bahia 2022", page_icon="🗳️")

# ============================================================
# Estilo
# ============================================================
AZUL1 = "#c8e6f5"
AZUL2 = "#6eb5d8"
AZUL3 = "#2a7fb5"
AZUL4 = "#003366"
CINZA_BG  = "#FFFFFF"
CINZA_MUN = "#c8d0d8"
TEXTO     = "#1A2533"
CARD_BG   = "#F5F7FA"
ACCENT    = "#1a6fa8"

st.markdown(f"""
<style>
  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {CINZA_BG};
      color: {TEXTO};
  }}
  [data-testid="stSidebar"] {{
      background-color: {CARD_BG} !important;
  }}
  .block-container {{ padding-top: 1.2rem; padding-bottom: 0; }}
  h1 {{ color: {TEXTO}; font-size: 1.45rem; letter-spacing: .02em; margin-bottom: .2rem; }}
  .subtitulo {{ color: #5a7080; font-size: .85rem; margin-top: -.4rem; margin-bottom: 1rem; }}
  [data-testid="metric-container"] {{
      background: {CARD_BG};
      border: 1px solid #d0dce8;
      border-radius: 10px;
      padding: 14px 16px 10px;
      margin-bottom: 10px;
  }}
  [data-testid="stMetricLabel"] {{ color: #5a7080 !important; font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }}
  [data-testid="stMetricValue"] {{ color: {ACCENT} !important; font-size: 1.25rem; font-weight: 700; }}
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stRadio label {{ color: {TEXTO} !important; font-size: .88rem; }}
  [data-testid="stSidebar"] .stRadio > div {{ gap: .3rem; }}
  hr {{ border-color: #d0dce8 !important; }}
  .ql-box {{
      display: flex; align-items: center; gap: 8px;
      background: {CARD_BG}; border: 1px solid #d0dce8;
      border-radius: 8px; padding: 8px 12px; margin-bottom: 6px;
  }}
  .ql-dot {{ width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }}
  .ql-label {{ color: {TEXTO}; font-size: .82rem; }}
  .ql-range {{ color: #5a7080; font-size: .78rem; margin-left: auto; }}
  .section-title {{
      color: #5a7080; font-size: .72rem; text-transform: uppercase;
      letter-spacing: .08em; margin: 1rem 0 .4rem;
  }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# Dados
# ============================================================
@st.cache_data
def load_data():
    return pd.read_excel("dados.xlsx")

@st.cache_data
def load_geo():
    return geobr.read_municipality(code_muni="BA", year=2020)

df = load_data()
gdf = load_geo()
gdf["name_muni_upper"] = gdf["name_muni"].str.upper()

# ============================================================
# Título
# ============================================================
st.markdown("# 🗳️ Distribuição dos votos para deputados — Eleições 2022")
st.markdown('<p class="subtitulo">Bahia · Deputado Estadual e Federal</p>', unsafe_allow_html=True)

# ============================================================
# Sidebar — Filtros + Botão Submeter
# ============================================================
with st.sidebar:
    st.markdown('<p class="section-title">Área</p>', unsafe_allow_html=True)
    escopo = st.radio("", ["Bahia", "Território de Identidade", "Município"], label_visibility="collapsed")

    territorios, municipios = [], []
    if escopo == "Território de Identidade":
        territorios = st.multiselect("Território", sorted(df["territorio_identidade"].unique()))
    elif escopo == "Município":
        municipios = st.multiselect("Município", sorted(df["nm_municipio"].unique()))

    st.markdown('<p class="section-title">Cargo</p>', unsafe_allow_html=True)
    cargo_sel = st.radio("", ["Todos", "Deputado Estadual", "Deputado Federal"], label_visibility="collapsed")

    st.markdown('<p class="section-title">Candidato</p>', unsafe_allow_html=True)
    opcoes_cand = ["Todos"] + sorted(df["nm_urna_candidato"].unique())
    candidato_sel = st.selectbox("", opcoes_cand, index=0, label_visibility="collapsed")

    st.markdown("")
    submeter = st.button("▶  Aplicar filtros", use_container_width=True, type="primary")

# ============================================================
# Lógica
# ============================================================
if "filtros" not in st.session_state:
    st.session_state.filtros = dict(
        escopo="Bahia", territorios=[], municipios=[],
        candidato="Todos", cargo="Todos"
    )
    st.session_state.filtros_aplicados = False

if submeter:
    st.session_state.filtros = dict(
        escopo=escopo, territorios=territorios,
        municipios=municipios, candidato=candidato_sel,
        cargo=cargo_sel
    )
    st.session_state.filtros_aplicados = True

fil = st.session_state.filtros
_escopo      = fil["escopo"]
_territorios = fil["territorios"]
_municipios  = fil["municipios"]
_candidato   = fil["candidato"]
_cargo       = fil.get("cargo", "Todos")

# ---- base geográfica ----
f_geo = df.copy()
if _territorios:
    f_geo = f_geo[f_geo["territorio_identidade"].isin(_territorios)]
elif _municipios:
    f_geo = f_geo[f_geo["nm_municipio"].isin(_municipios)]

if _cargo != "Todos":
    f_geo = f_geo[f_geo["ds_cargo"] == _cargo]

f_estadual = f_geo[f_geo["ds_cargo"] == "Deputado Estadual"]
f_federal  = f_geo[f_geo["ds_cargo"] == "Deputado Federal"]

# ---- municípios destacados no mapa ----
if _municipios:
    municipios_selecionados = set(_municipios)
elif _territorios:
    municipios_selecionados = set(df[df["territorio_identidade"].isin(_territorios)]["nm_municipio"].unique())
else:
    municipios_selecionados = set()

selecao_geo_ativa = bool(municipios_selecionados)

# ---- base do mapa ----
if _candidato != "Todos":
    base_mapa = f_geo[f_geo["nm_urna_candidato"] == _candidato]
else:
    base_mapa = f_geo

votos_mun = base_mapa.groupby("nm_municipio")["qt_votos_nom_validos"].sum().reset_index()
votos_mun["nm_municipio_upper"] = votos_mun["nm_municipio"].str.upper()

# Território de identidade por município
terr_mun = df[["nm_municipio", "territorio_identidade"]].drop_duplicates("nm_municipio")
votos_mun = votos_mun.merge(terr_mun, on="nm_municipio", how="left")

mapa = gdf.merge(votos_mun, left_on="name_muni_upper", right_on="nm_municipio_upper", how="left")
mapa["qt_votos_nom_validos"] = mapa["qt_votos_nom_validos"].fillna(0)
mapa["territorio_identidade"] = mapa["territorio_identidade"].fillna("—")

mun_sel_upper = {m.upper() for m in municipios_selecionados}
mapa["selecionado"] = mapa["name_muni_upper"].isin(mun_sel_upper) if selecao_geo_ativa else True
mapa_plot = mapa[mapa["selecionado"]].copy()

# ---- Classificar por quartis ----
def classificar_quartil(serie):
    if serie.nunique() < 4:
        ranks = serie.rank(method="first")
        return pd.cut(ranks, bins=4, labels=["Q1", "Q2", "Q3", "Q4"]).astype(str)
    q1, q2, q3 = serie.quantile([0.25, 0.5, 0.75])
    def cl(v):
        if v <= q1:  return "Q1"
        elif v <= q2: return "Q2"
        elif v <= q3: return "Q3"
        else:         return "Q4"
    return serie.apply(cl)

def quartil_ranges(serie):
    if serie.nunique() < 2:
        return {q: "—" for q in ["Q1","Q2","Q3","Q4"]}
    q1, q2, q3 = serie.quantile([0.25, 0.5, 0.75])
    qmax = serie.max()
    return {
        "Q1": f"0 – {q1:,.0f}",
        "Q2": f"{q1:,.0f} – {q2:,.0f}",
        "Q3": f"{q2:,.0f} – {q3:,.0f}",
        "Q4": f"{q3:,.0f} – {qmax:,.0f}",
    }

mapa_plot["faixa"] = classificar_quartil(mapa_plot["qt_votos_nom_validos"])
ranges = quartil_ranges(mapa_plot["qt_votos_nom_validos"])

QUARTIL_CORES = {"Q1": AZUL1, "Q2": AZUL2, "Q3": AZUL3, "Q4": AZUL4}

# ============================================================
# Layout: mapa (esquerda) + estatísticas (direita)
# ============================================================
map_col, stats_col = st.columns([2, 1])

with map_col:
    if selecao_geo_ativa:
        mapa_fora = mapa[~mapa["selecionado"]]
    else:
        mapa_fora = pd.DataFrame()

    ja_aplicou = st.session_state.get("filtros_aplicados", False)

    if not ja_aplicou:
        fig_map = go.Figure(go.Choropleth(
            geojson=mapa_plot.geometry.__geo_interface__,
            locations=mapa_plot.index,
            z=[0] * len(mapa_plot),
            colorscale=[[0, "rgba(255,255,255,0)"], [1, "rgba(255,255,255,0)"]],
            showscale=False,
            marker_line_color="#000000",
            marker_line_width=0.7,
            hovertemplate="<b>%{text}</b><br>Território: %{customdata}<extra></extra>",
            text=mapa_plot["name_muni"].values,
            customdata=mapa_plot["territorio_identidade"].values,
        ))
    else:
        fig_map = px.choropleth(
            mapa_plot, geojson=mapa_plot.geometry, locations=mapa_plot.index,
            color="faixa",
            category_orders={"faixa": ["Q1", "Q2", "Q3", "Q4"]},
            color_discrete_map=QUARTIL_CORES,
            hover_name="name_muni",
            hover_data={"qt_votos_nom_validos": ":,.0f", "faixa": True, "territorio_identidade": True},
            labels={"qt_votos_nom_validos": "Votos", "faixa": "Quartil", "territorio_identidade": "Território"},
        )
        fig_map.update_traces(
            marker_line_width=0.5,
            marker_line_color="#b0c4d8",
            hovertemplate="<b>%{hovertext}</b><br>Território: %{customdata[2]}<br>Votos: %{customdata[0]:,.0f}<br>Quartil: %{customdata[1]}<extra></extra>",
        )

    if not mapa_fora.empty:
        fig_cinza = go.Choropleth(
            geojson=mapa_fora.geometry.__geo_interface__,
            locations=mapa_fora.index,
            z=[0] * len(mapa_fora),
            colorscale=[[0, CINZA_MUN], [1, CINZA_MUN]],
            showscale=False,
            marker_line_color="#b0c4d8",
            marker_line_width=0.5,
            hovertemplate="<b>%{text}</b><extra></extra>",
            text=mapa_fora["name_muni"].values,
        )
        fig_map.add_trace(fig_cinza)

    if not mapa_plot.empty:
        bounds = mapa_plot.geometry.total_bounds
        pad_lat = max((bounds[3] - bounds[1]) * 0.08, 0.12)
        pad_lon = max((bounds[2] - bounds[0]) * 0.08, 0.12)
        fig_map.update_geos(
            visible=False,
            lataxis_range=[bounds[1] - pad_lat, bounds[3] + pad_lat],
            lonaxis_range=[bounds[0] - pad_lon, bounds[2] + pad_lon],
        )
    else:
        fig_map.update_geos(fitbounds="locations", visible=False)

    if _territorios:
        titulo_mapa = f"Território: {', '.join(_territorios)}"
    elif _municipios:
        titulo_mapa = f"Município: {', '.join(_municipios)}"
    else:
        titulo_mapa = "Bahia — todos os municípios"
    cargo_label = f" · {_cargo}" if _cargo != "Todos" else ""
    titulo_mapa += f"{cargo_label} · {'votos de ' + _candidato if _candidato != 'Todos' else 'votos totais'} · quartis"

    fig_map.update_layout(
        height=720,
        margin={"r": 0, "t": 32, "l": 0, "b": 0},
        title=dict(text=titulo_mapa, font=dict(size=13, color="#5a7080")),
        font=dict(color=TEXTO),
        paper_bgcolor=CINZA_BG,
        geo_bgcolor=CINZA_BG,
        showlegend=False,
    )
    st.plotly_chart(fig_map, use_container_width=True, key="mapa_principal")

with stats_col:
    st.markdown('<p class="section-title">Legenda — quartis de votos</p>', unsafe_allow_html=True)
    labels_quartil = {
        "Q1": "Menor concentração",
        "Q2": "Concentração média-baixa",
        "Q3": "Concentração média-alta",
        "Q4": "Maior concentração",
    }
    for q, cor in QUARTIL_CORES.items():
        st.markdown(f"""
        <div class="ql-box">
          <div class="ql-dot" style="background:{cor}"></div>
          <span class="ql-label">{labels_quartil[q]}</span>
          <span class="ql-range">{ranges[q]}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown('<p class="section-title">Estatísticas</p>', unsafe_allow_html=True)

    if _territorios:
        area_label = _territorios[0] if len(_territorios) == 1 else f"{len(_territorios)} territórios"
    elif _municipios:
        area_label = _municipios[0] if len(_municipios) == 1 else f"{len(_municipios)} municípios"
    else:
        area_label = "Bahia"

    st.metric("Área", area_label)
    st.metric("Cargo", _cargo)
    st.metric("Candidato", _candidato)

    # ---- Top 3 Deputado Estadual ----
    if not f_estadual.empty:
        st.markdown('<p class="section-title">Top 3 — Deputado Estadual</p>', unsafe_allow_html=True)
        top3_est = (f_estadual.groupby("nm_urna_candidato")["qt_votos_nom_validos"]
                    .sum().nlargest(3).reset_index())
        for i, row in enumerate(top3_est.itertuples()):
            medalha = ["🥇", "🥈", "🥉"][i]
            st.markdown(f"""
            <div class="ql-box" style="flex-direction: column; align-items: flex-start; gap: 2px;">
              <span class="ql-label"><b>{medalha} {row.nm_urna_candidato}</b></span>
              <span class="ql-range">{row.qt_votos_nom_validos:,.0f} votos</span>
            </div>""", unsafe_allow_html=True)

    # ---- Top 3 Deputado Federal ----
    if not f_federal.empty:
        st.markdown('<p class="section-title">Top 3 — Deputado Federal</p>', unsafe_allow_html=True)
        top3_fed = (f_federal.groupby("nm_urna_candidato")["qt_votos_nom_validos"]
                    .sum().nlargest(3).reset_index())
        for i, row in enumerate(top3_fed.itertuples()):
            medalha = ["🥇", "🥈", "🥉"][i]
            st.markdown(f"""
            <div class="ql-box" style="flex-direction: column; align-items: flex-start; gap: 2px;">
              <span class="ql-label"><b>{medalha} {row.nm_urna_candidato}</b></span>
              <span class="ql-range">{row.qt_votos_nom_validos:,.0f} votos</span>
            </div>""", unsafe_allow_html=True)

# ============================================================
# Função auxiliar para gráficos de barra
# ============================================================
def bar_chart(data, x, y, title):
    fig = px.bar(data, x=x, y=y, orientation="h", title=title,
                  color=x, color_continuous_scale=[[0, AZUL1],[0.33,AZUL2],[0.66,AZUL3],[1,AZUL4]],
                  text=x)
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        showlegend=False, coloraxis_showscale=False,
        font=dict(color=TEXTO, size=11),
        paper_bgcolor=CINZA_BG, plot_bgcolor=CINZA_BG,
        title=dict(font=dict(size=13, color="#5a7080")),
        xaxis=dict(gridcolor="#d0dce8", title="Votos válidos"),
        yaxis_title="",
        margin=dict(l=0, r=20, t=40, b=10),
    )
    return fig

st.divider()

# ============================================================
# Gráficos — Top 5 na área selecionada
# ============================================================
st.markdown('<p class="section-title">Top 5 na área selecionada</p>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

top_estadual = (f_estadual.groupby("nm_urna_candidato")["qt_votos_nom_validos"]
                .sum().nlargest(5).reset_index())
col1.plotly_chart(bar_chart(top_estadual, "qt_votos_nom_validos", "nm_urna_candidato",
                              "Deputado Estadual"), use_container_width=True, key="top5_estadual")

top_federal = (f_federal.groupby("nm_urna_candidato")["qt_votos_nom_validos"]
               .sum().nlargest(5).reset_index())
col2.plotly_chart(bar_chart(top_federal, "qt_votos_nom_validos", "nm_urna_candidato",
                              "Deputado Federal"), use_container_width=True, key="top5_federal")

st.divider()

# ============================================================
# Gráficos — Top 10 geral Bahia
# ============================================================
st.markdown('<p class="section-title">Top 10 — Bahia (geral)</p>', unsafe_allow_html=True)
col3, col4 = st.columns(2)

top10_base = df.copy()
if _cargo != "Todos":
    top10_base = top10_base[top10_base["ds_cargo"] == _cargo]

top10_est = (top10_base[top10_base["ds_cargo"] == "Deputado Estadual"]
             .groupby("nm_urna_candidato")["qt_votos_nom_validos"]
             .sum().nlargest(10).reset_index())
col3.plotly_chart(bar_chart(top10_est, "qt_votos_nom_validos", "nm_urna_candidato",
                              "Deputado Estadual"), use_container_width=True, key="top10_estadual")

top10_fed = (top10_base[top10_base["ds_cargo"] == "Deputado Federal"]
             .groupby("nm_urna_candidato")["qt_votos_nom_validos"]
             .sum().nlargest(10).reset_index())
col4.plotly_chart(bar_chart(top10_fed, "qt_votos_nom_validos", "nm_urna_candidato",
                              "Deputado Federal"), use_container_width=True, key="top10_federal")
