# Data Dictionary — `data/pegasus.db`

All monetary values are **US$ in thousands**. Built by `etl/build_db.py` from
the Project Pegasus QofE databook.

## `kpi_annual` (3 rows, one per fiscal year)
Source: **DD1. Quality of Revenue** (annual columns).

| column | meaning |
|---|---|
| `year` | fiscal year (2023–2025) |
| `reported_net_revenue` | net revenue, reported |
| `net_revenue` | net revenue, adjusted (QofE basis) |
| `cash_collections` | date-of-service cash collections |
| `est_future_collections` | revenue recognized but not yet collected |
| `gross_charges` | total gross billed charges |
| `procedure_count`, `encounters` | volume metrics |
| `rev_per_procedure` | adjusted net revenue per procedure |
| `gross_to_net_pct` | net revenue ÷ gross charges |
| `cash_collection_rate_pct` | cash collections ÷ gross charges |
| `efc_pct_of_net_rev` | est. future collections ÷ net revenue |

## `pnl_monthly` (36 rows)
Sources: **Clinic v. Corporate → Consolidated** (revenue, gross profit) and
**QofE Table** (EBITDA build). Consolidated adjusted IS basis.

`month, net_revenue, gross_profit, reported_ebitda, adjusted_ebitda,
interest_expense, gross_margin_pct, ebitda_margin_pct`

`adjusted_ebitda = reported_ebitda + total due-diligence adjustments`.

## `location_annual` (39 rows, long format)
Source: **Location Summary → Adjusted**.

`location, state (TX|GA), segment (ASC|Clinic), year, net_revenue`

ASC = Tyler Surgery Center, ASC-Texarkana. All other sites = Clinic.

## `revenue_drivers` (3 rows)
Derived from `kpi_annual`. Adds `gross_charge_per_proc`.

## `revenue_bridge` (2 rows)
Year-over-year net-revenue decomposition into volume and rate:
- `volume_effect = Δprocedures × prior-year rev/procedure`
- `rate_effect   = Δrev/procedure × current-year procedures`

## `ar_monthly` (36 rows)
Source: **AR** sheet. "Insurance/standard" = non-lien; "injury/PI" = lien.

`month, ar_insurance_gross, reserve_insurance, ar_injury_gross,
reserve_injury, net_ar, net_ar_insurance, net_ar_injury`

## `cash_annual` (3 rows)
Cash conversion and working-capital metrics:

`year, gross_charges, cash_collections, est_future_collections, net_revenue,
cash_conversion_pct, net_ar_year_end, dso_days`

`dso_days = year-end net AR ÷ net revenue × 365`.
