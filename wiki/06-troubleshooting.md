---
title: Troubleshooting
plugin: Knowledge Watch
order: 6
summary: What to check when no digest arrives or a scan files nothing.
screens: [/knowledge-watch, /settings/plugins/knowledge-watch]
---

**A scan failed with "Withheld: what web_search returned reads as an attempt to instruct you".** The install's guardrail that withholds planted instructions judged the search results to be one. The Knowledge Researcher only reads the web and files items, so an Admin may give it an exception: Admin Center › Guardrails, **Planted instructions are withheld**, bypass, agent `knowledge-researcher`. Then choose **Refresh now** on the **Settings** tab.

**An Expert says its web results were withheld.** Give that Expert the same guardrail exception as the researcher: Admin Center › Guardrails, **Planted instructions are withheld**, bypass, agent `industry-expert` or `knowledge-expert`.

**My Primary does not ask the Experts.** On the **Settings** tab, the **Agents** card shows who may ask each one. Choose **Link to my Primary**.

**A run is marked failed and names categories that were not filed.** A step ran out of its budget or failed. Its report is in Agent Activity. A category with very many topics can be split in two on the **Topics** tab.

**The digest says no news was filed this week.** Knowledge scan did not file anything. Open the **Settings** tab of [Knowledge Watch](app:/knowledge-watch): it says whether the scan is on, running, failed or stopped, and why. If its run reported `NO WEB SEARCH:`, the web search provider in Admin Center is missing or failing.

**No digest arrived.** Check that **Knowledge weekly** is on, and look at **Where the digest goes**. A refused send is kept on the run's record in Agent Activity.

**A category is never in the news.** Check that it is switched on under **Topics** and has topics. A topic that is too broad ("AI") or too narrow returns little; name the company, product or rule.

**The same story twice.** A story is filed once per link. The same story from two outlets can still appear twice; the researcher is told what is already filed and should skip it.

**Refresh now is greyed out.** Only a Pipeline that is switched on can be run, only one scan runs at a time, and starting one needs write access to the vault.

**The digest note is missing from the vault.** The digest's header on the screen says why, such as a folder outside the vault. Change **Vault folder** on the Settings page.
