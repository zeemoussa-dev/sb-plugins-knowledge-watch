---
name: industry-digest
description: Writes the CBO's weekly Industry Watch digest from the news items filed since the last one -- headlines, one section per knowledge category, and what to watch next week -- and files it on the screen and in the vault. Use in the Industry weekly Pipeline.
version: 1.0.0
author: industry-watch
license: MIT
platforms: [linux, windows]
metadata:
  sbos:
    tags: [industry, news, digest, weekly]
---

# Industry digest

## Steps

1. Call `industry_watch_digest_facts`. It answers the `week`, the `sections` in order
   (`Headlines`, one per knowledge category, `Watch next week`), the house `prompt`,
   and each category's `items` since the last digest.
2. If `item_count` is 0, file a digest whose `Headlines` is one line: "No news was
   filed this week. The Industry scan Pipeline may be off, or web search may be
   failing: see Industry Watch." Leave the other sections out.
3. Otherwise write each section, following the house prompt:
   - **Headlines**: the three to five stories that matter most this week, across all
     categories, most important first, each in one sentence with its source.
   - **One section per category**: its stories, the high ones first, each one or two
     sentences ending with the source as a markdown link and its date, e.g.
     `([Reuters](https://...), 12 Nov)`. Close with one line *What it means for
     Core42 (inference):* when there is something to say. A category with no items
     gets one line: "Nothing material this week."
   - **Watch next week**: dates, launches, decisions and follow-ups the items point to.
     Leave it out when there are none.
4. Call `industry_watch_save_digest` with `sections` (each name exactly as listed, to
   its markdown) and `sources` (the links you cited).

## Rules

- Every story is an item the tool gave you. Never add one from memory.
- Names, numbers and dates exactly as the item gives them.
- Inference is marked as inference.
- You send nothing, and you never call `send_mail`. The Pipeline delivers your last
  reply to the people and addresses set on the plugin's Settings page.

## How the run ends

Your last reply **is the digest the CBO receives**, on his chat or by mail. Reply with
exactly the `markdown` that `industry_watch_save_digest` answered: its first line
`Industry Watch, week to <date>`, then each section as `## <name>`. Nothing else: no
list of steps, no "filed", no tool names.
