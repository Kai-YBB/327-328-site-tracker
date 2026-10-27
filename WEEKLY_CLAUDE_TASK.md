# Weekly Claude task

A scheduled Claude task runs this every Monday afternoon, a few hours after the
"Refresh site data" workflow. Edit this file to change what the weekly task does;
the schedule itself only says "follow WEEKLY_CLAUDE_TASK.md".

Read CLAUDE.md first. Its content rules apply to everything below.

## 1. Check this week's data refresh

1. Pull the latest `main` and open `data/refresh_status.json`.
2. If `ranAt` is more than 8 days old, the Monday run did not happen. Note it in
   the report (GitHub turns off scheduled workflows in repositories with no
   activity for 60 days; a commit or a manual run turns them back on).
3. If `result` is `ok`, go to step 2.
4. If `result` is `failed`, read `logTail`:
   - Timeout, connection error, or a 5xx error from a city site: the source was
     down. Note it and move on. Next week's run retries.
   - "NOT WRITTEN, data looks broken": a source returned too few sites. Check that
     source's page with the web fetch tool. If the data really shrank, lower the
     threshold in the script and explain why in the commit. If the source moved or
     changed, fix the script.
   - A Python error (KeyError, a renamed field, a new dataset id, a new URL): fix
     `scripts/build_data.py`. See MAINTENANCE.md step 1.
5. After pushing a script fix, the workflow runs again on its own. Wait for
   `data/refresh_status.json` to change (pull every 2 minutes, up to 20 minutes).
   If it still fails, try one more fix. If that fails too, stop and say so in the
   report. Do not loop.

## 2. Add new Boston Employment Commission records

Follow MAINTENANCE.md step 2. In short:

1. Open https://www.boston.gov/departments/small-business-development/boston-employment-commission
   with the web fetch tool and list minutes and agendas newer than the newest
   entry in the `BEC` dictionary in `scripts/build_data.py`.
2. Read each new document with the web fetch or Firecrawl tool.
3. Add the document to `BEC`, then add or update each project and contractor
   record it supports.
4. If there are no new documents, change nothing.

## 3. Check the change and publish

1. Run `python3 -m py_compile scripts/build_data.py` to catch typos.
2. Commit with a message that lists every document and project added or changed,
   then push to `main`. The workflow rebuilds the data and the site updates.
3. Wait for `data/refresh_status.json` to update as in step 1.5 and confirm
   `result` is `ok`. If the new records broke the build, revert your commit,
   push, and say so in the report.

## 4. Report

End with a short plain summary for Kai:
- Did Monday's refresh work, and how many sites are on the page now
  (from the `sites` line in `logTail`).
- Anything fixed in the script.
- BEC documents read, and projects or contractors added or changed.
- Anything that needs a person to look at it.

Never delete the repository, rewrite history, force-push, or change GitHub
settings.
