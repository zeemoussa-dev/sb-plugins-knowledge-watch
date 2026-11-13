"""Registration, the interests, filing items, the digest, the routes' permissions, and
what the plugin ships for the framework to deploy."""
from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

from backend import digests, interests, items, pipelines, runs, settings
from tests.conftest import call, route

REPO = Path(__file__).resolve().parent.parent
TOOLS = {"scan_brief", "save_items", "digest_facts", "save_digest", "recent_items", "report_problem"}


def story(n: int, **extra) -> dict:
    return {"url": f"https://www.reuters.com/tech/story-{n}/?utm_source=x", "title": f"Story {n}",
            "summary": f"Something happened, {n}.", "published": "2026-11-12", "topic": "oracle oci",
            "why_it_matters": "Core42 competes here.", "importance": "high", "companies": ["Oracle"], **extra}


# -- registration -------------------------------------------------------------

def test_register_wires_everything_through_the_plugin_api(registered):
    assert set(registered.tools) == TOOLS
    assert len(registered.routers) == 1
    assert {interests.STORE, items.STORE, digests.STORE, runs.STORE} <= set(registered.registered)


# -- the interests ------------------------------------------------------------

def test_an_install_that_never_saved_has_the_shipped_categories(api):
    found = interests.read(api)
    assert [c["id"] for c in found] == ["models", "cloud", "sovereign", "infrastructure", "gulf", "watchlist"]
    assert all(c["enabled"] and c["topics"] for c in found)


def test_categories_and_topics_are_the_cbos_to_change(registered):
    api = registered
    saved = route(api, "/interests", "PUT")({"categories": [
        {"name": "Quantum computing", "about": "where it meets HPC",
         "topics": [{"name": "IBM", "notes": "roadmap"}, "IBM", {"name": " "}, "Pasqal"]},
        {"name": "Quantum computing", "enabled": False, "topics": ["Rigetti"]},
    ]})["categories"]
    assert [c["id"] for c in saved] == ["quantum-computing", "quantum-computing-2"]
    assert [t["name"] for t in saved[0]["topics"]] == ["IBM", "Pasqal"], "duplicates and blanks are dropped"
    assert saved[0]["topics"][0]["notes"] == "roadmap"
    assert [c["id"] for c in interests.enabled(api)] == ["quantum-computing"], "a category switched off is not scanned"
    assert route(api, "/interests/reset", "POST")()["categories"][0]["id"] == "models"


def test_a_category_needs_a_name(registered):
    with pytest.raises(HTTPException) as refused:
        route(registered, "/interests", "PUT")({"categories": [{"name": "", "topics": ["x"]}]})
    assert refused.value.status_code == 400


def test_interests_need_write_access_to_the_vault(registered):
    api = registered
    api.caller = {"id": "u2", "disabled": False, "capabilities": []}
    api.writable = False
    with pytest.raises(HTTPException) as refused:
        route(api, "/interests", "PUT")({"categories": []})
    assert refused.value.status_code == 403
    api.writable = True
    assert route(api, "/interests", "PUT")({"categories": []})["categories"] == []


# -- scanning -----------------------------------------------------------------

def test_the_scan_brief_lists_each_category_with_its_topics_and_prompt(registered):
    brief = call(registered, "scan_brief")
    cloud = next(c for c in brief["categories"] if c["category"] == "cloud")
    assert "Oracle OCI" in cloud["prompt"] and "Hyperscalers and cloud" in cloud["prompt"]
    assert cloud["already_filed"] == [] and brief["max_items_per_category"] == 6
    assert "reuters.com" in brief["preferred_sources"]
    assert [c["category"] for c in call(registered, "scan_brief", category="gulf")["categories"]] == ["gulf"]


def test_filing_items_dedupes_by_link_and_refuses_what_cannot_be_kept(registered):
    api = registered
    api.settings["blocked_domains"] = "spam.example"
    answer = call(api, "save_items", category="cloud", queries=["oracle cloud uae"], items=[
        story(1), story(1, title="Same story, other tracking"), {"url": "", "title": "x", "summary": "y"},
        {"url": "https://news.spam.example/a", "title": "Spam", "summary": "s"}])
    assert answer["saved"] == 1
    assert sorted(r["why"] for r in answer["refused"]) == ["already filed", "news.spam.example is a blocked source",
                                                            "no link"]
    filed = items.all_items(api)[0]
    assert filed["url"] == "https://reuters.com/tech/story-1" and filed["topic"] == "Oracle OCI"
    assert filed["source"] == "reuters.com" and filed["importance"] == "high"
    assert call(api, "scan_brief", category="cloud")["categories"][0]["already_filed"][0]["title"] == "Story 1"
    assert items.last_scan(api, "cloud")["queries"] == ["oracle cloud uae"]


def test_a_scan_files_at_most_the_limit(registered):
    registered.settings["max_items"] = "2"
    answer = call(registered, "save_items", category="cloud", items=[story(n) for n in range(4)])
    assert answer["saved"] == 2 and len(answer["refused"]) == 2


def test_an_unknown_category_is_refused(registered):
    with pytest.raises(ValueError, match="not a category"):
        call(registered, "save_items", category="nope", items=[])


def test_the_next_scan_looks_back_to_the_last_one(registered):
    api = registered
    assert items.since(api, "cloud") == (items.now() - timedelta(days=7)).date().isoformat()
    call(api, "save_items", category="cloud", items=[])
    assert items.since(api, "cloud") == (items.now() - timedelta(days=1)).date().isoformat()


# -- the digest -----------------------------------------------------------------

def test_the_digest_round_trip(registered, tmp_path):
    api = registered
    call(api, "save_items", category="cloud", items=[story(1)])
    facts = call(api, "digest_facts")
    assert facts["sections"][0] == "Headlines" and facts["sections"][-1] == "Watch next week"
    assert "Hyperscalers and cloud" in facts["sections"] and facts["item_count"] == 1
    cloud = next(c for c in facts["categories"] if c["category"] == "Hyperscalers and cloud")
    assert cloud["items"][0]["title"] == "Story 1"

    with pytest.raises(ValueError, match="not a section"):
        call(api, "save_digest", sections={"Headlines": "x", "Sports": "y"})
    with pytest.raises(ValueError, match="Headlines"):
        call(api, "save_digest", sections={"Hyperscalers and cloud": "y"})

    saved = call(api, "save_digest", sections={"Headlines": "- **Oracle** opens a region.",
                                               "Hyperscalers and cloud": "Oracle opened it."},
                 sources=["https://reuters.com/tech/story-1"])
    assert saved["markdown"].startswith(f"Knowledge Watch, week to {facts['week']}\n\n## Headlines")
    assert "## Hyperscalers and cloud" in saved["markdown"] and "## Watch next week" not in saved["markdown"]
    note = tmp_path / "Work" / "Knowledge Watch" / f"Knowledge Watch {facts['week']}.md"
    assert note.is_file() and "Oracle opened it." in note.read_text(encoding="utf-8")
    listed = route(api, "/digests")()
    assert listed[0]["headline"] == "Oracle opens a region." and listed[0]["items"] == 1
    assert route(api, "/digests/{digest_id}")(listed[0]["id"])["sections"]["Headlines"]
    assert call(api, "digest_facts")["item_count"] == 0, "the next digest starts where this one ended"


def test_a_digest_is_filed_even_when_the_vault_refuses_the_note(registered):
    api = registered

    def refuse(*args, **kwargs):
        raise PermissionError("hidden folder")
    api.vault.write_note = refuse
    saved = call(api, "save_digest", sections={"Headlines": "Quiet week."})
    assert saved["saved"] and saved["note"].startswith("not filed in the vault")


def test_recent_items_answers_a_question(registered):
    api = registered
    call(api, "save_items", category="cloud", items=[story(1), story(2, title="AWS region", companies=["AWS"])])
    found = call(api, "recent_items", query="aws")
    assert [i["title"] for i in found["items"]] == ["AWS region"]


# -- the routes -----------------------------------------------------------------

def test_settings_need_manage_plugins_and_save_the_default_as_empty(registered):
    api = registered
    answer = route(api, "/settings", "PUT")({"horizon_days": "10", "max_items": settings.DEFAULTS["max_items"],
                                             "nope": "x"})
    assert api.settings == {"horizon_days": "10", "max_items": ""}
    assert answer["refused"] == {"nope": "not a setting of this plugin"}
    api.caller = {"id": "u2", "disabled": False, "capabilities": []}
    with pytest.raises(HTTPException):
        route(api, "/settings", "PUT")({"horizon_days": "3"})


def test_running_a_pipeline_needs_it_on(registered):
    api = registered
    assert route(api, "/pipelines/{pipeline_id}/run", "POST")("knowledge-scan")["started"] is False
    api.switch_on("knowledge-scan")
    assert route(api, "/pipelines/{pipeline_id}/run", "POST")("knowledge-scan")["started"] is True
    assert api.jobs == [("job-knowledge-scan", None)]


def test_status_and_items_routes(registered):
    api = registered
    call(api, "save_items", category="gulf", items=[story(1, topic="MGX")])
    status = route(api, "/status")()
    assert status["items_week"] == 1 and status["categories"] == 6
    assert [p["id"] for p in status["pipelines"]] == list(pipelines.ALL)
    found = route(api, "/items")(category="gulf", days=30, q="")
    assert found["items"][0]["category_name"] == "Gulf and UAE technology market"


# -- what ships -----------------------------------------------------------------

def test_the_shipped_artifacts_agree_with_each_other():
    manifest = json.loads((REPO / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["id"] == "knowledge-watch" and manifest["requires"] == [] and manifest["optional"] == []
    keys = {c["key"] for c in manifest["flavours"][0]["config"]}
    assert keys == set(settings.DEFAULTS)
    skills = {p.parent.name for p in (REPO / "artifacts" / "skills").rglob("SKILL.md")}
    agents = {}
    for path in (REPO / "artifacts" / "agents").glob("*/Agent.json"):
        agent = json.loads(path.read_text(encoding="utf-8"))
        agents[agent["id"]] = agent
        assert set(agent["skill_ids"]) <= skills and agent["plugins"] == ["knowledge-watch"]
        assert (path.parent / "soul.md").is_file()
    assert agents["knowledge-researcher"]["tools"] == ["web"], "the researcher has the web"
    assert agents["knowledge-editor"]["tools"] == [], "the editor has no web and no shell"
    for pid in pipelines.ALL:
        pipeline = json.loads((REPO / "artifacts" / "pipelines" / f"{pid}.json").read_text(encoding="utf-8"))
        assert pipeline["schedule"].startswith("CRON_TZ=Asia/Dubai ")
        assert all(step["agent_id"] in agents for step in pipeline["steps"])
    for path in (REPO / "artifacts").rglob("*"):
        if path.suffix in (".md", ".json"):
            for tool in ("scan_brief", "save_items", "digest_facts", "save_digest"):
                text = path.read_text(encoding="utf-8")
                if f"knowledge_watch_{tool}" in text:
                    assert tool in TOOLS
