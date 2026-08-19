import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PT_MESES = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

def label_pt(ts):
    ts = pd.Timestamp(ts)
    return f"{PT_MESES[ts.month]}/{str(ts.year)[2:]}"

TRIGGER_MERCH = {2: 8, 3: 11, 4: 15, 5: 16, 6: 16, 7: 17, 8: 18, 9: 19}
TRIGGER_MERCH_TETO = 19.5  # MOB 10+

TRIGGER_CONS = {2: 8, 3: 10.5, 4: 12.5, 5: 13.5}
TRIGGER_CONS_TETO = 14  # MOB 6+

CORES_RATING = {'ABC (bom)': '#1a7f37', 'D': '#f6c343', 'EFGH (ruim)': '#d1242f', 'Outro': '#aaaaaa'}

def grupo_rating(r):
    if r in ('A', 'B', 'C'): return 'ABC (bom)'
    if r == 'D':              return 'D'
    if r in ('E', 'F', 'G', 'H'): return 'EFGH (ruim)'
    return 'Outro'

def tipo_produto_merch(p):
    if p in ('EXPRESS_POINT_MLB_1', 'EXPRESS_MA_MLB', 'EXPRESS_MLB_1', 'BABY_EXPRESS_POINT_MLB_1'):
        return 'Express (1 parcela)'
    if p in ('MER_MLB_MA', 'POINT_MLB_1', 'MLB_EO_ONLINE', 'MER_MLB_SFO', 'POINT_MLB_FO_RNV', 'MER_MLB_FO_RNV'):
        return 'Parcelado curto (≤8x)'
    if p in ('MER_MLB_1', 'POINT_MLB_STD', 'FUNDING_MLB', 'CHECKOUT_MLB'):
        return 'Parcelado longo (8x+)'
    return 'Outro'


def build_trigger_series(trigger_dict, teto, max_mob):
    return {m: trigger_dict.get(m, teto) for m in range(2, max_mob + 1)}


def build_chuveirinho(df_vint, trigger_dict, teto, label_atual, label_comp, min_mob_breach=4):
    """df_vint precisa ter colunas: label, MOB, OVER_30 (já em %)."""
    max_mob = int(df_vint['MOB'].max())
    trigger_map = build_trigger_series(trigger_dict, teto, max_mob)
    df_vint = df_vint.copy()
    df_vint['trigger_val'] = df_vint['MOB'].map(trigger_map)

    fig = go.Figure()

    outros = df_vint[~df_vint['label'].isin([label_atual, label_comp])]
    for lbl, sub in outros.groupby('label'):
        sub = sub.sort_values('MOB')
        fig.add_trace(go.Scatter(
            x=sub['MOB'], y=sub['OVER_30'], mode='lines',
            line=dict(color='#cccccc', width=1), opacity=0.7,
            name=lbl, showlegend=False, hoverinfo='skip'
        ))

    if label_comp:
        sub_comp = df_vint[df_vint['label'] == label_comp].sort_values('MOB')
        if not sub_comp.empty:
            fig.add_trace(go.Scatter(
                x=sub_comp['MOB'], y=sub_comp['OVER_30'], mode='lines',
                line=dict(color='#1a7f37', width=2.5, dash='dash'),
                name=f'{label_comp} (comparação)'
            ))

    sub_atual = df_vint[df_vint['label'] == label_atual].sort_values('MOB')
    if not sub_atual.empty:
        fig.add_trace(go.Scatter(
            x=sub_atual['MOB'], y=sub_atual['OVER_30'], mode='lines+markers',
            line=dict(color='#d1242f', width=3.5), marker=dict(size=5),
            name=f'{label_atual} (selecionado)'
        ))

    fig.add_trace(go.Scatter(
        x=list(trigger_map.keys()), y=list(trigger_map.values()), mode='lines',
        line=dict(color='black', width=2, dash='dot'),
        name=f'Trigger (teto {teto:g}%)'
    ))

    df_breach = df_vint[(df_vint['MOB'] >= min_mob_breach) & (df_vint['OVER_30'] > df_vint['trigger_val'])]
    if not df_breach.empty:
        fig.add_trace(go.Scatter(
            x=df_breach['MOB'], y=df_breach['OVER_30'], mode='markers',
            marker=dict(symbol='x', size=9, color='#d1242f', line=dict(width=2)),
            name='Breach (rompeu trigger)'
        ))

    fig.update_layout(
        height=420, margin=dict(t=20, b=10),
        xaxis_title='MOB (meses desde a originação)',
        yaxis_title='OVER 30 (%)',
        legend=dict(orientation='h', y=-0.2),
        hovermode='x unified'
    )
    return fig, df_breach


def breach_summary(df_breach, labels_order):
    if df_breach.empty:
        return None
    resumo = df_breach.groupby('label')['MOB'].min().reset_index()
    ordem = {lbl: i for i, lbl in enumerate(labels_order)}
    resumo = resumo.sort_values(by='label', key=lambda s: s.map(ordem))
    return ", ".join(f"{r.label} (MOB {int(r.MOB)})" for r in resumo.itertuples())


def stats_periodo(d, col_rating_pct='volume_mm', pct_efgh_from=None):
    """Recebe um df já filtrado por mês. Espera colunas volume_mm, prazo_medio (WA), grupo_rating (opcional)."""
    vol = d['volume_mm'].sum()
    wa_prazo = (d['prazo_medio'] * d['volume_mm']).sum() / vol if vol > 0 else 0
    if pct_efgh_from is not None:
        pct_efgh = pct_efgh_from
    elif 'grupo_rating' in d.columns:
        pct_efgh = d[d['grupo_rating'] == 'EFGH (ruim)']['volume_mm'].sum() / vol * 100 if vol > 0 else 0
    else:
        pct_efgh = None
    return vol, pct_efgh, wa_prazo


def insight_text(vol_a, efgh_a, prazo_a, label_a, vol_b, efgh_b, prazo_b, label_b):
    d_prazo = prazo_a - prazo_b
    d_efgh = (efgh_a - efgh_b) if (efgh_a is not None and efgh_b is not None) else 0
    partes = []
    if abs(d_prazo) >= 0.5:
        maior = label_a if d_prazo > 0 else label_b
        partes.append(f"prazo médio **{abs(d_prazo):.1f}x maior em {maior}**")
    if efgh_a is not None and abs(d_efgh) >= 3:
        maior = label_a if d_efgh > 0 else label_b
        partes.append(f"**{abs(d_efgh):.0f}pp mais volume em rating ruim (EFGH) em {maior}**")
    if not partes:
        return f"{label_a} e {label_b} têm perfil de rating e prazo parecidos — a diferença no chuveirinho provavelmente vem de outro fator (volume, sazonalidade)."
    return (
        "Principal diferença: " + " e ".join(partes) +
        ". Prazo mais longo mantém o saldo em atraso mais tempo no book; mais EFGH aumenta a chance de "
        "inadimplência — combinados, explicam a curva mais alta no chuveirinho."
    )


def chart_produto_prazo(d, dim_produto, titulo, cores_rating=None, dim_rating='grupo_rating'):
    """Barras de volume por produto (empilhado por rating se disponível) + diamante de prazo médio WA."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if dim_rating in d.columns and cores_rating is not None:
        agg = d.groupby([dim_produto, dim_rating])['volume_mm'].sum().reset_index()
        for grp in ['ABC (bom)', 'D', 'EFGH (ruim)']:
            sub = agg[agg[dim_rating] == grp]
            if sub.empty:
                continue
            fig.add_trace(go.Bar(
                x=sub[dim_produto], y=sub['volume_mm'],
                name=grp, marker_color=cores_rating[grp]
            ), secondary_y=False)
    else:
        agg = d.groupby(dim_produto)['volume_mm'].sum().reset_index()
        fig.add_trace(go.Bar(
            x=agg[dim_produto], y=agg['volume_mm'],
            name='Volume', marker_color='#4a90d9'
        ), secondary_y=False)

    prazo_by_prod = d.groupby(dim_produto)[['prazo_medio', 'volume_mm']].apply(
        lambda g: (g['prazo_medio'] * g['volume_mm']).sum() / g['volume_mm'].sum()
    ).reset_index(name='wa_prazo')
    fig.add_trace(go.Scatter(
        x=prazo_by_prod[dim_produto], y=prazo_by_prod['wa_prazo'],
        mode='markers+text', marker=dict(size=14, color='black', symbol='diamond'),
        text=prazo_by_prod['wa_prazo'].round(1).astype(str) + 'x',
        textposition='top center', name='Prazo médio WA'
    ), secondary_y=True)

    fig.update_layout(
        title=titulo, barmode='stack', height=350,
        margin=dict(t=40, b=10),
        legend=dict(orientation='h', y=-0.3),
        yaxis_title='Volume (R$M)',
        yaxis2_title='Prazo médio (parcelas)'
    )
    fig.update_yaxes(range=[0, 20], secondary_y=True)
    return fig


def render_mes(container, d, label, vol, efgh, prazo, dim_produto, cores_rating=None):
    with container:
        st.subheader(label)
        c1, c2, c3 = st.columns(3)
        c1.metric("Volume", f"R${vol:.1f}M")
        c2.metric("% EFGH (ruim)", f"{efgh:.1f}%" if efgh is not None else "—")
        c3.metric("Prazo médio", f"{prazo:.1f}x")
        fig_p = chart_produto_prazo(d, dim_produto, '', cores_rating=cores_rating)
        st.plotly_chart(fig_p, width='stretch')
