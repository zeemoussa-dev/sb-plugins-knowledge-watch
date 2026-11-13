"""What the plugin knows about its own runs: started, how far it got, finished, failed.

The framework tells a plugin only a Pipeline's last status (completed or failed) and
its last and next run, not whether one is running now nor why it failed. So each
scan and each digest is recorded here as its agent works, through the plugin's own
tools: `scan_brief` opens a scan, each `save_items` marks its category filed, and
`report_problem` records why it could not go on. A digest opens at `digest_facts`
and closes at `save_digest`. A run left open longer than `STALE_MINUTES` is shown as
stopped without finishing.

Stored in `data/KnowledgeWatch/runs.json`, newest first.
"""
from __future__ import annotations

import json
import uuid
from datetime import timedelta

from . import items

STORE = "data/KnowledgeWatch/runs.json"
KEEP = 60
STALE_MINUTES = 45
KINDS = ("scan", "digest")


def _read(api) -> list[dict]:
    raw = api.data.read_text(STORE)
    try:
        found = json.loads(raw) if raw else {}
    except ValueError:
        found = {}
    return list(found.get("runs") or [])


def _write(api, rows: list[dict]) -> None:
    api.data.write_text(STORE, json.dumps({"runs": rows[:KEEP]}, ensure_ascii=False, indent=1))


def _stale(run: dict) -> bool:
    started = items.parse(run.get("started_at"))
    return bool(started and items.now() - started > timedelta(minutes=STALE_MINUTES))


def state_of(run: dict) -> str:
    """`requested`, `running`, `done`, `failed`, or `stopped` (left open too long)."""
    state = run.get("state") or "running"
    if state in ("running", "requested") and _stale(run):
        return "stopped"
    return state


def listed(api) -> list[dict]:
    return [{**run, "state": state_of(run)} for run in _read(api)]


def open_run(api, kind: str) -> dict | None:
    return next((run for run in listed(api) if run.get("kind") == kind and run["state"] in ("running", "requested")),
                None)


def request(api, kind: str, trigger: str, *, category: str = "", topic: str = "", by: str = "") -> dict:
    """A run someone asked for before its agent has started: Run now, or a refresh."""
    run = {"id": uuid.uuid4().hex[:10], "kind": kind, "trigger": trigger, "state": "requested",
           "requested_at": items.stamp(), "started_at": items.stamp(), "finished_at": "",
           "category": category, "topic": topic, "by": by, "categories": [], "filed": {}, "refused": {},
           "problem": "", "reply": ""}
    _write(api, [run] + _read(api))
    return run


def _update(api, run_id: str, change) -> dict | None:
    rows = _read(api)
    for row in rows:
        if row.get("id") == run_id:
            change(row)
            _write(api, rows)
            return row
    return None


def begin(api, kind: str, categories: list[str]) -> dict:
    """The agent has started: the run someone asked for, or a scheduled one."""
    found = open_run(api, kind)
    if found is None:
        found = request(api, kind, "schedule")

    def start(row):
        if row["state"] == "requested":
            row["state"] = "running"
            row["started_at"] = items.stamp()
        row["categories"] = sorted(set(row.get("categories") or []) | set(categories))
    return _update(api, found["id"], start) or found


def filed(api, category: str, saved: int, refused: int) -> None:
    found = open_run(api, "scan")
    if found is None:
        return

    def mark(row):
        row["filed"][category] = row["filed"].get(category, 0) + saved
        row["refused"][category] = row["refused"].get(category, 0) + refused
        if row.get("categories") and set(row["categories"]) <= set(row["filed"]):
            row["state"] = "done"
            row["finished_at"] = items.stamp()
    _update(api, found["id"], mark)


def digest_done(api) -> None:
    found = open_run(api, "digest")
    if found is not None:
        _update(api, found["id"], lambda row: row.update(state="done", finished_at=items.stamp()))


def problem(api, kind: str, text: str) -> dict:
    found = open_run(api, kind) or begin(api, kind, [])

    def fail(row):
        row["state"] = "failed"
        row["problem"] = " ".join(str(text or "").split())[:600] or "the agent could not go on"
        row["finished_at"] = items.stamp()
    return _update(api, found["id"], fail) or found


def finish(api, run_id: str, reply: str, *, failed: str = "") -> None:
    """A refresh's agent turn has returned: done unless its tools already said otherwise."""
    def close(row):
        row["reply"] = " ".join(str(reply or "").split())[:600]
        if failed:
            row["state"] = "failed"
            row["problem"] = failed[:600]
        elif row["state"] in ("running", "requested"):
            row["state"] = "done"
        row["finished_at"] = row.get("finished_at") or items.stamp()
    _update(api, run_id, close)
