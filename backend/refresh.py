"""Starting a scan outside the schedule, the same way from the screen and from an Expert.

One category, or one topic of it, is one turn of the Knowledge Researcher
(`api.agents.run`), on a thread of its own so the caller does not wait. Everything is
scanned by firing the Knowledge scan Pipeline, which is only done while it is on.
Both are recorded in the run log as they go.
"""
from __future__ import annotations

import threading

from . import interests, pipelines, runs

RESEARCHER = "knowledge-researcher"
TIMEOUT = 900.0


class Refused(Exception):
    """Why a refresh was not started, in words for the person; `status` is the HTTP code."""

    def __init__(self, text: str, status: int = 400):
        super().__init__(text)
        self.status = status


def one(api, category: str, topic: str = "", *, by: str = "") -> dict:
    if interests.get(api, category) is None:
        raise Refused(f"There is no category {category!r}.", 404)
    if topic and interests.find_topic(api, category, topic) is None:
        raise Refused(f"There is no topic {topic!r} in that category.", 404)
    if runs.open_run(api, "scan"):
        raise Refused("A scan is running already. Refresh again when it has finished.", 409)
    agents = getattr(api, "agents", None)
    if agents is None or not hasattr(agents, "run"):
        raise Refused("This install cannot run a plugin agent: it needs a newer framework.", 501)
    run = runs.request(api, "scan", "refresh", category=category, topic=topic, by=by)
    what = f"the topic `{topic}` of the category `{category}`" if topic else f"the category `{category}`"
    instruction = (
        f"Follow the knowledge-scan Skill for {what} only: call `knowledge_watch_scan_brief` with category "
        f"`{category}`" + (f" and topic `{topic}`" if topic else "") + ", scan it with `web_search` and "
        "`read_page`, and file it with `knowledge_watch_save_items`. If you cannot search, call "
        "`knowledge_watch_report_problem` first. Reply with one line.")

    def work():
        try:
            reply = agents.run(RESEARCHER, instruction, timeout=TIMEOUT)
            runs.finish(api, run["id"], reply)
        except Exception as exc:  # AgentRunRefused or a runtime failure: shown on the screen
            runs.finish(api, run["id"], "", failed=str(exc) or type(exc).__name__)

    threading.Thread(target=work, name=f"knowledge-watch-refresh-{run['id']}", daemon=True).start()
    return run


def everything(api, *, by: str = "") -> dict:
    if runs.open_run(api, "scan"):
        raise Refused("A scan is running already.", 409)
    # Recorded first: the Pipeline's step finds this run and carries it on.
    run = runs.request(api, "scan", "run now", by=by)
    started, why = pipelines.fire(api, pipelines.SCAN)
    if not started:
        runs.finish(api, run["id"], "", failed=f"the scan did not start: {why}")
        raise Refused(f"The scan did not start: {why}.", 409)
    return run
