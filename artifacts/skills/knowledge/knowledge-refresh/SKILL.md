---
name: knowledge-refresh
description: Refreshes the Knowledge Watch data now, outside its schedule: one topic, one category, or the whole scan, run in the background by the Knowledge Researcher. Used by the Industry Expert and the Knowledge Expert when the CBO asks for fresh news on something, or to update everything.
version: 1.0.0
author: knowledge-watch
license: MIT
platforms: [linux, windows]
metadata:
  sbos:
    tags: [refresh, scan, news]
---

# Knowledge refresh

## Steps

1. Work out what to refresh: one topic ("refresh Oracle OCI"), one category ("refresh the
   Gulf market"), or everything ("refresh all"). `knowledge_watch_topics` gives the
   category ids and topic names.
2. Call `knowledge_watch_refresh_now` with `category` and `topic`, `category` alone, or
   neither for everything.
3. It answers whether it started. If it did, say that the scan runs in the background
   and that its items appear on Knowledge Watch, and in your answers, when it is done
   (a topic takes a few minutes). If not, say why, in its words: a scan already running,
   or the Knowledge scan switched off.
4. Never wait for it in a loop. Answer from what is filed now if he asked a question too.
