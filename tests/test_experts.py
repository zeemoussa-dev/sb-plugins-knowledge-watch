"""1.3: the Industry and Knowledge Experts' tools -- topics, research filed in the vault,
the digest, and refreshing the knowledge data."""
from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from backend import interests, runs
from tests.conftest import call, route


def test_an_expert_adds_tunes_and_drops_a_topic(registered):
    api = registered
    added = call(api, "add_topic", category="cloud", name="Nebius", notes="its Middle East plans",
                 search_terms=["Nebius UAE"], sources=["https://nebius.com/newsroom"])
    assert added["saved"] and not added["updated"] and added["topic"]["sources"] == ["nebius.com"]
    tuned = call(api, "add_topic", category="cloud", name="nebius", leave_out="share price")
    assert tuned["updated"] and tuned["topic"]["notes"] == "its Middle East plans"
    assert tuned["topic"]["leave_out"] == "share price"
    assert "Nebius" in [t["name"] for t in call(api, "topics")["categories"][1]["topics"]]
    call(api, "remove_topic", category="cloud", name="Nebius")
    assert "Nebius" not in [t["name"] for t in interests.get(api, "cloud")["topics"]]
    with pytest.raises(ValueError):
        call(api, "add_topic", category="nope", name="X")


def test_research_is_filed_in_its_place_newest_on_top(registered, tmp_path):
    api = registered
    with pytest.raises(ValueError, match="source"):
        call(api, "save_research", category="cloud", topic="Oracle OCI", markdown="x", sources=[])
    with pytest.raises(ValueError, match="add it first"):
        call(api, "save_research", category="cloud", topic="Bananas", markdown="x", sources=["s"])
    first = call(api, "save_research", category="cloud", topic="Oracle OCI", title="UAE regions",
                 markdown="**In short** Two regions.", sources=[{"url": "https://oracle.com/a", "title": "Oracle"}])
    call(api, "save_research", category="cloud", topic="oracle oci", title="Sovereign offer",
         markdown="**In short** A sovereign edition.", sources=["https://oracle.com/b"])
    assert first["note"] == "Work/Knowledge Watch/Hyperscalers and cloud/Oracle OCI - research.md"
    text = (tmp_path / first["note"]).read_text(encoding="utf-8")
    assert text.index("Sovereign offer") < text.index("UAE regions"), "the newest is on top, the older kept"
    notes = call(api, "research_notes", topic="Oracle OCI")["notes"]
    assert [n["title"] for n in notes] == ["Sovereign offer", "UAE regions"]
    assert route(api, "/research")(category="cloud", topic="Oracle OCI")[0]["note"] == first["note"]


def test_an_expert_reads_the_digest(registered):
    api = registered
    assert call(api, "digest")["digest"] is None
    call(api, "save_digest", sections={"Headlines": "Quiet week."})
    found = call(api, "digest")
    assert "Quiet week." in found["digest"]["markdown"] and len(found["weeks"]) == 1


def test_an_expert_refreshes_a_topic_or_everything(registered):
    api = registered
    done = threading.Event()
    api.agents = SimpleNamespace(run=lambda *a, **k: done.set() or "ok")
    answer = call(api, "refresh_now", category="gulf", topic="MGX")
    assert answer["started"] and done.wait(5)
    for _ in range(50):
        if runs.listed(api)[0]["state"] != "requested":
            break
        threading.Event().wait(0.05)
    everything = call(api, "refresh_now")
    assert everything["started"] is False and "switched off" in everything["why"] or "not installed" in everything["why"]
    api.switch_on("knowledge-scan")
    assert call(api, "refresh_now")["started"] is True
    assert api.jobs == [("job-knowledge-scan", None)]
