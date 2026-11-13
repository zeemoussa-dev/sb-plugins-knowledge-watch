---
title: The Industry and Knowledge Experts
plugin: Knowledge Watch
order: 5
summary: The two Experts you or your Primary ask, what each does, and how to link them to your Primary.
screens: [/knowledge-watch]
---

Knowledge Watch brings two Experts you can ask in chat, directly or through your Primary.

| Expert | Ask it about |
|---|---|
| **Industry Expert** (`industry-expert`) | The industry and the market: what a competitor, partner, hyperscaler or model provider did, deals, capacity and pricing, the Gulf and UAE market, and what this week's digest said. |
| **Knowledge Expert** (`knowledge-expert`) | A technology or topic to understand: what it is, how it works, where it stands, what changed lately, and the topics you follow. |

Two are enough. Your Primary picks between them by what you ask. Both have the same four Skills, so either one can do any of these.

| Skill | Say, for example | What it does |
|---|---|---|
| `knowledge-answer` | "What did Oracle announce in the Gulf this month?" | Answers from the news Knowledge Watch filed and its digests, each story with its source and date, and looks up anything newer on the web. |
| `knowledge-topics` | "Follow Nebius, its Middle East plans." "Leave share prices out of Oracle OCI." "Stop following du." | Adds a topic to the category it fits, tunes its search, or drops it. Only when you ask. |
| `knowledge-research` | "Research liquid cooling for GPU data centres." | Researches the topic in depth on the web and files the research in the vault, in its place: `Work/Knowledge Watch/<category>/<topic> - research`, newest on top. The note is listed on the topic's drawer, with **Open the note**. |
| `knowledge-refresh` | "Refresh the Gulf market." "Get me fresh news on MGX." "Refresh everything." | Starts a scan now, in the background, of one topic, one category, or everything. The **Settings** tab shows it running. |

Like the researcher, the Experts read the web. The install's guardrail that withholds planted instructions may need an exception for each, as it did for the researcher. See [Troubleshooting](wiki:troubleshooting).

## Linking them to your Primary

The **Agents** card on the [Knowledge Watch](app:/knowledge-watch) screen's **Settings** tab shows both Experts and who may ask them.

- **Link to the install's Primary** lets `default` ask them. They arrive linked to it.
- **Link to my Primary** lets the Primary you talk to ask them. If you have no Primary of your own, this is the install's Primary.

Linking needs the permission to manage agents. A refusal is shown on the card.
