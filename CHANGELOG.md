# CHANGELOG

All notable changes to the Knowledge Watch plugin.

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
