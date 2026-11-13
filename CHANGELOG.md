# CHANGELOG

All notable changes to the Knowledge Watch plugin.

## [1.4.1] - 2026-11-13

From the first runs on the live install (2026-11-13). The first scan on 1.4.0 filed 17 items across six categories in 30 minutes. The first real digest was written from them, filed in the vault, and sent by chat and email.

- fix: **Write the digest now is refused while a scan is running.** On the install, a digest run started seconds before the scan. It wrote and sent a digest saying nothing was filed. The route now answers "a scan is running; write the digest when it has finished", and the button waits for the scan.
- fix: **the Settings tab does not crash on a state it does not know.** Right after the update, the backend still served 1.0's routes until it was restarted, and the page failed with "reading 'tone'". An unknown state is now shown as it is, in a neutral badge, and an answer without runs shows none.
- docs: **an update needs a backend restart.** Like any plugin with a backend, Knowledge Watch's code loads only when the backend starts. After installing or updating, use **Restart now** on Settings > System, as the wizard says. `restarts_itself: true` in the install's answer means only that the install can restart itself from that button, not that it already has.
- tests: 37.

## [1.4.0] - 2026-11-13

Built for framework API 14.14.0, where a plugin ships the guardrail exceptions its own agents need.

- feat: **the researcher's guardrail exception comes with the install.** `plugin.json` declares `injection_classifier`, `bypass`, for `knowledge-researcher`. On 1.0 the guard withheld ordinary `web_search` results as planted instructions (scored 1.00), and the scan filed nothing. The exception had to be given by hand on Guardrails.
  - The wizard's **Guardrails and grants** step lists it, ticked, with its reason, and the Admin may untick it.
  - Uninstalling takes it back.
- Nothing else is declared, because nothing else was seen to fail:
  - `knowledge-editor` has no web access; its hand-made exception on the install was a precaution.
  - The two Experts read the web too, but have not run yet. If their web lookups are withheld, an Admin gives them the same exception, and the next version declares it.
  - `agent_grants` is empty: the Primaries ask the Experts and need none of the plugin's tools.
- change: `framework_api` is 14.14.0. An update now stays in the plugin's current Section.
- docs: troubleshooting says the researcher's exception is given on install.
- tests: 36.

## [1.3.0] - 2026-11-13

The operator: "Add a Knowledge and Industry agent and allow a command in Settings to link them to the Primary (default and the user's current Primary)", then "give those agents skills like creating topics, or running research on a kind of thing and storing it in its place in the vault, and refreshing the knowledge data".

- feat: **two Experts**, `industry-expert` (the market, competitors, partners, deals, the Gulf) and `knowledge-expert` (technologies and topics). Each:
  - is a chat Expert with web access and its own budget (40 tool calls);
  - carries a Primary routing line;
  - arrives linked to the install's Primary (`depends_on: ["default"]`).

  Two are enough. Each answers its own kind of question, and both carry the same four Skills.
- feat: **four Expert Skills**:
  - `knowledge-answer`: from the filed news and digests, then the web;
  - `knowledge-topics`: add, tune and drop a topic, only when asked;
  - `knowledge-research`: deep web research filed in the vault in its place, `<vault folder>/<category>/<topic> - research`, newest on top;
  - `knowledge-refresh`: one topic, one category, or everything, in the background.
- feat: **agent tools** for them: `knowledge_watch_digest`, `_topics`, `_add_topic`, `_remove_topic`, `_save_research`, `_research_notes` and `_refresh_now`.
- feat: **research notes**. A topic's drawer lists its research notes, each with **Open the note**. The plugin keeps each topic's research text in `data/KnowledgeWatch/research.json` too, so a second piece of research never depends on the vault index having seen the first.
- feat: **the Agents card** on the Settings tab. It shows both Experts and who may ask them, with **Link to the install's Primary** and **Link to my Primary**. The card adds the Primary to each Expert's `depends_on` through the app's own `PATCH /agents/{id}`, with the signed-in person's rights.
- refactor: starting a refresh moved into `backend/refresh.py`, shared by the screen and the Experts.
- fix: tuning a topic under another spelling of its name no longer renames it.
- docs: a Guide page on the Experts, and troubleshooting for withheld web results and an unlinked Primary.
- tests: 35.

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
