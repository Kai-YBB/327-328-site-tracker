# Boston Carpentry Site Tracker

A public map and list of active construction sites in Carpenters Local 327 and
Local 328 territory (Boston, Cambridge and Somerville), with contractor union
records from Boston Employment Commission documents.

## How it stays current

- **Every Monday**, a GitHub Action runs `scripts/build_data.py`. The script pulls
  the latest data from the Boston Planning Department, the Cambridge Development
  Log and Somerville building permits, then saves `data/sites.json`. GitHub Pages
  republishes the site on its own.
- Every run saves its result to `data/refresh_status.json`.
- **Every Monday afternoon**, a scheduled Claude task follows `WEEKLY_CLAUDE_TASK.md`:
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
| `WEEKLY_CLAUDE_TASK.md` | What the weekly Claude task does. Edit this to change it. |
| `MAINTENANCE.md` | Detailed maintenance steps. |
| `CLAUDE.md` | Content rules for anyone, person or Claude, editing the records. |

## Data sources

- Boston Planning Department, Article 80 development projects
- City of Boston housing projects and Public Facilities projects in construction
- Cambridge Community Development Department, Development Log
- Somerville Inspectional Services, building permit applications
- Boston Employment Commission hearing minutes and agendas
- Carpenters Local 327 and 328 office details from nasrcc.org

City status can lag. A site listed as under construction may be finished or not started.
