"""
GS — Chuveirinho (Merchant + Consumer)
Gera um HTML autocontido (dados embutidos, JS puro) para publicar no Grid.

Uso:
    python generate_grid_dashboard.py            # produção — usa /d/_libs/plotly.min.js (Grid)
    python generate_grid_dashboard.py --local     # teste local — usa Plotly via CDN
"""
import argparse
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent

TRIGGER_MERCH = {"2": 8, "3": 11, "4": 15, "5": 16, "6": 16, "7": 17, "8": 18, "9": 19, "teto": 19.5}
TRIGGER_CONS = {"2": 8, "3": 10.5, "4": 12.5, "5": 13.5, "teto": 14}


def load_vint(fname):
    v = pd.read_csv(BASE / fname)
    v["Credit_Creation_Month"] = pd.to_datetime(v["Credit_Creation_Month"])
    return [
        {"m": r.Credit_Creation_Month.strftime("%Y-%m"), "mob": int(r.MOB), "o": round(float(r.OVER_30) * 100, 4)}
        for r in v.itertuples()
    ]


def load_merch_detail(fname):
    df = pd.read_csv(BASE / fname)
    df["mes"] = pd.to_datetime(df["mes"])
    return [
        {"m": r.mes.strftime("%Y-%m"), "p": r.produto, "r": r.rating,
         "v": round(float(r.volume_mm), 4), "t": round(float(r.prazo_medio), 4)}
        for r in df.itertuples()
    ]


def load_cons_product(fname):
    df = pd.read_csv(BASE / fname)
    df["mes"] = pd.to_datetime(df["mes"])
    return [
        {"m": r.mes.strftime("%Y-%m"), "p": r.produto_grupo,
         "v": round(float(r.volume_mm), 4), "t": round(float(r.avg_parcelas), 4)}
        for r in df.itertuples()
    ]


def load_cons_rating(fname):
    df = pd.read_csv(BASE / fname)
    df["mes"] = pd.to_datetime(df["mes"])
    return [
        {"m": r.mes.strftime("%Y-%m"), "r": r.rating, "v": round(float(r.volume_mm), 4)}
        for r in df.itertuples()
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true", help="usa Plotly via CDN para teste local (sem Grid)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    data = {
        "vint_merch": load_vint("over30_merch.csv"),
        "vint_cons": load_vint("over30_cons.csv"),
        "merch_detail": load_merch_detail("merch_detail_full.csv"),
        "cons_product": load_cons_product("product_mix_cons.csv"),
        "cons_rating": load_cons_rating("rating_mix_cons.csv"),
        "trigger_merch": TRIGGER_MERCH,
        "trigger_cons": TRIGGER_CONS,
    }

    template = (BASE / "grid_template.html").read_text(encoding="utf-8")
    plotly_src = "https://cdn.plot.ly/plotly-2.35.2.min.js" if args.local else "/d/_libs/plotly.min.js"
    html = (
        template
        .replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))
        .replace("__PLOTLY_SRC__", plotly_src)
    )

    default_name = "gs_chuveirinho_grid_local.html" if args.local else "gs_chuveirinho_grid.html"
    out = Path(args.out) if args.out else (BASE / default_name)
    out.write_text(html, encoding="utf-8")
    print(f"Gerado: {out}  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
