"""The Knowledge Watch HTTP surface, mounted at `/plugins/knowledge-watch/`.

Routes are open to anyone signed in, so each change checks first: the CBO's interests
may be changed by anyone who may write the install's vault, the plugin-wide settings
and the Pipelines need `manage_plugins`. Reading follows the person's access to the
install's vault.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from . import digests, interests, items, pipelines, settings


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
    def get_items(category: str = "", days: int = 30, q: str = "") -> dict:
        _may_read(api)
        days = min(max(days, 1), items.KEEP_DAYS)
        names = {c["id"]: c["name"] for c in interests.read(api)}
        found = items.recent(api, category=category, days=days, query=q, limit=300)
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
        """What the main screen shows at the top: the last scans, the next runs."""
        _may_read(api)
        enabled = interests.enabled(api)
        last = {}
        for scan in items.scans(api):
            last.setdefault(scan.get("category"), scan)
        return {"categories": len(enabled), "topics": sum(len(c["topics"]) for c in enabled),
                "items_week": len(items.recent(api, days=7, limit=10000)),
                "last_scans": [{"category": c["name"], **(last.get(c["id"]) or {})} for c in enabled],
                "pipelines": [pipelines.state(api, pid) for pid in pipelines.ALL]}

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
        _require(api, "manage_plugins")
        if pipeline_id not in pipelines.ALL:
            raise HTTPException(status_code=404, detail=f"no Pipeline {pipeline_id!r} in this plugin")
        started, why = pipelines.fire(api, pipeline_id)
        return {"started": started, "note": why}

    return router
