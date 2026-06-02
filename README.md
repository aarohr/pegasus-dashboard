# Project Pegasus — QofE Interactive Dashboard

A live, interactive Quality-of-Earnings dashboard for the Project Pegasus
databook. The Excel workbook is migrated into a **SQLite** database by a
one-time ETL; the dashboard (Streamlit + Plotly) reads **only** from the
database, never from Excel.

## What it shows

Five core KPIs across the header, then four analytical modules:

| Module | Question it answers | Key visuals |
|---|---|---|
| **1 · P&L Development Over Time** | Are revenue, profit and margins trending the right way? | Revenue + gross profit bars, adjusted-EBITDA line, gross & EBITDA margin lines (monthly / annual toggle) |
| **2 · Performance by Location** | Where does the money come from? | Clinic vs. ASC and Texas vs. Georgia, grouped bars + mix donut |
| **3 · Revenue Driver Analysis** | *Why* is revenue moving? | Procedure volume vs. net-revenue-per-procedure, plus a volume-vs-rate waterfall bridge |
| **4 · Cash Flow Analysis** | Does revenue become cash? | DSO trend, cash vs. accrued revenue, net-AR composition over time |

The five KPIs: net revenue per procedure, gross-to-net conversion, cash
collection rate, ASC facility mix, and adjusted EBITDA margin.

## Architecture

```
Excel databook  ──(etl/build_db.py)──►  data/pegasus.db  ──►  app.py (Streamlit)
```

## Tech stack
- **Database:** SQLite (file-based, zero-config, ships with the repo)
- **App:** Streamlit + Plotly
- **ETL:** pandas + openpyxl

## Run locally

```bash
pip install -r requirements.txt

# 1) build the database from the workbook (only needed once / on data refresh)
#    place the source workbook at data/pegasus_databook.xlsx first
python etl/build_db.py

# 2) launch the dashboard
streamlit run app.py
```

`data/pegasus.db` is committed, so step 2 works on a fresh clone without the
source workbook. Re-run step 1 only when the underlying data changes.

## Deploy (Streamlit Community Cloud)

1. Push this repo to GitHub (see below).
2. Go to https://share.streamlit.io → **New app**.
3. Pick the repo, branch `main`, main file `app.py`.
4. Deploy. The committed `data/pegasus.db` is all the app needs.

## Push to GitHub

```bash
git remote add origin https://github.com/<you>/pegasus-dashboard.git
git branch -M main
git push -u origin main
```

## Data notes
- All dollar figures are US$ in thousands.
- KPI and revenue-driver metrics use the **DD1 quality-of-revenue** basis
  (net revenue $35.3M in 2025). The P&L trend uses the **consolidated
  adjusted income-statement** basis (net revenue $35.6M), which is the
  matching basis for gross profit; the two differ by reconciling items
  (research income, litigation support, out-of-billing revenue, discontinued
  ops). This is documented in `data_dictionary.md`.
- The source workbook is blinded; the ETL maps fixed cell coordinates and
  includes reconciliation asserts that fail loudly if the layout shifts.

For analysis only — not investment advice.
