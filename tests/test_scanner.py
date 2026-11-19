"""1.5: the whole scan in the plugin, one researcher turn per category, where a failed
category is tried once more and then skipped; and a week with no items sends nothing."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend import runs, scanner
from tests.conftest import call, route


def fake_researcher(api, *, failing=(), flaky=()):
    """Files an empty scan for the category it is asked about, except: `failing` raises
    every time, `flaky` raises the first time only."""
    seen = []

    def run(agent_id, instruction, *, facts=None, timeout=180):
        category = instruction.split("`")[1]
        seen.append(category)
        if category in failing or (category in flaky and seen.count(category) == 1):
            raise ConnectionError("ReadError")
        call(api, "scan_brief", category=category)
        call(api, "save_items", category=category, items=[])
        return f"{category}: nothing new"
    api.agents = SimpleNamespace(run=run)
    return seen


def test_one_failed_category_does_not_stop_the_others(registered):
    api = registered
    seen = fake_researcher(api, failing={"sovereign"}, flaky={"cloud"})
    scanner.start(api, "schedule", wait=True, pause=0)
    assert seen.count("cloud") == 2, "a failure is tried once more"
    assert seen.count("sovereign") == 2 and seen[-1] == "watchlist", "a second failure is skipped, the rest go on"
    run = runs.listed(api)[0]
    assert run["state"] == "failed" and set(run["filed"]) == {"models", "cloud", "infrastructure", "gulf", "watchlist"}
    assert "Sovereign AI and policy: ConnectionError: ReadError" in run["problem"]
    assert run["failures"] == {"sovereign": "ConnectionError: ReadError"}
    assert len([r for r in runs.listed(api) if r["kind"] == "scan"]) == 1


def test_a_clean_scan_is_done(registered):
    api = registered
    fake_researcher(api)
    answer = scanner.start(api, "schedule", wait=True, pause=0)
    assert answer["started"] and len(answer["categories"]) == 6
    assert runs.listed(api)[0]["state"] == "done"


def test_a_turn_that_ends_without_filing_is_tried_again_then_recorded(registered):
    api = registered
    api.agents = SimpleNamespace(run=lambda *a, **k: "I could not find anything")
    scanner.start(api, "schedule", wait=True, pause=0)
    run = runs.listed(api)[0]
    assert run["state"] == "failed" and "I could not find anything" in run["problem"]


def test_a_problem_the_researcher_reports_does_not_end_the_background_scan(registered):
    api = registered
    seen = []

    def run(agent_id, instruction, *, facts=None, timeout=180):
        category = instruction.split("`")[1]
        seen.append(category)
        if category == "models":
            call(api, "report_problem", problem="Withheld: web_search")
            return "NO WEB SEARCH"
        call(api, "save_items", category=category, items=[])
        return "ok"
    api.agents = SimpleNamespace(run=run)
    scanner.start(api, "schedule", wait=True, pause=0)
    found = runs.listed(api)[0]
    assert seen[-1] == "watchlist" and found["state"] == "failed"
    assert "Withheld: web_search" in found["problem"] and len(found["filed"]) == 5


def test_the_pipeline_step_starts_the_scan_and_run_now_is_carried_on(registered):
    api = registered
    fake_researcher(api)
    api.switch_on("knowledge-scan")
    assert route(api, "/pipelines/{pipeline_id}/run", "POST")("knowledge-scan")["started"]
    assert runs.open_run(api, "scan")["state"] == "requested"
    answer = call(api, "start_scan")
    assert answer["started"] is True
    assert [r["trigger"] for r in runs.listed(api) if r["kind"] == "scan"] == ["run now"], "no second run"


def test_a_scan_is_not_started_twice(registered):
    api = registered
    fake_researcher(api)
    run = runs.request(api, "scan", "schedule")
    runs.begin(api, "scan", [], expected=["models"])
    assert runs.open_run(api, "scan")["id"] == run["id"]
    answer = call(api, "start_scan")
    assert answer == {"started": False, "why": "A scan is running already."}


def test_a_long_scan_with_a_heartbeat_is_not_stopped(registered):
    import json
    from datetime import timedelta

    from backend import items
    api = registered
    run = runs.request(api, "scan", "schedule")
    book = json.loads(api.files[runs.STORE])
    book["runs"][0]["started_at"] = items.stamp(items.now() - timedelta(minutes=runs.STALE_MINUTES + 20))
    book["runs"][0]["touched_at"] = items.stamp()
    api.files[runs.STORE] = json.dumps(book)
    assert runs.listed(api)[0]["state"] == "requested" and runs.open_run(api, "scan")["id"] == run["id"]


def test_a_week_with_no_items_sends_nothing(registered):
    api = registered
    facts = call(api, "digest_facts")
    assert facts["item_count"] == 0 and facts["reply_when_empty"] == "NOTHING" and "NOTHING" in facts["note"]
    with pytest.raises(ValueError, match="reply with exactly NOTHING"):
        call(api, "save_digest", sections={"Headlines": "Quiet week."})
    assert route(api, "/digests")() == []
