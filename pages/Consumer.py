import streamlit as st
import pandas as pd

from common import (
    label_pt, grupo_rating,
    TRIGGER_CONS, TRIGGER_CONS_TETO,
    build_chuveirinho, breach_summary, stats_periodo, insight_text, render_mes
)

st.set_page_config(page_title="GS Consumer — Chuveirinho", layout="wide", page_icon="🚿")


@st.cache_data
def load_product():
    df = pd.read_csv('product_mix_cons.csv')
    df['mes'] = pd.to_datetime(df['mes'])
    df['volume_mm'] = df['volume_mm'].astype(float)
    df['prazo_medio'] = df['avg_parcelas'].astype(float)
    df['label'] = df['mes'].apply(label_pt)
    return df


@st.cache_data
def load_rating():
    df = pd.read_csv('rating_mix_cons.csv')
    df['mes'] = pd.to_datetime(df['mes'])
    df['volume_mm'] = df['volume_mm'].astype(float)
    df['grupo_rating'] = df['rating'].apply(grupo_rating)
    df['label'] = df['mes'].apply(label_pt)
    return df


@st.cache_data
def load_vintage():
    v = pd.read_csv('over30_cons.csv')
    v['Credit_Creation_Month'] = pd.to_datetime(v['Credit_Creation_Month'])
    v['OVER_30'] = v['OVER_30'].astype(float) * 100
    v['label'] = v['Credit_Creation_Month'].apply(label_pt)
    return v


df_prod = load_product()
df_rat = load_rating()
df_vint = load_vintage()

meses = sorted(df_prod['mes'].unique())
labels = [label_pt(m) for m in meses]


def pct_efgh_mes(mes_ts):
    d = df_rat[df_rat['mes'] == mes_ts]
    vol = d['volume_mm'].sum()
    return d[d['grupo_rating'] == 'EFGH (ruim)']['volume_mm'].sum() / vol * 100 if vol > 0 else 0


st.title("🚿 GS Consumer — Chuveirinho")
st.caption("Veja qual safra está pior no gráfico, selecione o mês abaixo e entenda por quê.")

mes_sel_label = st.selectbox("📌 Mês para analisar", labels, index=len(labels) - 1)
comparar = st.checkbox("Comparar com outro mês")
mes_comp_label = None
if comparar:
    outros_labels = [l for l in labels if l != mes_sel_label]
    idx_default = max(0, min(labels.index(mes_sel_label) - 3, len(outros_labels) - 1))
    mes_comp_label = st.selectbox("🆚 Comparar com", outros_labels, index=idx_default)

fig, df_breach = build_chuveirinho(
    df_vint, TRIGGER_CONS, TRIGGER_CONS_TETO, mes_sel_label, mes_comp_label
)
st.plotly_chart(fig, width='stretch')
st.caption("MOB 2-3 fica fora do alerta de breach: base pequena faz o % oscilar muito (ruído).")

resumo = breach_summary(df_breach, labels)
if resumo:
    st.warning(f"⚠️ **Vintages que romperam o trigger:** {resumo}")
else:
    st.success("✅ Nenhuma vintage rompeu o trigger até o momento.")

st.markdown("---")

mes_sel_ts = meses[labels.index(mes_sel_label)]
df_a = df_prod[df_prod['mes'] == mes_sel_ts]
vol_a, _, prazo_a = stats_periodo(df_a)
efgh_a = pct_efgh_mes(mes_sel_ts)

if mes_comp_label:
    mes_comp_ts = meses[labels.index(mes_comp_label)]
    df_b = df_prod[df_prod['mes'] == mes_comp_ts]
    vol_b, _, prazo_b = stats_periodo(df_b)
    efgh_b = pct_efgh_mes(mes_comp_ts)
    col1, col2 = st.columns(2)
else:
    df_b = None
    col1 = st.container()
    col2 = None

render_mes(col1, df_a, mes_sel_label, vol_a, efgh_a, prazo_a, 'produto_grupo')
if col2 is not None:
    render_mes(col2, df_b, mes_comp_label, vol_b, efgh_b, prazo_b, 'produto_grupo')
    st.info(insight_text(vol_a, efgh_a, prazo_a, mes_sel_label, vol_b, efgh_b, prazo_b, mes_comp_label))

st.caption("Fonte: meli-bi-data.WHOWNER.BT_MP_CREDITS_CREDIT_DETAIL | GS Consumer (bpartner=571062534)")
