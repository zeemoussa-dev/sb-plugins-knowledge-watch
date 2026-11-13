---
name: knowledge-topics
description: Creates, tunes and drops the topics the CBO follows on Knowledge Watch, in the knowledge category each belongs to, when he asks: follow X, search X this way, look at this site for X, leave Y out, stop following X. Used by the Industry Expert and the Knowledge Expert.
version: 1.0.0
author: knowledge-watch
license: MIT
platforms: [linux, windows]
metadata:
  sbos:
    tags: [topics, interests, knowledge]
---

# Knowledge topics

## Steps

1. Call `knowledge_watch_topics`: his categories, each with its id and its topics, and
   how each topic's search is tuned.
2. Do what he asked:
   - **Follow something new**: pick the category it fits best and call
     `knowledge_watch_add_topic` with `category`, `name` (as the press names it) and,
     from what he said, `notes` (what he wants to know about it). If he named searches,
     sites or things to leave out, pass `search_terms`, `sources` (domains) and
     `leave_out`.
   - **Tune a topic**: call `knowledge_watch_add_topic` with its exact `name` and only
     what changes.
   - **Stop following one**: call `knowledge_watch_remove_topic`.
   - Nothing fits any category: say so and name the closest one; he can add a category
     on the Knowledge Watch screen's Topics tab.
3. Say what you set and where, in one or two lines. A new topic is scanned from the
   next scan; offer to refresh it now (knowledge-refresh) or research it now
   (knowledge-research).

## Rules

- Only what he asked. Never add, change or drop a topic on your own judgement.
- One topic per thing to follow: "OpenAI and Anthropic" is two topics.
