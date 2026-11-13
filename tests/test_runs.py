"""1.1: topic tuning, the run log behind the Settings tab, refreshing one topic, and
saying why a Pipeline does not work."""
from __future__ import annotations

import json
import threading
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend import interests, items, runs
from tests.conftest import call, route


def tuned(api):
    categories = interests.read(api)
    cloud = next(c for c in categories if c["id"] == "cloud")
    cloud["topics"][3] = {"name": "Oracle OCI", "notes": "UAE regions",
                          "search_terms": "Oracle Abu Dhabi region\nOCI sovereign cloud, Oracle Abu Dhabi region",
                          "sources": ["https://www.oracle.com/news", "datacenterdynamics.com"],
                          "leave_out": "share price"}
    return route(api, "/interests", "PUT")({"categories": categories})["categories"]


def test_a_topic_keeps_its_search_terms_sources_and_what_to_leave_out(registered):
    oci = next(c for c in tuned(registered) if c["id"] == "cloud")["topics"][3]
    assert oci["search_terms"] == ["Oracle Abu Dhabi region", "OCI sovereign cloud"]
    assert oci["sources"] == ["oracle.com", "datacenterdynamics.com"]
    assert oci["leave_out"] == "share price"
    assert interests.read(registered)[0]["topics"][0]["search_terms"] == [], "shipped topics have the new fields"


def test_the_scan_brief_carries_the_tuning_and_can_name_one_topic(registered):
    tuned(registered)
    brief = call(registered, "scan_brief", category="cloud", topic="oracle oci")
    job = brief["categories"][0]
    assert [t["name"] for t in job["topics"]] == ["Oracle OCI"]
    assert "search for: Oracle Abu Dhabi region, OCI sovereign cloud" in job["prompt"]
    assert "look first at: oracle.com" in job["prompt"] and "leave out: share price" in job["prompt"]
    with pytest.raises(ValueError, match="not a topic"):
        call(registered, "scan_brief", category="cloud", topic="Bananas")


def test_a_scheduled_scan_is_recorded_from_start_to_done(registered):
    api = registered
    call(api, "scan_brief")
    assert runs.open_run(api, "scan")["trigger"] == "schedule"
    for category in interests.enabled(api):
        call(api, "save_items", category=category["id"], items=[])
    run = runs.listed(api)[0]
    assert run["state"] == "done" and len(run["filed"]) == 6 and run["finished_at"]


def test_a_problem_the_agent_reports_shows_why_on_the_status(registered):
    api = registered
    api.switch_on("knowledge-scan")
    call(api, "scan_brief")
    call(api, "report_problem", problem="Withheld: what web_search returned reads as an attempt to instruct you")
    scan = route(api, "/status")()["pipelines"][0]
    assert scan["state"] == "failed" and scan["why"].startswith("Withheld")


def test_a_run_left_open_too_long_is_stopped(registered):
    api = registered
    call(api, "scan_brief")
    book = json.loads(api.files[runs.STORE])
    book["runs"][0]["started_at"] = items.stamp(items.now() - timedelta(minutes=runs.STALE_MINUTES + 5))
    api.files[runs.STORE] = json.dumps(book)
    assert runs.listed(api)[0]["state"] == "stopped"
    assert runs.open_run(api, "scan") is None


def test_the_status_says_off_no_job_running_and_on(registered):
    api = registered
    states = {p["id"]: p["state"] for p in route(api, "/status")()["pipelines"]}
    assert states == {"knowledge-scan": "missing", "knowledge-weekly": "missing"}
    api.switch_on("knowledge-scan")
    api.pipeline_states["knowledge-weekly"] = {"id": "knowledge-weekly", "cron_job_id": "j2", "cron_enabled": False}
    found = {p["id"]: p for p in route(api, "/status")()["pipelines"]}
    assert found["knowledge-scan"]["state"] == "on" and found["knowledge-weekly"]["state"] == "off"
    call(api, "scan_brief")
    found = {p["id"]: p for p in route(api, "/status")()["pipelines"]}
    assert found["knowledge-scan"]["state"] == "running" and found["knowledge-scan"]["run"]
    api.pipeline_states["knowledge-weekly"]["last_status"] = "failed"
    api.pipeline_states["knowledge-weekly"]["cron_enabled"] = True
    assert {p["id"]: p for p in route(api, "/status")()["pipelines"]}["knowledge-weekly"]["state"] == "failed"


def test_run_now_is_the_cbos_and_is_not_started_twice(registered):
    api = registered
    api.switch_on("knowledge-scan")
    api.caller = {"id": "u2", "name": "Sherif", "disabled": False, "capabilities": []}
    assert route(api, "/pipelines/{pipeline_id}/run", "POST")("knowledge-scan")["started"] is True
    assert runs.open_run(api, "scan")["trigger"] == "run now"
    again = route(api, "/pipelines/{pipeline_id}/run", "POST")("knowledge-scan")
    assert again == {"started": False, "note": "it is running already"}
    api.writable = False
    with pytest.raises(HTTPException):
        route(api, "/pipelines/{pipeline_id}/run", "POST")("knowledge-scan")


def test_refreshing_one_topic_runs_the_researcher_and_records_it(registered):
    api = registered
    asked = []
    done = threading.Event()

    def run(agent_id, instruction, *, facts=None, timeout=180):
        asked.append((agent_id, instruction, timeout))
        call(api, "scan_brief", category="cloud", topic="AWS")
        call(api, "save_items", category="cloud", items=[])
        done.set()
        return "cloud: nothing new"
    api.agents = SimpleNamespace(run=run)
    answer = route(api, "/refresh", "POST")({"category": "cloud", "topic": "AWS"})
    assert answer["started"] and done.wait(5)
    for _ in range(50):
        if runs.listed(api)[0]["finished_at"] and runs.listed(api)[0]["reply"]:
            break
        threading.Event().wait(0.05)
    run_row = runs.listed(api)[0]
    assert asked[0][0] == "knowledge-researcher" and "`AWS`" in asked[0][1]
    assert run_row["trigger"] == "refresh" and run_row["state"] == "done" and run_row["reply"] == "cloud: nothing new"


def test_a_refresh_that_fails_says_why(registered):
    api = registered
    done = threading.Event()

    def run(agent_id, instruction, *, facts=None, timeout=180):
        done.set()
        raise RuntimeError("Knowledge Researcher was not installed by knowledge-watch")
    api.agents = SimpleNamespace(run=run)
    route(api, "/refresh", "POST")({"category": "gulf"})
    assert done.wait(5)
    for _ in range(50):
        if runs.listed(api)[0]["state"] == "failed":
            break
        threading.Event().wait(0.05)
    assert runs.listed(api)[0]["problem"].startswith("Knowledge Researcher was not installed")


def test_a_refresh_is_refused_while_a_scan_runs_or_for_an_unknown_topic(registered):
    api = registered
    api.agents = SimpleNamespace(run=lambda *a, **k: "")
    with pytest.raises(HTTPException) as unknown:
        route(api, "/refresh", "POST")({"category": "cloud", "topic": "Bananas"})
    assert unknown.value.status_code == 404
    call(api, "scan_brief")
    with pytest.raises(HTTPException) as busy:
        route(api, "/refresh", "POST")({"category": "cloud"})
    assert busy.value.status_code == 409


def test_the_digest_is_recorded_as_a_run(registered):
    api = registered
    call(api, "digest_facts")
    assert runs.open_run(api, "digest") is not None
    call(api, "save_digest", sections={"Headlines": "Quiet."})
    assert runs.listed(api)[0]["kind"] == "digest" and runs.listed(api)[0]["state"] == "done"


def test_items_filter_by_topic(registered):
    api = registered
    call(api, "save_items", category="cloud", items=[
        {"url": "https://a.example/1", "title": "A", "summary": "s", "topic": "AWS"},
        {"url": "https://a.example/2", "title": "B", "summary": "s", "topic": "Oracle OCI"}])
    assert [i["title"] for i in route(api, "/items")(category="cloud", topic="aws", days=30, q="")["items"]] == ["A"]
