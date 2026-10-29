# Content rules and project notes

This is the public site "Construction Sites in Carpenters Local 327 and 328 Territory"
(repository 327-328-site-tracker) for YouthBuild Boston's resource
page: a list and map of active construction sites in Carpenters Local 327 and
Local 328 territory, with contractor union records from Boston Employment
Commission (BEC) documents.

## Content rules

- Every active site belongs on the page, union or not. Labels appear only where a
  public record supports them.
- Unverified union status must be easy to see. Keep the "Union status not
  verified" label on every site without a record, the counts notice at the top
  of the page, and "Local 327 area" / "Local 328 area" wording (a site's local
  means its territory, not that the job is union). Do not rename the page to
  anything that suggests every site is union.
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
- `WEEKLY_TASK.md` is the weekly maintenance job. `MAINTENANCE.md` has the
  detailed steps it follows.

## Network note

A cloud session's shell usually cannot reach the city data sites. Fetch
city pages and PDFs with the free web fetch tool instead, and let the GitHub
workflow run the script itself.

## Cost rule

Nothing in this project may cost Kai money beyond his existing subscriptions.
- Use only the built-in web fetch and web search tools. Do not use Firecrawl or
  any other connector that bills per use, even if it is available.
- Do not add paid services, paid GitHub features, or API keys.
- If a step cannot be done without something that costs money, skip it and say
  so in the report so Kai can decide.
