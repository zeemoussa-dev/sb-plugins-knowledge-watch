---
title: Troubleshooting
plugin: Industry Watch
order: 5
summary: What to check when no digest arrives or a scan files nothing.
screens: [/industry-watch, /settings/plugins/industry-watch]
---

**The digest says no news was filed this week.** Industry scan did not file anything. Check on the [Settings page](app:/settings/plugins/industry-watch) that it is switched on and when it last ran. If its run reported `NO WEB SEARCH:`, the web search provider in Admin Center is missing or failing.

**No digest arrived.** Check that **Industry weekly** is on, and look at **Where the digest goes**. A refused send is kept on the run's record in Agent Activity.

**A category is never in the news.** Check that it is switched on under **Interests** and has topics. A topic that is too broad ("AI") or too narrow returns little; name the company, product or rule.

**The same story twice.** A story is filed once per link. The same story from two outlets can still appear twice; the researcher is told what is already filed and should skip it.

**Run now does nothing.** Only a Pipeline that is switched on can be run from here.

**The digest note is missing from the vault.** The digest's header on the screen says why, such as a folder outside the vault. Change **Vault folder** on the Settings page.
