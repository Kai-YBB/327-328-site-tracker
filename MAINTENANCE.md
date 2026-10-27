# Maintenance steps

Detailed steps behind WEEKLY_CLAUDE_TASK.md. A person can follow them by hand too.

## 1. Check the data refresh

1. Open `data/refresh_status.json`. The workflow saves it after every run, with the
   result and the end of the log. The full log is at its `runUrl` (GitHub, Actions tab).
2. If `result` is `ok`, go to step 2.
3. If it failed, read the log. The script stops on purpose when a source is
   down or returns broken data, so the site keeps last week's data.
   - Source temporarily down (timeout, 5xx error): note it in the report and stop. Next week's run will retry.
   - Source changed (field renamed, new dataset id, new URL): fix `scripts/build_data.py`,
     commit, and push. The workflow re-runs on its own when the script changes.
   - Cambridge publishes a new Development Log dataset every quarter. The script
     finds it by name ("Development Log Current Edition YYYY Qn"). If Cambridge
     renames it, update the pattern in the `cambridge()` function.

## 2. Add new Boston Employment Commission records

The BEC page lists hearing minutes and links each monthly agenda:
https://www.boston.gov/departments/small-business-development/boston-employment-commission

1. Find minutes or agendas newer than the newest one in the `BEC` dictionary in
   `scripts/build_data.py`.
2. For each new document, add it to `BEC` with a new key (`mYYYY-MM` for minutes,
   `aYYYY-MM` for agendas), its title, URL and date.
3. For each project in it:
   - If it matches a site already built from Boston Planning data, add or update its
     `attach(...)` call: general contractor, contractors with trades, the Union or
     Open Shop label exactly as the document gives it, and a short `ev(...)` note.
   - If it is not in the Planning Department list but has a street address and is
     clearly under construction or starting, add it with `manual(...)` in the extra
     Boston sites section. Get coordinates from the US Census geocoder
     (geocoding.geo.census.gov). If there is no address, add it to `names_only`.
   - For every contractor the document links to a union or open shop label, add an
     `E(...)` evidence line to that contractor in `contractors`, or add the
     contractor with `K(...)`.
4. Rules for these records:
   - Write only what the document says. Do not infer union status.
   - A label on a project is not proof that a contractor is signatory. Word it as
     "on a project listed as Union", not "is signatory", unless the document says signatory.
   - Never add personal contact information (names with phone numbers or emails of
     workers, foremen or stewards). Union office phone numbers are fine.
   - Plain wording. No em dashes.
5. Remove `attach(...)` calls for projects the script reports as no longer under
   construction only if their records are older than two years.

## 3. Test and publish

1. If your computer can reach the city data sites, run `python3 scripts/build_data.py`.
   It must finish with "wrote data/sites.json". If it cannot (a Claude cloud session
   usually cannot), run `python3 -m py_compile scripts/build_data.py` instead and let
   the workflow do the real test.
2. Commit with a message that lists what changed, and push. The workflow rebuilds
   the data, and GitHub Pages republishes within a few minutes.
3. Check that `data/refresh_status.json` updates with `result: ok`.

## 4. Report

Write a short summary: whether the refresh worked, what was fixed, and which BEC
documents and projects were added.
