# CHANGELOG

All notable changes to the Knowledge Watch plugin.

## [1.2.0] - 2026-11-13

The first two real scans on the install filed nothing, and the run log is why this was quick to find.

1. The first scan was refused by the install's injection guard, which withheld the web results as "an attempt to instruct you". The operator granted the two Knowledge agents an exception.
2. The second scan stopped at the engine's turn budget: "this turn reached its limit of 12 tool calls". A whole scan of 47 topics is more than a hundred searches and reads.

- fix: **one category per step, each in its own turn.** Knowledge scan now has 12 steps. Each step calls `knowledge_watch_scan_brief` with `next` true, scans the one category it is handed, and files it.
  - A step with no category left replies NOTHING DUE at once, so up to 12 categories are scanned per run.
  - The run ends when every category is handed out. It is marked failed, naming the categories that were never filed, if a step ran out or failed.
  - The spare steps after the last category start no second run.
- fix: **the Knowledge Researcher's own budget**, `limits` in its Agent.json: 60 tool calls and 70 model calls a turn. One category of up to 15 topics fits in it.
- change: the scan Skill (1.2.0) says how to work in one-category steps and to file what it has before its budget runs out.
- change: the Settings tab's progress counts every category the run is to scan (`expected`), not only those handed out so far.
- tests: 31.

## [1.1.0] - 2026-11-13

The operator: "We need Settings so I can see the Pipeline, start a refresh now, create a topic, view the notes, fine-tune my search on a topic, check if the job is running or stopped when it doesn't work."

- feat: **a Settings tab on the screen**, for the person who reads it.
  - Each Pipeline shows as on, off, running, failed or stopped, with why when it does not work.
  - A running scan shows how many categories it has filed, and the screen updates by itself.
  - **Refresh now** and **Write the digest now** start a run. They are open to anyone who may write the vault, not only Admins, and a second run is not started while one is going.
  - **Each category** shows when it was last scanned, what it filed and refused, and what was searched, with a Refresh button.
  - **Recent runs** lists the last runs and what happened in each.
  - An Admin can also switch each Pipeline on or off there.
- feat: **the run log** (`data/KnowledgeWatch/runs.json`). The framework tells a plugin only a Pipeline's last status, not whether one is running nor why it failed. So each run is recorded through the plugin's own tools:
  - `scan_brief` opens a scan, and each `save_items` marks a category filed;
  - the new `knowledge_watch_report_problem` records why a run could not go on;
  - `digest_facts` and `save_digest` open and close a digest;
  - a run left open for 45 minutes shows as stopped.
- feat: **Topics** (the tab was called Interests).
  - **Add a topic** asks for its category and name.
  - Opening a topic tunes its search: what you want to know, its own **search terms**, the sources to **look first at**, and what to **leave out**. The researcher is given all of it and runs the search terms.
  - The topic's drawer lists **its news**, and **Refresh this topic now** scans just that topic. This is one turn of the Knowledge Researcher (`api.agents.run`), in the background, recorded in the run log.
- feat: **Open the note** under a digest opens its vault note.
- change: the scan Skill and the researcher's soul. On a failed or withheld search, the researcher calls `report_problem` first, so the screen shows the tool's own words.
- docs: the Guide's Topics and news page, a Settings tab section, and troubleshooting for withheld web results.
- tests: 29.

## [1.0.0] - 2026-11-13

First release, built to the scope the operator approved on 2026-11-13: a weekly digest only, on Sunday at 18:00 Dubai, one weekly note in the vault, and no link to the other plugins.

It was first built as Industry Watch. The operator renamed it Knowledge Watch before release, because it covers topics and technology research as well as industry news. Every id follows the new name: the plugin, its agents, Skills, Pipelines, agent tools, screens, data folder and vault folder.

- feat: **the CBO's interests.** Knowledge categories, each with the topics he is interested in and a note per topic on what he wants to know. He adds, edits, switches off and deletes them on the **Interests** tab. Six ship:
  - AI models and providers;
  - hyperscalers and cloud;
  - sovereign AI and policy;
  - data centres, GPUs and power;
  - the Gulf and UAE technology market;
  - competitors and partners.
- feat: **Knowledge scan** (`CRON_TZ=Asia/Dubai 0 6 * * 0,2,4`). The Knowledge Researcher (web, no vault) searches every topic and files dated, sourced items with a summary, why each matters to Core42 (marked as inference), its importance and the organisations it names.
  - Items are kept once per link, with tracking parameters ignored.
  - Blocked sources are refused, and each scan files at most a set number of items per category.
- feat: **Knowledge weekly** (`CRON_TZ=Asia/Dubai 0 18 * * 0`). The Knowledge Editor (no web) writes the digest: headlines, one section per category, then what to watch next week.
  - It is filed on the screen and as a vault note in `Work/Knowledge Watch/`.
  - It is sent by the framework's Pipeline delivery.
- feat: **the Knowledge Watch screen.** Headline figures, then three tabs: **Weekly digest**, **News** (filter by category, period and words) and **Interests**.
- feat: **the Settings page**, a settings sheet:
  - when each Pipeline runs, with Run now;
  - where the digest goes (chat and email);
  - preferred and blocked sources, and how much a scan files;
  - the scan and digest prompts, and the vault folder.
- docs: the Guide (5 pages) and 2 help entries.
- tests: 17. `check_plugin.py` is ok.
