"""This plugin's two Pipelines, as its screens see them.

Both ship switched off with a schedule (`ADR-131`). Firing one is
`api.runtime.run_cron_job` with the job its own record names; only a Pipeline that is
switched on is fired, because switching it on is the person's decision.
"""
from __future__ import annotations

SCAN = "knowledge-scan"
WEEKLY = "knowledge-weekly"
ALL = (SCAN, WEEKLY)


def state(api, pipeline_id: str) -> dict:
    try:
        found = api.pipelines.get(pipeline_id)
    except Exception as exc:
        return {"id": pipeline_id, "installed": False, "error": str(exc)}
    if not found:
        return {"id": pipeline_id, "installed": False}
    return {"installed": True, **found}


def fire(api, pipeline_id: str) -> tuple[bool, str]:
    found = state(api, pipeline_id)
    if not found.get("installed"):
        return False, "the Pipeline is not installed"
    if not found.get("cron_job_id"):
        return False, "the Pipeline has no job yet: give it a schedule on the Settings page"
    if not found.get("cron_enabled"):
        return False, "the Pipeline is switched off: switch it on on the Settings page"
    try:
        started = bool(api.runtime.run_cron_job(found["cron_job_id"], found.get("cron_profile_id")))
    except Exception as exc:
        return False, str(exc)
    return started, "" if started else "the scheduler did not start it (a run may be going already)"
