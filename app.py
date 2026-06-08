"""
Project Pegasus - QofE Interactive Dashboard
Reads exclusively from data/pegasus.db (built by etl/build_db.py).
Run locally:  streamlit run app.py
"""
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB = Path(__file__).resolve().parent / "data" / "pegasus.db"

# ---- theme ---------------------------------------------------------------
NAVY, TEAL, AMBER, RED, SLATE = "#1f3a5f", "#2a9d8f", "#e9a23b", "#c1453b", "#6c7a89"
GRID = "#e6e8eb"
st.set_page_config(page_title="Project Pegasus | QofE Dashboard",
                   layout="wide", page_icon="📊")

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1300px;}
[data-testid="stMetric"] {background:#f7f9fb; border:1px solid #e6e8eb;
    border-radius:10px; padding:14px 16px;}
[data-testid="stMetricLabel"] {font-size:0.78rem; color:#6c7a89;}
h1,h2,h3 {color:#1f3a5f;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def q(sql: str) -> pd.DataFrame:
    con = sqlite3.connect(DB)
    df = pd.read_sql(sql, con)
    con.close()
    return df


def fmt_m(x):       # $ thousands -> $M
    return f"${x/1000:,.1f}M"


# ==========================================================================
# HEADER + KPI CARDS
# ==========================================================================
st.title("Project Pegasus — Quality of Earnings Dashboard")
st.caption("Live view of the five core KPIs and supporting financials. "
           "All figures US$ in thousands unless noted. FY2023–FY2025.")

kpi = q("select * from kpi_annual order by year")
cur, prv = kpi.iloc[-1], kpi.iloc[-2]


def delta(now, then, pct=False, inv=False):
    d = now - then
    s = f"{d:+.1f} pp" if pct else f"{d/then*100:+.1f}%"
    return s


c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Adj. revenue / procedure", f"${cur.rev_per_procedure:,.0f}",
          delta(cur.rev_per_procedure, prv.rev_per_procedure),
          help="Is each case getting more valuable? The core mix-shift test.")
c2.metric("Gross-to-net conversion", f"{cur.gross_to_net_pct:,.1f}%",
          delta(cur.gross_to_net_pct, prv.gross_to_net_pct, pct=True),
          help="How much of billed charges becomes net revenue.")
c3.metric("Cash collection rate", f"{cur.cash_collection_rate_pct:,.1f}%",
          delta(cur.cash_collection_rate_pct, prv.cash_collection_rate_pct, pct=True),
          help="Date-of-service cash collected as a % of gross charges. The floor under everything.")
asc_share = q("select sum(net_revenue) nr from location_annual where year=2025 and segment='ASC'").nr[0]
loc_tot = q("select sum(net_revenue) nr from location_annual where year=2025").nr[0]
c4.metric("ASC facility mix", f"{asc_share/loc_tot*100:,.0f}%",
          help="Share of net revenue from the ASC growth engine.")
ebit = q("select * from pnl_monthly")
ebit_m = ebit.assign(yr=ebit.month.str[:4]).groupby("yr").agg(
    e=("adjusted_ebitda", "sum"), r=("net_revenue", "sum"))
m25 = ebit_m.loc["2025"].e / ebit_m.loc["2025"].r * 100
m24 = ebit_m.loc["2024"].e / ebit_m.loc["2024"].r * 100
c5.metric("Adj. EBITDA margin", f"{m25:,.1f}%", delta(m25, m24, pct=True),
          help="Does growth drop to profit? (consolidated IS basis)")

st.divider()

# ==========================================================================
# MODULE 1 — P&L DEVELOPMENT OVER TIME
# ==========================================================================
st.header("1 · P&L Development Over Time")
gran = st.radio("View", ["Monthly", "Annual"], horizontal=True, key="pnl_gran")

pnl = q("select * from pnl_monthly")
pnl["date"] = pd.to_datetime(pnl.month + "-01")
if gran == "Annual":
    g = pnl.assign(yr=pnl.month.str[:4]).groupby("yr").agg(
        net_revenue=("net_revenue", "sum"), gross_profit=("gross_profit", "sum"),
        adjusted_ebitda=("adjusted_ebitda", "sum")).reset_index()
    g["x"] = g.yr
    g["gross_margin_pct"] = g.gross_profit / g.net_revenue * 100
    g["ebitda_margin_pct"] = g.adjusted_ebitda / g.net_revenue * 100
else:
    g = pnl.copy()
    g["x"] = g.date

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_bar(x=g.x, y=g.net_revenue, name="Net revenue", marker_color=NAVY, opacity=.85)
fig.add_bar(x=g.x, y=g.gross_profit, name="Gross profit", marker_color=TEAL, opacity=.85)
fig.add_trace(go.Scatter(x=g.x, y=g.adjusted_ebitda, name="Adj. EBITDA",
              mode="lines+markers", line=dict(color=AMBER, width=3)))
fig.add_trace(go.Scatter(x=g.x, y=g.ebitda_margin_pct, name="EBITDA margin %",
              mode="lines", line=dict(color=RED, width=2, dash="dot")), secondary_y=True)
fig.add_trace(go.Scatter(x=g.x, y=g.gross_margin_pct, name="Gross margin %",
              mode="lines", line=dict(color=SLATE, width=2, dash="dot")), secondary_y=True)
fig.update_layout(barmode="group", height=440, plot_bgcolor="white",
                  legend=dict(orientation="h", y=1.12), margin=dict(t=40, b=10),
                  yaxis_title="US$ (thousands)")
fig.update_yaxes(secondary_y=True, title="Margin %", range=[0, max(80, g.gross_margin_pct.max()+10)],
                 showgrid=False)
fig.update_yaxes(secondary_y=False, gridcolor=GRID)
fig.update_xaxes(showgrid=False)
st.plotly_chart(fig, use_container_width=True)
st.caption("Revenue grows on a richer case mix, not volume. Watch the EBITDA-margin "
           "line: it compresses into 2025 even as the bars rise.")

st.divider()

# ==========================================================================
# MODULE 2 — PERFORMANCE BY LOCATION
# ==========================================================================
st.header("2 · Performance by Location")
slice_by = st.radio("Slice", ["Clinic vs. ASC", "Texas vs. Georgia"],
                    horizontal=True, key="loc_slice")
loc = q("select * from location_annual")
dim = "segment" if slice_by.startswith("Clinic") else "state"
colmap = {"ASC": TEAL, "Clinic": NAVY, "TX": NAVY, "GA": AMBER}

a, b = st.columns([3, 2])
with a:
    grp = loc.groupby([dim, "year"]).net_revenue.sum().reset_index()
    fig2 = go.Figure()
    for key in grp[dim].unique():
        d = grp[grp[dim] == key]
        fig2.add_bar(x=d.year.astype(str), y=d.net_revenue, name=str(key),
                     marker_color=colmap.get(key, SLATE))
    fig2.update_layout(barmode="group", height=380, plot_bgcolor="white",
                       yaxis_title="Net revenue (US$ thousands)",
                       legend=dict(orientation="h", y=1.1), margin=dict(t=30))
    fig2.update_yaxes(gridcolor=GRID)
    fig2.update_xaxes(type="category")
    st.plotly_chart(fig2, use_container_width=True)
with b:
    cur_mix = loc[loc.year == 2025].groupby(dim).net_revenue.sum().reset_index()
    fig3 = go.Figure(go.Pie(labels=cur_mix[dim], values=cur_mix.net_revenue, hole=.55,
                            marker_colors=[colmap.get(k, SLATE) for k in cur_mix[dim]]))
    fig3.update_layout(height=380, title="2025 mix", margin=dict(t=40),
                       legend=dict(orientation="h", y=-0.05))
    st.plotly_chart(fig3, use_container_width=True)
st.caption("ASCs in Tyler and Texarkana carry an outsized share of revenue; Georgia "
           "remains a small, underbuilt footprint.")

st.divider()

# ==========================================================================
# MODULE 3 — REVENUE DRIVER ANALYSIS (volume vs rate)
# ==========================================================================
st.header("3 · Revenue Driver Analysis — Volume vs. Rate")
drv = q("select * from revenue_drivers order by year")
br = q("select * from revenue_bridge")

a, b = st.columns(2)
with a:
    fig4 = make_subplots(specs=[[{"secondary_y": True}]])
    fig4.add_bar(x=drv.year.astype(str), y=drv.procedure_count, name="Procedure count",
                 marker_color=SLATE, opacity=.8)
    fig4.add_trace(go.Scatter(x=drv.year.astype(str), y=drv.rev_per_procedure,
                   name="Net rev / procedure ($)", mode="lines+markers",
                   line=dict(color=AMBER, width=3)), secondary_y=True)
    fig4.update_layout(height=380, plot_bgcolor="white", margin=dict(t=30),
                       legend=dict(orientation="h", y=1.12),
                       yaxis_title="Procedures")
    fig4.update_yaxes(secondary_y=True, title="$ / procedure", showgrid=False)
    fig4.update_yaxes(secondary_y=False, gridcolor=GRID)
    fig4.update_xaxes(type="category", showgrid=False)
    st.plotly_chart(fig4, use_container_width=True)
    st.caption("Volume falls while price-per-case rises — the mix shift in one chart.")
with b:
    step = st.selectbox("Bridge step", br.step.tolist(), index=len(br)-1)
    row = br[br.step == step].iloc[0]
    fig5 = go.Figure(go.Waterfall(
        orientation="v", measure=["absolute", "relative", "relative", "total"],
        x=["Start NR", "Volume effect", "Rate effect", "End NR"],
        y=[row.start_net_revenue, row.volume_effect, row.rate_effect, row.end_net_revenue],
        text=[fmt_m(v) for v in [row.start_net_revenue, row.volume_effect,
                                 row.rate_effect, row.end_net_revenue]],
        textposition="outside",
        increasing=dict(marker_color=TEAL), decreasing=dict(marker_color=RED),
        totals=dict(marker_color=NAVY)))
    fig5.update_layout(height=380, plot_bgcolor="white", margin=dict(t=30),
                       title=f"Net revenue bridge · {step}",
                       yaxis_title="US$ (thousands)")
    fig5.update_yaxes(gridcolor=GRID)
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("Decomposes the year-over-year revenue change into volume and rate. "
               "In 2024→2025, rate more than offsets a sharp volume decline.")

st.divider()

# ==========================================================================
# MODULE 4 — CASH FLOW ANALYSIS
# ==========================================================================
st.header("4 · Cash Flow Analysis")
cash = q("select * from cash_annual order by year")
ar = q("select * from ar_monthly")
ar["date"] = pd.to_datetime(ar.month + "-01")

a, b, c = st.columns(3)
with a:
    fig6 = go.Figure()
    fig6.add_bar(x=cash.year.astype(str), y=cash.dso_days, marker_color=NAVY,
                 text=[f"{d:,.0f}d" for d in cash.dso_days], textposition="outside")
    fig6.update_layout(height=330, plot_bgcolor="white", title="Days sales outstanding",
                       margin=dict(t=40), yaxis_title="Days")
    fig6.update_yaxes(gridcolor=GRID)
    fig6.update_xaxes(type="category")
    st.plotly_chart(fig6, use_container_width=True)
with b:
    fig7 = go.Figure()
    fig7.add_bar(x=cash.year.astype(str), y=cash.cash_collections, name="Cash collected",
                 marker_color=TEAL)
    fig7.add_bar(x=cash.year.astype(str), y=cash.est_future_collections,
                 name="Est. future collections", marker_color=AMBER)
    fig7.update_layout(barmode="stack", height=330, plot_bgcolor="white",
                       title="Net revenue: cash vs. accrued", margin=dict(t=40),
                       legend=dict(orientation="h", y=-0.2), yaxis_title="US$ (thousands)")
    fig7.update_yaxes(gridcolor=GRID)
    fig7.update_xaxes(type="category")
    st.plotly_chart(fig7, use_container_width=True)
with c:
    fig8 = go.Figure()
    fig8.add_trace(go.Scatter(x=ar.date, y=ar.net_ar_insurance, name="Insurance / standard",
                   stackgroup="one", line=dict(width=0.5, color=NAVY)))
    fig8.add_trace(go.Scatter(x=ar.date, y=ar.net_ar_injury, name="Injury / PI",
                   stackgroup="one", line=dict(width=0.5, color=AMBER)))
    fig8.update_layout(height=330, plot_bgcolor="white", title="Net AR composition",
                       margin=dict(t=40), legend=dict(orientation="h", y=-0.2),
                       yaxis_title="US$ (thousands)")
    fig8.update_yaxes(gridcolor=GRID)
    fig8.update_xaxes(showgrid=False)
    st.plotly_chart(fig8, use_container_width=True)
st.caption("DSO sits near 200+ days and accrued (not-yet-collected) revenue is a "
           "growing slice of the top line — the central earnings-quality risk.")

st.divider()
st.caption("Source: Project Pegasus QofE databook, migrated to SQLite via etl/build_db.py. "
           "KPI/revenue metrics on the DD1 quality-of-revenue basis; P&L trend on the "
           "consolidated adjusted IS basis. Built for analysis, not investment advice.")