# Industry Watch

A Second Brain OS plugin that keeps the CBO up to date on the technology and industry
landscape: AI models and providers, hyperscalers and cloud, sovereign AI and policy,
data centres, GPUs and power, the Gulf and UAE market, and the competitors and partners
that matter to Core42.

- **His interests.** He chooses the knowledge categories and the topics he is
  interested in inside each, with a note per topic on what he wants to know (the
  **Interests** tab). Six categories ship.
- **A scan** three times a week: a researcher agent searches the web for every topic
  and files dated, sourced items.
- **A weekly digest** on Sunday evening, written by an editor agent from those items,
  sent by chat and email (framework Pipeline delivery) and filed as a vault note.

The Guide in the Wiki (`wiki/`) is the user's manual; the design is
[`Documentation/DESIGN.md`](Documentation/DESIGN.md).

## What it ships

| Kind | What |
|---|---|
| Agents (background) | `industry-researcher`: the web, no vault. `industry-editor`: no web, no shell. |
| Skills | `industry-scan`, `industry-digest` |
| Pipelines | `industry-scan`: `CRON_TZ=Asia/Dubai 0 6 * * 0,2,4`. `industry-weekly`: `CRON_TZ=Asia/Dubai 0 18 * * 0`. Both ship **switched off**. |
| Agent tools | `industry_watch_scan_brief`, `_save_items`, `_digest_facts`, `_save_digest`, `_recent_items` |
| Screens | `/industry-watch` (Weekly digest, News, Interests), the Settings page `/settings/plugins/industry-watch` |
| Data | `data/IndustryWatch/interests.json`, `items.json`, `digests.json`; one note a week in `Work/Industry Watch/` |

It reads no other plugin: no Entities registry, no Strategic Entities list (operator's
decision, 2026-11-13).

## Developing

```bash
python -m pytest
```

with any Python 3.11+ that has `pytest` and `fastapi`, and before tagging, from the
framework's `src/backend`:

```bash
python scripts/check_plugin.py <this repo>
```
