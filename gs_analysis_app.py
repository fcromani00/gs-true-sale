"""
GS Brasil – Whole Loan Forward Flow: Delinquency Analysis
Streamlit app — série histórica completa (SBOX Jul/23–Abr/26) + DME Mar/26–Jun/26
"""
import json
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from collections import defaultdict

st.set_page_config(
    page_title="GS Brasil – Delinquency Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PALETTE ───────────────────────────────────────────────────────────────────
BLUE    = "#2a78d6"
ORANGE  = "#eb6834"
GREEN   = "#1baf7a"
YELLOW  = "#eda100"
RED     = "#e34948"
MUTED   = "#898781"
GRID    = "rgba(200,200,195,0.4)"
SURFACE = "rgba(0,0,0,0)"

# ── DATA: MERCHANT ─────────────────────────────────────────────────────────────
# SBOX: Jul/23–Apr/26 (DM_CALCULO_TRAILING_BUCKETS_MERCH_GS_MLB, latest per month)
# DME:  Mar/26–Jun/26 (DM_MP_FND_BUCKETS_ROLLFORWARD_GS_MLB + TRAILING)
MERCH_ROWS = [
    ("2023-07-31", 2.7503, 2.7503, "PASS", "PASS", "SBOX"),
    ("2023-08-31", 3.7710, 3.7710, "PASS", "PASS", "SBOX"),
    ("2023-09-30", 5.2118, 5.2118, "PASS", "PASS", "SBOX"),
    ("2023-10-31", 4.1117, 4.6618, "PASS", "PASS", "SBOX"),
    ("2023-11-30", 3.8029, 4.3755, "PASS", "PASS", "SBOX"),
    ("2023-12-31", 3.7578, 3.8908, "PASS", "PASS", "SBOX"),
    ("2024-01-31", 5.6316, 4.3974, "PASS", "PASS", "SBOX"),
    ("2024-02-29", 5.4897, 4.9597, "PASS", "PASS", "SBOX"),
    ("2024-03-31", 7.3164, 6.1459, "PASS", "PASS", "SBOX"),  # ← pico mensal
    ("2024-04-30", 5.9416, 6.2492, "PASS", "PASS", "SBOX"),  # ← pico trailing
    ("2024-05-31", 5.3319, 6.1966, "PASS", "PASS", "SBOX"),
    ("2024-06-30", 5.9648, 5.7461, "PASS", "PASS", "SBOX"),
    ("2024-07-31", 2.9710, 4.7559, "PASS", "PASS", "SBOX"),
    ("2024-08-31", 4.9619, 4.6326, "PASS", "PASS", "SBOX"),
    ("2024-09-30", 3.8554, 3.9294, "PASS", "PASS", "SBOX"),
    ("2024-10-31", 4.3020, 4.3731, "PASS", "PASS", "SBOX"),
    ("2024-11-30", 4.6939, 4.2837, "PASS", "PASS", "SBOX"),
    ("2024-12-31", 4.3925, 4.4628, "PASS", "PASS", "SBOX"),
    ("2025-01-31", 5.3368, 4.8077, "PASS", "PASS", "SBOX"),
    ("2025-02-28", 4.4503, 4.7265, "PASS", "PASS", "SBOX"),
    ("2025-03-31", 4.5794, 4.7888, "PASS", "PASS", "SBOX"),
    ("2025-04-30", 5.0834, 4.7044, "PASS", "PASS", "SBOX"),
    ("2025-05-31", 4.3192, 4.6607, "PASS", "PASS", "SBOX"),
    ("2025-06-30", 3.6637, 4.3554, "PASS", "PASS", "SBOX"),
    ("2025-07-31", 4.2553, 4.0794, "PASS", "PASS", "SBOX"),
    ("2025-08-31", 3.7076, 3.8755, "PASS", "PASS", "SBOX"),
    ("2025-09-30", 5.9514, 4.6381, "PASS", "PASS", "SBOX"),
    ("2025-10-31", 6.5334, 5.3975, "PASS", "PASS", "SBOX"),
    ("2025-11-30", 4.1320, 5.5389, "PASS", "PASS", "SBOX"),
    ("2025-12-31", 3.6173, 4.7609, "PASS", "PASS", "SBOX"),
    ("2026-01-31", 5.4786, 4.4093, "PASS", "PASS", "SBOX"),
    ("2026-02-28", 3.9346, 4.3435, "PASS", "PASS", "SBOX"),
    # DME from Mar/26 (official, slight diff vs SBOX for same months)
    ("2026-03-31", 4.5560, 5.0086, "PASS", "PASS", "DME"),
    ("2026-04-30", 5.7991, 4.9392, "PASS", "PASS", "DME"),
    ("2026-05-31", 4.4553, 4.9368, "PASS", "PASS", "DME"),
    ("2026-06-30", 5.0686, 5.1077, "PASS", "PASS", "DME"),
]

# ── DATA: CONSUMER ─────────────────────────────────────────────────────────────
CONS_ROWS = [
    ("2023-07-31", 3.4110, 3.4110, "PASS", "PASS", "SBOX"),
    ("2023-08-31", 4.5261, 4.5261, "PASS", "PASS", "SBOX"),
    ("2023-09-30", 4.5229, 4.5229, "PASS", "PASS", "SBOX"),
    ("2023-10-31", 4.2159, 4.3694, "PASS", "PASS", "SBOX"),
    ("2023-11-30", 3.7056, 4.1481, "PASS", "PASS", "SBOX"),
    ("2023-12-31", 3.6640, 3.8618, "PASS", "PASS", "SBOX"),
    ("2024-01-31", 3.6814, 3.6836, "PASS", "PASS", "SBOX"),
    ("2024-02-29", 4.8435, 4.0629, "PASS", "PASS", "SBOX"),
    ("2024-03-31", 3.2225, 3.9158, "PASS", "PASS", "SBOX"),
    ("2024-04-30", 5.0458, 4.3706, "PASS", "PASS", "SBOX"),
    ("2024-05-31", 3.6923, 3.9869, "PASS", "PASS", "SBOX"),
    ("2024-06-30", 3.2483, 3.9955, "PASS", "PASS", "SBOX"),
    ("2024-07-31", 4.0208, 3.6538, "PASS", "PASS", "SBOX"),
    ("2024-08-31", 3.9702, 3.7464, "PASS", "PASS", "SBOX"),
    ("2024-09-30", 4.0954, 4.0288, "PASS", "PASS", "SBOX"),
    ("2024-10-31", 4.1773, 4.0809, "PASS", "PASS", "SBOX"),
    ("2024-11-30", 3.7012, 3.9913, "PASS", "PASS", "SBOX"),
    ("2024-12-31", 4.4864, 4.1216, "PASS", "PASS", "SBOX"),
    ("2025-01-31", 5.0538, 4.4138, "PASS", "PASS", "SBOX"),
    ("2025-02-28", 5.2243, 4.9215, "PASS", "PASS", "SBOX"),
    ("2025-03-31", 4.4587, 4.9123, "PASS", "PASS", "SBOX"),
    ("2025-04-30", 4.1149, 4.5993, "PASS", "PASS", "SBOX"),
    ("2025-05-31", 3.2999, 3.9578, "PASS", "PASS", "SBOX"),
    ("2025-06-30", 3.9579, 3.7909, "PASS", "PASS", "SBOX"),
    ("2025-07-31", 3.1052, 3.4543, "PASS", "PASS", "SBOX"),
    ("2025-08-31", 3.7848, 3.6160, "PASS", "PASS", "SBOX"),
    ("2025-09-30", 3.6461, 3.5120, "PASS", "PASS", "SBOX"),
    ("2025-10-31", 3.5919, 3.6743, "PASS", "PASS", "SBOX"),
    ("2025-11-30", 4.2922, 3.8434, "PASS", "PASS", "SBOX"),
    ("2025-12-31", 4.1970, 4.0270, "PASS", "PASS", "SBOX"),
    ("2026-01-31", 4.2059, 4.2317, "PASS", "PASS", "SBOX"),
    ("2026-02-28", 3.2159, 3.8729, "PASS", "PASS", "SBOX"),
    ("2026-03-31", 5.9018, 4.4412, "PASS", "PASS", "SBOX"),
    ("2026-04-30", 4.2248, 4.4475, "PASS", "PASS", "SBOX"),
    # DME Consumer from rollforward
    ("2026-03-31", 6.9331, None, "PASS", "PASS", "DME"),
    ("2026-04-30", 5.7200, None, "PASS", "PASS", "DME"),
    ("2026-05-31", 4.6666, None, "PASS", "PASS", "DME"),
]


def build_df(rows, prefer_dme_from="2026-03-31"):
    df = pd.DataFrame(rows, columns=["date", "monthly", "trailing", "nivel1", "nivel2", "source"])
    df["date"] = pd.to_datetime(df["date"])
    # Keep DME when both SBOX and DME exist for same date
    df = df.sort_values(["date", "source"], ascending=[True, False])  # DME > SBOX alphabetically? No. D<S → DME first
    df = df.sort_values(["date", "source"])  # DME comes before SBOX (D < S)
    df = df.drop_duplicates(subset="date", keep="first")
    df = df.sort_values("date").reset_index(drop=True)
    df["label"] = df["date"].dt.strftime("%b/%y")
    return df


df_m = build_df(MERCH_ROWS)
df_c = build_df(CONS_ROWS)

# ── VINTAGE DATA ──────────────────────────────────────────────────────────────
@st.cache_data
def load_vintage():
    raw_path = Path(r"C:\Users\fcromani\AppData\Local\Temp\claude\c--Users-fcromani-Projetos-MELI-2026-Migra--o-DME-com-Claude\79de03a9-2acd-465b-84e7-1652093621c2\scratchpad\vintage_data.json")
    with open(raw_path) as f:
        raw = json.load(f)
    result = {}
    for seg in ["total", "merchant", "consumer"]:
        rows = [r for r in raw[seg] if r["Credit_Creation_Month"] >= "2023-01-01"]
        by_month = defaultdict(dict)
        for r in rows:
            if r["OVER_90"] is not None:
                by_month[r["Credit_Creation_Month"]][r["MOB"]] = r["OVER_90"] / 100
        result[seg] = dict(by_month)
    return result


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### GS Brasil")
    st.markdown("**Whole Loan Forward Flow**")
    st.caption("Mercado Pago · Ago/2026")
    st.divider()
    page = st.radio("", ["Trailing Delinquency", "Vintage Chuveirinho"],
                    label_visibility="collapsed")
    st.divider()
    st.caption("Fontes  \nSBOX: `DM_CALCULO_TRAILING_BUCKETS_*`  \nDME: `DM_MP_FND_BUCKETS_*`")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 – TRAILING DELINQUENCY
# ══════════════════════════════════════════════════════════════════════════════
if page == "Trailing Delinquency":
    st.title("Trailing Portfolio Delinquency Ratio")
    st.caption("Jul/23 – Jun/26 · SBOX job 311252 + DME job 436747")

    tab_m, tab_c = st.tabs(["🏬 Merchant", "👤 Consumer"])

    def trailing_chart(df, seg_label, trig_1, trig_2, new_trig=None):
        max_monthly = df["monthly"].max()
        max_trailing = df["trailing"].dropna().max()
        idx_peak_m = df["monthly"].idxmax()
        idx_peak_t = df["trailing"].dropna().idxmax()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Máx. Monthly", f"{max_monthly:.2f}%", delta=df.loc[idx_peak_m, 'label'], delta_color="off")
        c2.metric("Máx. Trailing 3M", f"{max_trailing:.2f}%", delta=df.loc[idx_peak_t, 'label'], delta_color="off")
        c3.metric("Gatilho Nível I (atual)", f"{trig_1:.1f}%", delta="Accel. Amortization", delta_color="off")
        c4.metric("Gatilho Nível II (atual)", f"{trig_2:.1f}%", delta="Event of Default", delta_color="off")
        if new_trig:
            c5.metric("⚠️ Novo limite proposto", f"{new_trig:.1f}%", delta="Forward Flow draft", delta_color="off")

        # Alerts
        if max_trailing >= trig_1:
            st.error(f"🔴 Trailing excedeu o gatilho Nível I ({trig_1}%) em algum mês!")
        elif max_monthly >= trig_1:
            st.warning(f"⚠️ Monthly excedeu {trig_1:.0f}% em {df.loc[idx_peak_m, 'label']} ({max_monthly:.2f}%), "
                       f"mas trailing máx. foi {max_trailing:.2f}% → **PASS nos dois níveis**.")
        else:
            st.success(f"✅ PASS — Monthly máx. {max_monthly:.2f}%, Trailing máx. {max_trailing:.2f}%")

        if new_trig and max_trailing >= new_trig:
            st.error(f"🔴 Com o novo limite proposto de **{new_trig}%**: trailing de {max_trailing:.2f}% "
                     f"em {df.loc[idx_peak_t, 'label']} teria **FALHADO**.")

        fig = go.Figure()

        # Source background bands
        sbox_mask = df["source"] == "SBOX"
        dme_mask  = df["source"] == "DME"
        if dme_mask.any():
            first_dme = df.loc[dme_mask, "label"].iloc[0]
            fig.add_vrect(
                x0=first_dme, x1=df["label"].iloc[-1],
                fillcolor="rgba(26,122,68,0.06)", line_width=0,
                annotation_text="DME", annotation_position="top left",
                annotation_font=dict(size=9, color=GREEN),
            )

        # Monthly bars (light)
        fig.add_trace(go.Bar(
            x=df["label"], y=df["monthly"],
            name="Monthly %",
            marker_color=[RED + "cc" if v >= trig_1 else BLUE + "55" for v in df["monthly"]],
            hovertemplate="<b>%{x}</b><br>Monthly: %{y:.2f}%<extra></extra>",
        ))

        # Trailing 3M line
        df_t = df.dropna(subset=["trailing"])
        fig.add_trace(go.Scatter(
            x=df_t["label"], y=df_t["trailing"],
            name="Trailing 3M",
            line=dict(color=ORANGE, width=2.5),
            marker=dict(size=6, color=ORANGE),
            mode="lines+markers",
            hovertemplate="<b>%{x}</b><br>Trailing 3M: %{y:.2f}%<extra></extra>",
        ))

        # Trigger lines
        labels = df["label"].tolist()
        for val, name, color, dash in [
            (trig_1, f"Nível I atual ({trig_1}%)", YELLOW, "dash"),
            (trig_2, f"Nível II atual ({trig_2}%)", RED,    "dot"),
        ]:
            fig.add_hline(y=val, line_color=color, line_width=1.5, line_dash=dash,
                          annotation_text=name, annotation_position="top right",
                          annotation_font=dict(size=10, color=color))

        if new_trig:
            fig.add_hline(y=new_trig, line_color=GREEN, line_width=1.5, line_dash="dashdot",
                          annotation_text=f"Novo limite proposto ({new_trig}%)",
                          annotation_position="bottom right",
                          annotation_font=dict(size=10, color=GREEN))

        fig.update_layout(
            height=440,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
            barmode="overlay",
            yaxis=dict(title="Delinquency %", tickformat=".1f", ticksuffix="%",
                       gridcolor=GRID, range=[0, max(max_monthly, trig_2) * 1.15]),
            xaxis=dict(gridcolor=GRID, tickangle=-45, tickfont=dict(size=10)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Tabela completa"):
            show_df = df[["label", "monthly", "trailing", "nivel1", "nivel2", "source"]].copy()
            show_df.columns = ["Mês", "Monthly %", "Trailing 3M %", "Nível I", "Nível II", "Fonte"]
            def highlight_row(row):
                styles = [""] * len(row)
                if row["Monthly %"] >= trig_1:
                    styles[1] = "background-color: #fde8e8; color: #c00"
                if pd.notna(row["Trailing 3M %"]) and row["Trailing 3M %"] >= trig_1:
                    styles[2] = "background-color: #fde8e8; color: #c00"
                elif new_trig and pd.notna(row["Trailing 3M %"]) and row["Trailing 3M %"] >= new_trig:
                    styles[2] = "background-color: #fff3cd; color: #856404"
                return styles
            styled = show_df.style.apply(highlight_row, axis=1).format(
                {"Monthly %": "{:.2f}%", "Trailing 3M %": lambda x: f"{x:.2f}%" if pd.notna(x) else "—"}
            )
            st.dataframe(styled, use_container_width=True, height=420)

    with tab_m:
        st.markdown("**Merchant — Warehouse existente:** Nível I = 7% | Nível II = 8%  \n"
                    "**Forward Flow draft:** limite proposto ~6%")
        trailing_chart(df_m, "Merchant", trig_1=7.0, trig_2=8.0, new_trig=6.0)

    with tab_c:
        st.markdown("**Consumer — Warehouse existente:** Nível I = 7% | Nível II = 8%  \n"
                    "**Forward Flow draft:** limite proposto ~7%")
        trailing_chart(df_c, "Consumer", trig_1=7.0, trig_2=8.0, new_trig=None)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 – VINTAGE CHUVEIRINHO
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.title("Vintage Chuveirinho – DPD ≥ 90")
    st.caption("Lender 399304599 · desde Jan/23")

    vintage_data = load_vintage()

    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        segment = st.selectbox("Segmento", ["Merchant", "Consumer", "Total"])
    with col2:
        from_year = st.selectbox("A partir de", [2023, 2024, 2025, 2026])
    with col3:
        max_mob = st.slider("MOB máx.", 3, 43, 24)
    with col4:
        highlight_year = st.selectbox("Destacar ano", ["Todos", "2023", "2024", "2025", "2026"])

    seg_key = segment.lower()
    seg_data = vintage_data[seg_key]
    vintages = sorted(m for m in seg_data if m[:4] >= str(from_year))

    if not vintages:
        st.info("Sem dados para os filtros selecionados.")
        st.stop()

    def vintage_color(i, n, yr, hl):
        if hl != "Todos" and yr != hl:
            return "rgba(180,180,180,0.25)"
        t = i / max(n - 1, 1)
        rs, gs, bs = 0xcd, 0xe2, 0xfb
        re, ge, be = 0x0d, 0x36, 0x6b
        return "#{:02x}{:02x}{:02x}".format(
            int(rs + (re - rs) * t),
            int(gs + (ge - gs) * t),
            int(bs + (be - bs) * t),
        )

    import datetime as dt
    fig = go.Figure()
    n = len(vintages)

    for i, month in enumerate(vintages):
        mobs = sorted((k, v) for k, v in seg_data[month].items() if k <= max_mob)
        if not mobs:
            continue
        yr = month[:4]
        is_hl = highlight_year == "Todos" or yr == highlight_year
        color = vintage_color(i, n, yr, highlight_year)
        label = dt.datetime.strptime(month, "%Y-%m-%d").strftime("%b/%y")
        fig.add_trace(go.Scatter(
            x=[m for m, _ in mobs],
            y=[v for _, v in mobs],
            name=label,
            mode="lines",
            line=dict(color=color, width=2.2 if is_hl else 1.0),
            hovertemplate=f"<b>{label}</b>  MOB %{{x}}: %{{y:.4f}}<extra></extra>",
            showlegend=is_hl,
        ))

    # GS trigger reference points (from term sheet)
    triggers = {
        "merchant": {6: 15.0, 8: 18.0, 9: 19.0, 10: 19.5},
        "consumer": {4: 12.5, 5: 13.5, 6: 14.0, 7: 14.0},
        "total":    {},
    }
    trigs = {k: v for k, v in triggers[seg_key].items() if k <= max_mob}
    if trigs:
        fig.add_trace(go.Scatter(
            x=list(trigs.keys()), y=list(trigs.values()),
            name="Gatilho GS (cumul. %)",
            mode="markers+lines",
            line=dict(color=RED, width=1.5, dash="dot"),
            marker=dict(symbol="diamond", size=9, color=RED),
            hovertemplate="MOB %{x}: trigger %{y:.1f}%<extra></extra>",
        ))

    fig.update_layout(
        height=540,
        margin=dict(l=0, r=0, t=20, b=60),
        plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
        xaxis=dict(title="MOB", range=[1, max_mob], dtick=2,
                   gridcolor=GRID, showline=True, linecolor=GRID),
        yaxis=dict(title="OVER 90+ (REM_CAP / Orig.)",
                   gridcolor=GRID, showline=True, linecolor=GRID,
                   tickformat=".2f"),
        hovermode="x",
        legend=dict(
            font=dict(size=9), bgcolor="rgba(0,0,0,0)",
            orientation="h", y=-0.15, x=0,
        ) if highlight_year == "Todos" else dict(
            font=dict(size=9), bgcolor="rgba(0,0,0,0)",
            x=1.01, y=1,
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

    ca, cb, cc = st.columns(3)
    ca.metric("Vintages exibidos", len(vintages))
    max_y = max(
        (v for m in vintages for k, v in seg_data[m].items() if k <= max_mob if v),
        default=0,
    )
    cb.metric("Máx. OVER90", f"{max_y:.4f}")
    cc.metric("MOB máx.", max_mob)

    with st.expander("ℹ️ Sobre os dados do chuveirinho"):
        st.markdown("""
        **Fonte:** `DM_CRD_ACCOUNTING` + `BT_MP_CREDITS_CREDIT_DETAIL`
        | Lender `399304599` | Parceiro GS `571062534`

        **Y-axis:** `SUM(REM_CAP onde DPD≥90) / MAX(Orig. diária do vintage)` — razão bruta da query.

        Os **gatilhos GS** (diamantes vermelhos) são os limites cumulativos do term sheet (em %).
        A escala do Y não é diretamente comparável com eles; use o chuveirinho para comparar
        a **forma relativa** entre cohorts (vintage mais recente = linha mais escura).
        """)
