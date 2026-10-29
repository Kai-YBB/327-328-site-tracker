# Construction Sites in Carpenters Local 327 and 328 Territory

A public map and list of active construction sites in Carpenters Local 327 and
Local 328 territory (Boston, Cambridge and Somerville), union or not, with
contractor union records from Boston Employment Commission documents.

Most sites have no public record of union status. The page marks a site union
or open shop only when a record says so, labels every other site "Union status
not verified", and shows the counts at the top. "Local 327 area" or "Local 328
area" means the site is in that local's territory, not that the job is union.

## How it stays current

- **Every Monday**, a GitHub Action runs `scripts/build_data.py`. The script pulls
  the latest data from the Boston Planning Department, the Cambridge Development
  Log and Somerville building permits, then saves `data/sites.json`. GitHub Pages
  republishes the site on its own.
- Every run saves its result to `data/refresh_status.json`.
- **Every Monday afternoon**, a scheduled maintenance task follows `WEEKLY_TASK.md`:
  it checks that file, fixes the script if a source changed, and adds new Boston
  Employment Commission records.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The page people see. |
| `data/sites.json` | Site data the page loads. Built by the script; do not edit by hand. |
| `data/map.json` | Town and neighborhood outlines for the map. Does not change. |
| `scripts/build_data.py` | Pulls live data and builds `data/sites.json`. Hand-entered records are in its sections marked MANUAL RECORDS. |
| `data/refresh_status.json` | Result of the latest data refresh. |
| `.github/workflows/refresh.yml` | The weekly refresh schedule. |
| `WEEKLY_TASK.md` | What the weekly maintenance task does. Edit this to change it. |
| `MAINTENANCE.md` | Detailed maintenance steps. |
| `CONTENT_RULES.md` | Content and cost rules for anyone editing the records. |

## Data sources

- Boston Planning Department, Article 80 development projects
- City of Boston housing projects and Public Facilities projects in construction
- Cambridge Community Development Department, Development Log
- Somerville Inspectional Services, building permit applications
- Boston Employment Commission hearing minutes and agendas
- Carpenters Local 327 and 328 office details from nasrcc.org

City status can lag. A site listed as under construction may be finished or not started.
