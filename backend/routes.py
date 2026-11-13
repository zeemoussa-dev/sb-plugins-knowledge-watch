"""The Knowledge Watch HTTP surface, mounted at `/plugins/knowledge-watch/`.

Routes are open to anyone signed in, so each change checks first: the CBO's interests
may be changed by anyone who may write the install's vault, the plugin-wide settings
and the Pipelines need `manage_plugins`. Reading follows the person's access to the
install's vault.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from . import digests, interests, items, pipelines, refresh, research, runs, settings


def _caller(api) -> dict | None:
    people = getattr(api, "people", None)
    try:
        return people.caller() if people is not None else None
    except Exception:
        return None


def _has(api, capability: str) -> bool:
    caller = _caller(api)
    return bool(caller and not caller.get("disabled") and capability in (caller.get("capabilities") or []))


def _require(api, capability: str) -> None:
    if not _has(api, capability):
        raise HTTPException(status_code=403, detail=f"This needs the {capability} capability.")


def _vault_check(api, name: str) -> bool:
    check = getattr(getattr(api, "vault", None), name, None)
    if check is None:
        return True
    try:
        return bool(check())
    except Exception:
        return True


def _may_read(api) -> None:
    if not _vault_check(api, "may_read"):
        raise HTTPException(status_code=403, detail="You are not a member of this install's vault.")


def _may_change_interests(api) -> None:
    caller = _caller(api)
    if caller is None or caller.get("disabled"):
        raise HTTPException(status_code=403, detail="Sign in to change the interests.")
    if not (_has(api, "manage_plugins") or _vault_check(api, "may_write")):
        raise HTTPException(status_code=403, detail="Changing the interests needs write access to the vault.")


# Starting a run the Admin already switched on is the CBO's own: the same people who
# may change his interests may ask for a refresh.
_may_run = _may_change_interests


def _may_run_quietly(api) -> bool:
    try:
        _may_run(api)
        return True
    except HTTPException:
        return False


def _pipeline_view(api, pipeline_id: str, open_run: dict | None, last_run: dict | None) -> dict:
    """A Pipeline as the screen shows it: one `state` and, when something is wrong, why."""
    found = pipelines.state(api, pipeline_id)
    if not found.get("installed"):
        return {**found, "state": "missing", "why": "The Pipeline is not on this install: reinstall the plugin."}
    if not found.get("cron_job_id"):
        return {**found, "state": "no job", "why": "It has no job yet: an Admin gives it a schedule."}
    if open_run:
        return {**found, "state": "running", "why": ""}
    if last_run and last_run["state"] in ("failed", "stopped"):
        why = last_run.get("problem") or ("It stopped without finishing. Its report is in Agent Activity."
                                          if last_run["state"] == "stopped" else "")
        return {**found, "state": last_run["state"], "why": why}
    if found.get("last_status") == "failed":
        return {**found, "state": "failed",
                "why": "The last run failed before the agent could say why. Its report is in Agent Activity."}
    if not found.get("cron_enabled"):
        return {**found, "state": "off", "why": "It is switched off, so it does not run on its schedule."}
    return {**found, "state": "on", "why": ""}


def build_router(api) -> APIRouter:
    router = APIRouter()

    # -- the CBO's interests: knowledge categories and topics ----------------------

    @router.get("/interests")
    def get_interests() -> dict:
        _may_read(api)
        return {"categories": interests.read(api), "limits": {"categories": interests.MAX_CATEGORIES,
                                                              "topics": interests.MAX_TOPICS}}

    @router.put("/interests")
    def put_interests(payload: dict = Body(...)) -> dict:
        _may_change_interests(api)
        try:
            return {"categories": interests.save(api, (payload or {}).get("categories"))}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/interests/reset")
    def reset_interests() -> dict:
        _may_change_interests(api)
        return {"categories": interests.reset(api)}

    # -- the news and the digests --------------------------------------------------

    @router.get("/items")
    def get_items(category: str = "", topic: str = "", days: int = 30, q: str = "") -> dict:
        _may_read(api)
        days = min(max(days, 1), items.KEEP_DAYS)
        names = {c["id"]: c["name"] for c in interests.read(api)}
        found = items.recent(api, category=category, topic=topic, days=days, query=q, limit=300)
        return {"items": [{**i, "category_name": names.get(i.get("category"), i.get("category"))} for i in found],
                "categories": [{"id": k, "name": v} for k, v in names.items()]}

    @router.get("/digests")
    def get_digests() -> list[dict]:
        _may_read(api)
        return digests.listed(api)

    @router.get("/digests/{digest_id}")
    def get_digest(digest_id: str) -> dict:
        _may_read(api)
        found = digests.read(api, digest_id)
        if found is None:
            raise HTTPException(status_code=404, detail=f"no digest {digest_id!r}")
        return found

    @router.get("/status")
    def status() -> dict:
        """Everything the screen says about how it is doing: the figures, each Pipeline's
        state and why, the run going now, the recent runs, and each category's last scan."""
        _may_read(api)
        enabled = interests.enabled(api)
        last = {}
        for scan in items.scans(api):
            last.setdefault(scan.get("category"), scan)
        history = runs.listed(api)
        views = []
        for pid, kind in ((pipelines.SCAN, "scan"), (pipelines.WEEKLY, "digest")):
            open_run = next((r for r in history if r["kind"] == kind and r["state"] in ("running", "requested")), None)
            last_run = next((r for r in history if r["kind"] == kind and r.get("trigger") != "refresh"), None)
            views.append({**_pipeline_view(api, pid, open_run, last_run), "kind": kind, "run": open_run})
        names = {c["id"]: c["name"] for c in interests.read(api)}
        return {"categories": len(enabled), "topics": sum(len(c["topics"]) for c in enabled),
                "items_week": len(items.recent(api, days=7, limit=10000)),
                "last_scans": [{"category": c["name"], "category_id": c["id"], **(last.get(c["id"]) or {})}
                               for c in enabled],
                "pipelines": views,
                "runs": [{**r, "category_names": [names.get(c, c) for c in r.get("categories") or []]}
                         for r in history[:20]],
                "may_run": _may_run_quietly(api), "may_admin": _has(api, "manage_plugins")}

    @router.post("/refresh")
    def refresh_route(payload: dict = Body(...)) -> dict:
        """Scans one category, or one topic of it, now, outside the schedule: one turn of
        the researcher, in the background. The run is on the status as it goes."""
        _may_run(api)
        caller = _caller(api) or {}
        try:
            run = refresh.one(api, str((payload or {}).get("category") or "").strip(),
                              str((payload or {}).get("topic") or "").strip(), by=str(caller.get("name") or ""))
        except refresh.Refused as refused:
            raise HTTPException(status_code=refused.status, detail=str(refused)) from refused
        return {"started": True, "run": run}

    @router.get("/research")
    def research_list(category: str = "", topic: str = "") -> list[dict]:
        _may_read(api)
        return research.listed(api, category=category, topic=topic)[:50]

    # -- the plugin-wide Settings page -------------------------------------------

    @router.get("/settings")
    def get_settings() -> dict:
        _may_read(api)
        return {"values": settings.all_values(api), "defaults": settings.DEFAULTS,
                "pipelines": [pipelines.state(api, pid) for pid in pipelines.ALL]}

    @router.put("/settings")
    def put_settings(payload: dict = Body(...)) -> dict:
        _require(api, "manage_plugins")
        refused = {}
        for key, value in (payload or {}).items():
            if key not in settings.DEFAULTS:
                refused[key] = "not a setting of this plugin"
                continue
            # The default as written is saved as empty, so a later change to the
            # shipped default reaches this install too.
            text = "" if str(value).strip() == settings.DEFAULTS[key] else str(value)
            try:
                api.config.set(key, text)
            except Exception as exc:
                refused[key] = str(exc)
        return {"values": settings.all_values(api), "refused": refused}

    @router.put("/pipelines/{pipeline_id}")
    def change_pipeline(pipeline_id: str, payload: dict = Body(...)) -> dict:
        _require(api, "manage_plugins")
        if pipeline_id not in pipelines.ALL:
            raise HTTPException(status_code=404, detail=f"no Pipeline {pipeline_id!r} in this plugin")
        try:
            if str((payload or {}).get("schedule") or "").strip():
                api.pipelines.set_schedule(pipeline_id, str(payload["schedule"]).strip())
            if "enabled" in (payload or {}):
                api.pipelines.set_enabled(pipeline_id, bool(payload["enabled"]))
        except Exception as exc:  # PipelineChangeRefused, matched by being any refusal
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return pipelines.state(api, pipeline_id)

    @router.post("/pipelines/{pipeline_id}/run")
    def run_pipeline(pipeline_id: str) -> dict:
        _may_run(api)
        if pipeline_id not in pipelines.ALL:
            raise HTTPException(status_code=404, detail=f"no Pipeline {pipeline_id!r} in this plugin")
        kind = "scan" if pipeline_id == pipelines.SCAN else "digest"
        if runs.open_run(api, kind):
            return {"started": False, "note": "it is running already"}
        started, why = pipelines.fire(api, pipeline_id)
        if started:
            caller = _caller(api) or {}
            runs.request(api, kind, "run now", by=str(caller.get("name") or ""))
        return {"started": started, "note": why}

    return router
