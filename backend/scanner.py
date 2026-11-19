"""The whole scan, one category at a time, where one category's failure stops nothing.

A Pipeline stops at its first failed step: on the install, one connection error in
category 1 or 3 left every category after it unscanned. So the Knowledge scan Pipeline
now has one step, which calls `knowledge_watch_start_scan`, and the plugin runs the
scan itself, on a thread of its own: one turn of the Knowledge Researcher per category
(`api.agents.run`), each with its own budget.

- A category whose turn fails, or ends without filing, is tried once more.
- A category that fails twice is recorded with why, and the scan goes on to the next.
- The run ends `done` when every category filed, otherwise `failed`, naming each
  category that did not file and why. The Settings tab shows it.

Code orders the work; the researcher judges every story, as before.
"""
from __future__ import annotations

import threading
import time

from . import interests, items, runs

RESEARCHER = "knowledge-researcher"
TIMEOUT = 900.0
ATTEMPTS = 2
RETRY_PAUSE_S = 30.0


class Refused(Exception):
    pass


def _instruction(category: dict) -> str:
    return (
        f"Follow the knowledge-scan Skill for ONE category, `{category['id']}` ({category['name']}): call "
        f"`knowledge_watch_scan_brief` with category `{category['id']}`, scan its topics with `web_search` and "
        "`read_page`, using each topic's own search terms, and file it with `knowledge_watch_save_items`, with an "
        "empty list when nothing new was found. If you cannot search, call `knowledge_watch_report_problem` first. "
        "Reply with one line: what was filed.")


def _filed_since(api, category_id: str, moment: str) -> bool:
    last = items.last_scan(api, category_id)
    return bool(last and str(last.get("at") or "") >= moment)


def scan_one(api, agents, category: dict, *, pause: float = RETRY_PAUSE_S) -> tuple[bool, str]:
    """`(filed, why not)` for one category, tried up to `ATTEMPTS` times."""
    why = ""
    for attempt in range(1, ATTEMPTS + 1):
        started = items.stamp()
        runs.touch(api, f"{category['name']}, attempt {attempt}")
        try:
            reply = agents.run(RESEARCHER, _instruction(category), timeout=TIMEOUT)
            if _filed_since(api, category["id"], started):
                return True, ""
            why = (" ".join(str(reply or "").split())[:300]) or "the researcher ended without filing"
        except Exception as exc:  # AgentRunRefused, a connection or read error: tried again
            why = f"{type(exc).__name__}: {exc}".strip(": ")[:300]
        if attempt < ATTEMPTS and pause:
            time.sleep(pause)
    return False, why


def run_all(api, agents, run_id: str, categories: list[dict], *, pause: float = RETRY_PAUSE_S) -> None:
    failed: dict[str, str] = {}
    for category in categories:
        ok, why = scan_one(api, agents, category, pause=pause)
        if not ok:
            failed[category["id"]] = why
            runs.category_failed(api, run_id, category["id"], why)
    runs.end_scan(api, run_id, failed, {c["id"]: c["name"] for c in categories})


def start(api, trigger: str = "schedule", *, by: str = "", wait: bool = False, pause: float = RETRY_PAUSE_S) -> dict:
    """Starts the whole scan in the background and answers at once. `wait` runs it in
    this thread instead, for tests."""
    agents = getattr(api, "agents", None)
    if agents is None or not hasattr(agents, "run"):
        raise Refused("This install cannot run a plugin agent: it needs a newer framework.")
    categories = interests.enabled(api)
    if not categories:
        raise Refused("No category is switched on: nothing to scan.")
    found = runs.open_run(api, "scan")
    if found and found.get("state") == "running":
        raise Refused("A scan is running already.")
    # A Run now asked for this run already ("requested"); a scheduled one starts here.
    run = found or runs.request(api, "scan", trigger, by=by)
    runs.begin(api, "scan", [], expected=[c["id"] for c in categories])
    runs.mark_background(api, run["id"])
    if wait:
        run_all(api, agents, run["id"], categories, pause=pause)
    else:
        threading.Thread(target=run_all, args=(api, agents, run["id"], categories),
                         kwargs={"pause": pause}, name=f"knowledge-watch-scan-{run['id']}", daemon=True).start()
    return {"started": True, "run": run["id"], "categories": [c["name"] for c in categories]}
