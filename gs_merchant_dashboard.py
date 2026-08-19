import streamlit as st
import pandas as pd

from common import (
    label_pt, grupo_rating, tipo_produto_merch, CORES_RATING,
    TRIGGER_MERCH, TRIGGER_MERCH_TETO,
    build_chuveirinho, breach_summary, stats_periodo, insight_text, render_mes
)

st.set_page_config(page_title="GS Merchant — Chuveirinho", layout="wide", page_icon="🚿")


@st.cache_data
def load_detail():
    df = pd.read_csv('merch_detail_full.csv')
    df['mes'] = pd.to_datetime(df['mes'])
    df['volume_mm'] = df['volume_mm'].astype(float)
    df['prazo_medio'] = df['prazo_medio'].astype(float)
    df['grupo_rating'] = df['rating'].apply(grupo_rating)
    df['tipo_produto'] = df['produto'].apply(tipo_produto_merch)
    df['label'] = df['mes'].apply(label_pt)
    return df


@st.cache_data
def load_vintage():
    v = pd.read_csv('over30_merch.csv')
    v['Credit_Creation_Month'] = pd.to_datetime(v['Credit_Creation_Month'])
    v['OVER_30'] = v['OVER_30'].astype(float) * 100
    v['label'] = v['Credit_Creation_Month'].apply(label_pt)
    return v


df = load_detail()
df_vint = load_vintage()

meses = sorted(df['mes'].unique())
labels = [label_pt(m) for m in meses]

st.title("🚿 GS Merchant — Chuveirinho")
st.caption("Veja qual safra está pior no gráfico, selecione o mês abaixo e entenda por quê.")

mes_sel_label = st.selectbox("📌 Mês para analisar", labels, index=len(labels) - 1)
comparar = st.checkbox("Comparar com outro mês")
mes_comp_label = None
if comparar:
    outros_labels = [l for l in labels if l != mes_sel_label]
    idx_default = max(0, min(labels.index(mes_sel_label) - 3, len(outros_labels) - 1))
    mes_comp_label = st.selectbox("🆚 Comparar com", outros_labels, index=idx_default)

fig, df_breach = build_chuveirinho(
    df_vint, TRIGGER_MERCH, TRIGGER_MERCH_TETO, mes_sel_label, mes_comp_label
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
df_a = df[df['mes'] == mes_sel_ts]
vol_a, efgh_a, prazo_a = stats_periodo(df_a)

if mes_comp_label:
    mes_comp_ts = meses[labels.index(mes_comp_label)]
    df_b = df[df['mes'] == mes_comp_ts]
    vol_b, efgh_b, prazo_b = stats_periodo(df_b)
    col1, col2 = st.columns(2)
else:
    df_b = None
    col1 = st.container()
    col2 = None


render_mes(col1, df_a, mes_sel_label, vol_a, efgh_a, prazo_a, 'tipo_produto', cores_rating=CORES_RATING)
if col2 is not None:
    render_mes(col2, df_b, mes_comp_label, vol_b, efgh_b, prazo_b, 'tipo_produto', cores_rating=CORES_RATING)
    st.info(insight_text(vol_a, efgh_a, prazo_a, mes_sel_label, vol_b, efgh_b, prazo_b, mes_comp_label))

st.caption("Fonte: meli-bi-data.WHOWNER.BT_MP_CREDITS_CREDIT_DETAIL | GS Merchant (bpartner=571062534)")
