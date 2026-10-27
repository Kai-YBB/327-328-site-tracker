# Notes for Claude working in this repository

This is the public Boston Carpentry Site Tracker for YouthBuild Boston's resource
page: a list and map of active construction sites in Carpenters Local 327 and
Local 328 territory, with contractor union records from Boston Employment
Commission (BEC) documents.

## Content rules

- Every active site belongs on the page, union or not. Labels appear only where a
  public record supports them.
- Write only what a source says. Never infer union status. A project label
  ("Union", "Open Shop") is not proof that a contractor is signatory; say
  "on a project listed as Union" unless the document says "signatory".
- Every record links to its source document.
- No personal contact information: no names with phone numbers or emails of
  workers, foremen, supers or stewards. Union office phone numbers are fine.
- Plain, functional wording. No em dashes. No invented terms.

## How the pieces fit

- `scripts/build_data.py` pulls live open data and builds `data/sites.json`.
  Hand-entered records live in it under the sections marked MANUAL RECORDS.
- `.github/workflows/refresh.yml` runs the script every Monday and after any change
  to the script, and saves the result to `data/refresh_status.json`.
- `index.html` is the whole site. It loads `data/sites.json` and `data/map.json`.
- `WEEKLY_CLAUDE_TASK.md` is the weekly maintenance job. `MAINTENANCE.md` has the
  detailed steps it follows.

## Network note

A Claude cloud session's shell usually cannot reach the city data sites. Fetch
city pages and PDFs with the web fetch or Firecrawl tools instead, and let the
GitHub workflow run the script itself.
