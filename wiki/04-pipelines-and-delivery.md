---
title: Pipelines and delivery
plugin: Knowledge Watch
order: 4
summary: What the two Pipelines do, how to see whether they are running or why they failed, and how the digest reaches you.
screens: [/knowledge-watch, /settings/plugins/knowledge-watch]
---

| Pipeline | When (Dubai) | What it does |
|---|---|---|
| **Knowledge scan** | Sunday, Tuesday, Thursday 06:00 (`CRON_TZ=Asia/Dubai 0 6 * * 0,2,4`) | The Knowledge Researcher calls `knowledge_watch_scan_brief`, searches the web for each category and topic, reads each page, and files items with `knowledge_watch_save_items`. It sends nothing. |
| **Knowledge weekly** | Sunday 18:00 (`CRON_TZ=Asia/Dubai 0 18 * * 0`) | The Knowledge Editor calls `knowledge_watch_digest_facts`, writes the digest, and files it with `knowledge_watch_save_digest`. The digest goes on the screen and into the vault, and its last reply is the digest you receive. |

Both arrive **switched off**. An Admin switches them on, and changes a schedule, on the Admin settings page.

## The Settings tab

The **Settings** tab of the [Knowledge Watch screen](app:/knowledge-watch) shows how they are doing, for anyone who reads it:

| State | Means |
|---|---|
| **On** | It runs on its schedule. |
| **Running** | A run is going now, with how many categories it has filed so far. The screen updates by itself. |
| **Failed** | The last run failed. The card says why, in the words of the tool that failed. |
| **Stopped** | A run started but never finished, after 45 minutes. Its report is in Agent Activity. |
| **Off** | It is switched off and does not run on its schedule. |

- **Refresh now** starts a scan of everything, and **Write the digest now** writes the digest. Each needs its Pipeline to be on.
- **Each category** lists when it was last scanned, what it filed and refused, and what was searched. **Refresh** scans that category now.
- **Recent runs** lists the last runs, newest first: scheduled, Run now or a refresh, their state, and what happened.

An Admin also sees a switch to turn each Pipeline on or off there.

## Delivery

The framework sends the weekly Pipeline's result at the end of its run. No agent sends it, and no agent picks who gets it.

- **Send it to**: a person, on their usual chat or on the one you pick.
- **Also email it**: from a mailbox you may send from, to the people you tick and the addresses you type.

The email is laid out from the digest's own headings: each `##` section becomes a band.

The scan's report (one line per category) stays in the run history. It is not sent.
