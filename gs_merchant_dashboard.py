import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="GS Merchant — Dashboard", layout="wide", page_icon="📊")

# ── Helpers ───────────────────────────────────────────────────────────────────
TRIGGER_MERCH = {2: 8, 3: 11, 4: 15, 5: 16, 6: 16, 7: 17, 8: 18, 9: 19}

def grupo_rating(r):
    if r in ('A', 'B', 'C'): return 'ABC (bom)'
    if r == 'D':              return 'D'
    if r in ('E', 'F', 'G', 'H'): return 'EFGH (ruim)'
    return 'Outro'

def tipo_produto(p):
    if p in ('EXPRESS_POINT_MLB_1', 'EXPRESS_MA_MLB', 'EXPRESS_MLB_1', 'BABY_EXPRESS_POINT_MLB_1'):
        return 'Express (1 parcela)'
    if p in ('MER_MLB_MA', 'POINT_MLB_1', 'MLB_EO_ONLINE', 'MER_MLB_SFO', 'POINT_MLB_FO_RNV', 'MER_MLB_FO_RNV'):
        return 'Parcelado curto (≤8x)'
    if p in ('MER_MLB_1', 'POINT_MLB_STD', 'FUNDING_MLB', 'CHECKOUT_MLB'):
        return 'Parcelado longo (8x+)'
    return 'Outro'

CORES_RATING  = {'ABC (bom)': '#1a7f37', 'D': '#f6c343', 'EFGH (ruim)': '#d1242f', 'Outro': '#aaaaaa'}
CORES_PRODUTO = {'Express (1 parcela)': '#e74c3c', 'Parcelado curto (≤8x)': '#f39c12', 'Parcelado longo (8x+)': '#8e44ad', 'Outro': '#aaaaaa'}

PT_MESES = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

def label_pt(ts):
    ts = pd.Timestamp(ts)
    return f"{PT_MESES[ts.month]}/{str(ts.year)[2:]}"

# ── Carregar dados ─────────────────────────────────────────────────────────────
@st.cache_data
def load():
    df = pd.read_csv('merch_detail_full.csv')
    df['mes'] = pd.to_datetime(df['mes'])
    df['volume_mm']  = df['volume_mm'].astype(float)
    df['prazo_medio'] = df['prazo_medio'].astype(float)
    df['pct_total']   = df['pct_total'].astype(float)
    df['qtd']         = df['qtd'].astype(int)
    df['ticket_medio'] = df['ticket_medio'].astype(float)
    df['grupo_rating']  = df['rating'].apply(grupo_rating)
    df['tipo_produto']  = df['produto'].apply(tipo_produto)
    df['label_mes']     = df['mes'].apply(label_pt)
    return df

df = load()
meses_sorted = sorted(df['mes'].unique())
labels_sorted = [label_pt(m) for m in meses_sorted]

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔎 Filtros")

mes_sel = st.sidebar.selectbox(
    "Mês de análise",
    options=range(len(meses_sorted)),
    format_func=lambda i: labels_sorted[i],
    index=len(meses_sorted) - 1
)
mes_atual = meses_sorted[mes_sel]

mes_comp_idx = st.sidebar.selectbox(
    "Comparar com",
    options=range(len(meses_sorted)),
    format_func=lambda i: labels_sorted[i],
    index=max(0, mes_sel - 3)
)
mes_comp = meses_sorted[mes_comp_idx]

st.sidebar.markdown("---")
rating_filter = st.sidebar.multiselect(
    "Grupo de Rating",
    options=['ABC (bom)', 'D', 'EFGH (ruim)'],
    default=['ABC (bom)', 'D', 'EFGH (ruim)']
)
produto_filter = st.sidebar.multiselect(
    "Tipo de Produto",
    options=['Express (1 parcela)', 'Parcelado curto (≤8x)', 'Parcelado longo (8x+)'],
    default=['Express (1 parcela)', 'Parcelado curto (≤8x)', 'Parcelado longo (8x+)']
)

# ── Dados filtrados ────────────────────────────────────────────────────────────
df_mes = df[
    (df['mes'] == mes_atual) &
    (df['grupo_rating'].isin(rating_filter)) &
    (df['tipo_produto'].isin(produto_filter))
]
df_comp = df[
    (df['mes'] == mes_comp) &
    (df['grupo_rating'].isin(rating_filter)) &
    (df['tipo_produto'].isin(produto_filter))
]
df_hist = df[
    (df['grupo_rating'].isin(rating_filter)) &
    (df['tipo_produto'].isin(produto_filter))
]

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 GS Merchant — Análise de Portfólio")
st.caption(f"Comparando **{labels_sorted[mes_sel]}** vs **{labels_sorted[mes_comp_idx]}**")

# ── Chuveirinho: Vintage Analysis (OVER 30) ────────────────────────────────────
st.subheader("🚿 Chuveirinho — OVER 30 por Vintage")
st.caption(
    "Cada linha cinza = uma safra de originação. Eixo X = MOB (meses desde a originação). "
    "Use este gráfico pra ver qual(is) vintage(s) romperam o trigger e escolher o mês na barra lateral. "
    "MOB 2-3 fica de fora do alerta de breach porque a base ainda é pequena e o % oscila muito (ruído)."
)

@st.cache_data
def load_vintage():
    v = pd.read_csv('over30_merch.csv')
    v['Credit_Creation_Month'] = pd.to_datetime(v['Credit_Creation_Month'])
    v['OVER_30'] = v['OVER_30'].astype(float) * 100
    v['label'] = v['Credit_Creation_Month'].apply(label_pt)
    return v

df_vint = load_vintage()
label_atual = labels_sorted[mes_sel]
label_comp  = labels_sorted[mes_comp_idx]

max_mob = int(df_vint['MOB'].max())
trigger_map = {m: TRIGGER_MERCH.get(m, 19.5) for m in range(2, max_mob + 1)}
df_vint['trigger_val'] = df_vint['MOB'].map(trigger_map)

fig_vint = go.Figure()

outros = df_vint[~df_vint['label'].isin([label_atual, label_comp])]
for cm, label in outros[['Credit_Creation_Month', 'label']].drop_duplicates().values:
    sub = outros[outros['Credit_Creation_Month'] == cm].sort_values('MOB')
    fig_vint.add_trace(go.Scatter(
        x=sub['MOB'], y=sub['OVER_30'], mode='lines',
        line=dict(color='#cccccc', width=1), opacity=0.7,
        name=label, showlegend=False, hoverinfo='skip'
    ))

sub_comp = df_vint[df_vint['label'] == label_comp].sort_values('MOB')
if not sub_comp.empty:
    fig_vint.add_trace(go.Scatter(
        x=sub_comp['MOB'], y=sub_comp['OVER_30'], mode='lines',
        line=dict(color='#1a7f37', width=2.5, dash='dash'),
        name=f'{label_comp} (comparação)'
    ))

sub_atual = df_vint[df_vint['label'] == label_atual].sort_values('MOB')
if not sub_atual.empty:
    fig_vint.add_trace(go.Scatter(
        x=sub_atual['MOB'], y=sub_atual['OVER_30'], mode='lines+markers',
        line=dict(color='#d1242f', width=3.5), marker=dict(size=5),
        name=f'{label_atual} (selecionado)'
    ))

fig_vint.add_trace(go.Scatter(
    x=list(trigger_map.keys()), y=list(trigger_map.values()), mode='lines',
    line=dict(color='black', width=2, dash='dot'), name='Trigger'
))

df_breach = df_vint[(df_vint['MOB'] >= 4) & (df_vint['OVER_30'] > df_vint['trigger_val'])]
if not df_breach.empty:
    fig_vint.add_trace(go.Scatter(
        x=df_breach['MOB'], y=df_breach['OVER_30'], mode='markers',
        marker=dict(symbol='x', size=9, color='#d1242f', line=dict(width=2)),
        name='Breach (rompeu trigger)'
    ))

fig_vint.update_layout(
    height=450, margin=dict(t=20, b=10),
    xaxis_title='MOB (meses desde a originação)',
    yaxis_title='OVER 30 (%)',
    legend=dict(orientation='h', y=-0.2),
    hovermode='x unified'
)
st.plotly_chart(fig_vint, use_container_width=True)

if not df_breach.empty:
    resumo_breach = (
        df_breach.groupby('label')['MOB'].min().reset_index()
        .rename(columns={'MOB': 'mob'})
    )
    ordem = {lbl: i for i, lbl in enumerate(labels_sorted)}
    resumo_breach = resumo_breach.sort_values(by='label', key=lambda s: s.map(ordem))
    texto = ", ".join(f"{r.label} (MOB {int(r.mob)})" for r in resumo_breach.itertuples())
    st.warning(f"⚠️ **Vintages que romperam o trigger:** {texto}")
else:
    st.success("✅ Nenhuma vintage rompeu o trigger até o momento.")

st.markdown("---")

# ── KPIs ───────────────────────────────────────────────────────────────────────
def kpis(d, label):
    vol      = d['volume_mm'].sum()
    pct_efgh = d[d['grupo_rating'] == 'EFGH (ruim)']['volume_mm'].sum() / vol * 100 if vol > 0 else 0
    pct_exp  = d[d['tipo_produto'] == 'Express (1 parcela)']['volume_mm'].sum() / vol * 100 if vol > 0 else 0
    wa_prazo = (d['prazo_medio'] * d['volume_mm']).sum() / vol if vol > 0 else 0
    return vol, pct_efgh, pct_exp, wa_prazo

v1, e1, x1, p1 = kpis(df_mes,  labels_sorted[mes_sel])
v2, e2, x2, p2 = kpis(df_comp, labels_sorted[mes_comp_idx])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Volume Total (R$M)",     f"R${v1:.1f}M",   f"{v1-v2:+.1f}M vs {labels_sorted[mes_comp_idx]}")
col2.metric("% EFGH (rating ruim)",   f"{e1:.1f}%",     f"{e1-e2:+.1f}pp", delta_color="inverse")
col3.metric("% Express (1 parcela)",  f"{x1:.1f}%",     f"{x1-x2:+.1f}pp")
col4.metric("Prazo médio ponderado",  f"{p1:.1f}x",     f"{p1-p2:+.1f}x", delta_color="inverse")

st.markdown("---")

# ── Row 1: Rating mix histórico + Rating mix comparativo ──────────────────────
col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("Mix de Rating — histórico")
    df_hist_agg = (
        df_hist.groupby(['mes', 'label_mes', 'grupo_rating'])['volume_mm']
        .sum().reset_index()
    )
    totais_hist = df_hist_agg.groupby('mes')['volume_mm'].sum().rename('total')
    df_hist_agg = df_hist_agg.join(totais_hist, on='mes')
    df_hist_agg['pct'] = df_hist_agg['volume_mm'] / df_hist_agg['total'] * 100
    df_hist_agg = df_hist_agg.sort_values('mes')

    fig_hist = px.bar(
        df_hist_agg, x='label_mes', y='pct', color='grupo_rating',
        color_discrete_map=CORES_RATING,
        labels={'pct': '% do volume', 'label_mes': '', 'grupo_rating': 'Rating'},
        category_orders={'grupo_rating': ['EFGH (ruim)', 'D', 'ABC (bom)']},
        barmode='stack'
    )
    fig_hist.add_hline(y=60, line_dash='dot', line_color='green',
                       annotation_text='Mín ABC = 60%', annotation_position='top left')
    fig_hist.update_layout(height=350, margin=dict(t=20, b=10), legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    st.subheader(f"Rating — {labels_sorted[mes_sel]}")
    df_pie = df_mes.groupby('grupo_rating')['volume_mm'].sum().reset_index()
    fig_pie = px.pie(
        df_pie, values='volume_mm', names='grupo_rating',
        color='grupo_rating', color_discrete_map=CORES_RATING,
        hole=0.4
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=350, margin=dict(t=20, b=10), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ── Row 2: Produto × Prazo comparativo ────────────────────────────────────────
st.subheader(f"Mix de Produto e Prazo — {labels_sorted[mes_sel]} vs {labels_sorted[mes_comp_idx]}")

col_c, col_d = st.columns(2)

def chart_produto(d, titulo):
    agg = d.groupby(['tipo_produto', 'grupo_rating']).agg(
        volume_mm=('volume_mm', 'sum'),
        prazo_medio=('prazo_medio', lambda x: (x * d.loc[x.index, 'volume_mm']).sum() / d.loc[x.index, 'volume_mm'].sum())
    ).reset_index()
    agg['label'] = agg['tipo_produto'] + '<br>' + agg['grupo_rating']

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for grp in ['ABC (bom)', 'D', 'EFGH (ruim)']:
        sub = agg[agg['grupo_rating'] == grp]
        fig.add_trace(go.Bar(
            x=sub['tipo_produto'], y=sub['volume_mm'],
            name=grp, marker_color=CORES_RATING[grp], legendgroup=grp,
            showlegend=True
        ), secondary_y=False)

    prazo_by_prod = d.groupby('tipo_produto').apply(
        lambda g: (g['prazo_medio'] * g['volume_mm']).sum() / g['volume_mm'].sum()
    ).reset_index(name='wa_prazo')
    fig.add_trace(go.Scatter(
        x=prazo_by_prod['tipo_produto'], y=prazo_by_prod['wa_prazo'],
        mode='markers+text', marker=dict(size=14, color='black', symbol='diamond'),
        text=prazo_by_prod['wa_prazo'].round(1).astype(str) + 'x',
        textposition='top center', name='Prazo médio WA', showlegend=True
    ), secondary_y=True)

    fig.update_layout(
        title=titulo, barmode='stack', height=380,
        margin=dict(t=40, b=10),
        legend=dict(orientation='h', y=-0.25),
        yaxis_title='Volume (R$M)',
        yaxis2_title='Prazo médio (parcelas)'
    )
    fig.update_yaxes(range=[0, 20], secondary_y=True)
    return fig

with col_c:
    st.plotly_chart(chart_produto(df_mes,  labels_sorted[mes_sel]),  use_container_width=True)
with col_d:
    st.plotly_chart(chart_produto(df_comp, labels_sorted[mes_comp_idx]), use_container_width=True)

st.markdown("---")

# ── Row 3: Tabela detalhada ───────────────────────────────────────────────────
st.subheader(f"Detalhe por produto — {labels_sorted[mes_sel]}")

tabela = (
    df_mes.groupby(['tipo_produto', 'grupo_rating', 'produto'])
    .agg(qtd=('qtd', 'sum'), volume_mm=('volume_mm', 'sum'),
         prazo_medio=('prazo_medio', lambda x: round((x * df_mes.loc[x.index, 'volume_mm']).sum() / df_mes.loc[x.index, 'volume_mm'].sum(), 1)),
         ticket_medio=('ticket_medio', 'mean'))
    .reset_index()
    .sort_values('volume_mm', ascending=False)
)
tabela['volume_mm']   = tabela['volume_mm'].round(2)
tabela['ticket_medio'] = tabela['ticket_medio'].round(0).astype(int)

st.dataframe(
    tabela.rename(columns={
        'tipo_produto': 'Tipo', 'grupo_rating': 'Rating', 'produto': 'Produto',
        'qtd': 'Qtd', 'volume_mm': 'Volume (R$M)', 'prazo_medio': 'Prazo Médio',
        'ticket_medio': 'Ticket Médio (R$)'
    }),
    use_container_width=True, height=400,
    column_config={
        'Volume (R$M)': st.column_config.NumberColumn(format="R$%.2fM"),
        'Ticket Médio (R$)': st.column_config.NumberColumn(format="R$%d"),
    }
)

st.caption("Fonte: meli-bi-data.WHOWNER.BT_MP_CREDITS_CREDIT_DETAIL | GS Merchant (bpartner=571062534)")
