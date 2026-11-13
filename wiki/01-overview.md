---
title: Industry Watch overview
plugin: Industry Watch
order: 1
summary: What Industry Watch is for, what it brings to your install, and what it needs.
screens: [/industry-watch]
---

Industry Watch keeps you up to date on the technology and industry landscape that matters to Core42. That means AI models and providers, hyperscalers and cloud, sovereign AI and policy, data centres, GPUs and power, the Gulf and UAE technology market, and the competitors and partners you name.

You choose what it follows. Each **knowledge category** is a beat, with the **topics** you are interested in inside it, and each topic can carry a note on what you want to know about it. See [Interests and news](wiki:interests-and-news).

## What you receive

- **A weekly digest**, every Sunday at 18:00 Dubai. It opens with the headlines, has one section per category, and ends with what to watch next week. Every story carries its source and date. Where the editor says what a story means for Core42, that is marked as its inference.
- The digest is sent to you by chat and by email, wherever the Settings page says.
- It is also filed as a note in the vault (`Work/Industry Watch/`), so other agents can find it through search.

There are no daily alerts. Between digests, the **News** tab shows every item as it is filed.

## What it brings

| Part | What it is |
|---|---|
| The **Industry Watch** screen | Three tabs: **Weekly digest**, **News** and **Interests**. |
| Two background agents | The **Industry Researcher** scans the web and files items; it cannot read the vault. The **Industry Editor** writes the digest from those items; it has no web access. Nobody chats with either. |
| Two Pipelines | **Industry scan** runs Sunday, Tuesday and Thursday at 06:00 Dubai. **Industry weekly** runs Sunday at 18:00 Dubai. Both arrive switched off. See [Pipelines and delivery](wiki:pipelines-and-delivery). |
| Two Skills | `industry-scan` and `industry-digest`. |
| A Settings page | The Pipelines, where the digest goes, sources and prompts. |

## What it needs

- A **web search provider** in Admin Center (Tavily on this install). Without one the scan files nothing and says why.
- A mailbox you may send from, if the digest is also to be emailed.

Industry Watch reads no other plugin. It does not use the Entities registry or the Strategic Entities list. The companies it watches are the topics you put under **Competitors and partners**.
