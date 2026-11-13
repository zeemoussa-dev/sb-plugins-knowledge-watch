---
title: Pipelines and delivery
plugin: Knowledge Watch
order: 4
summary: What the two Pipelines do, when they run, and how the digest reaches you.
screens: [/settings/plugins/knowledge-watch]
---

| Pipeline | When (Dubai) | What it does |
|---|---|---|
| **Knowledge scan** | Sunday, Tuesday, Thursday 06:00 (`CRON_TZ=Asia/Dubai 0 6 * * 0,2,4`) | The Knowledge Researcher calls `knowledge_watch_scan_brief`, searches the web for each category and topic, reads each page, and files items with `knowledge_watch_save_items`. It sends nothing. |
| **Knowledge weekly** | Sunday 18:00 (`CRON_TZ=Asia/Dubai 0 18 * * 0`) | The Knowledge Editor calls `knowledge_watch_digest_facts`, writes the digest, and files it with `knowledge_watch_save_digest`. The digest goes on the screen and into the vault, and its last reply is the digest you receive. |

Both arrive **switched off**. Switch them on, change a schedule, or **Run now** on the Settings page.

## Delivery

The framework sends the weekly Pipeline's result at the end of its run. No agent sends it, and no agent picks who gets it.

- **Send it to**: a person, on their usual chat or on the one you pick.
- **Also email it**: from a mailbox you may send from, to the people you tick and the addresses you type.

The email is laid out from the digest's own headings: each `##` section becomes a band.

The scan's report (one line per category) stays in the run history. It is not sent.
