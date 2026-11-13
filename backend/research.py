"""Research notes: an Expert's deeper look at one topic, filed in its place in the vault.

A note is `<vault folder>/<category name>/<topic> - research.md`, the newest research
at the top under its date, with its sources, so the topic's history reads down the
page. The Expert does the research with the web; this module only files what it wrote.

What a note holds is kept in `data/KnowledgeWatch/research.json` too, and the note is
written from that, so a second piece of research never depends on the vault's index
having seen the first. The index there is what the topic's drawer lists.
"""
from __future__ import annotations

import json
import re

from . import interests, items, settings

STORE = "data/KnowledgeWatch/research.json"
KEEP = 400
MAX_BODY = 60000


def _text(value, limit: int = 300) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe(name: str) -> str:
    """A name the vault takes as a file name."""
    return re.sub(r'[\\/:*?"<>|#^\[\]]+', " ", name).strip()[:80] or "Topic"


def _read(api) -> dict:
    raw = api.data.read_text(STORE)
    try:
        found = json.loads(raw) if raw else {}
    except ValueError:
        found = {}
    return {"notes": list(found.get("notes") or []), "bodies": dict(found.get("bodies") or {})}


def listed(api, *, category: str = "", topic: str = "") -> list[dict]:
    return [n for n in _read(api)["notes"]
            if (not category or n.get("category") == category)
            and (not topic or str(n.get("topic") or "").lower() == topic.lower())]


def save(api, category_id: str, topic_name: str, title: str, markdown: str, sources, *, by: str = "") -> dict:
    category = interests.get(api, str(category_id or ""))
    if category is None:
        raise ValueError(f"{category_id!r} is not a category; `topics` lists them")
    topic = next((t for t in category["topics"] if t["name"].lower() == str(topic_name or "").strip().lower()), None)
    if topic is None:
        raise ValueError(f"{topic_name!r} is not a topic of {category['name']}; add it first with `add_topic`")
    body = str(markdown or "").strip()
    if not body:
        raise ValueError("there is nothing to file")
    listed_sources = []
    for source in sources or []:
        if isinstance(source, dict) and _text(source.get("url")):
            label = _text(source.get("title")) or _text(source.get("url"))
            date = _text(source.get("date"), 20)
            listed_sources.append(f"- [{label}]({_text(source['url'], 600)})" + (f" ({date})" if date else ""))
        elif isinstance(source, str) and _text(source):
            listed_sources.append(f"- {_text(source, 600)}")
    if not listed_sources:
        raise ValueError("research needs at least one source")

    book = _read(api)
    key = f"{category['id']}|{topic['name'].lower()}"
    folder = f"{settings.vault_folder(api)}/{_safe(category['name'])}"
    name = f"{_safe(topic['name'])} - research"
    heading = _text(title, 160) or topic["name"]
    section = (f"## {items.now().date().isoformat()}: {heading}\n\n{body}\n\n**Sources**\n\n"
               + "\n".join(listed_sources) + "\n")
    text = (section + ("\n" + book["bodies"].get(key, "").strip() + "\n" if book["bodies"].get(key) else ""))[:MAX_BODY]
    note = api.vault.write_note(folder, name, {
        "type": "Research",
        "name": f"{topic['name']}: research",
        "category": category["name"],
        "topic": topic["name"],
        "tags": ["kind/research", "kind/knowledge-watch"],
    }, text)
    book["bodies"][key] = text
    book["notes"].insert(0, {"category": category["id"], "topic": topic["name"], "title": heading,
                             "at": items.stamp(), "note": note, "by": _text(by, 80),
                             "summary": _text(body.splitlines()[0].lstrip("#-* "), 300)})
    book["notes"] = book["notes"][:KEEP]
    api.data.write_text(STORE, json.dumps(book, ensure_ascii=False, indent=1))
    return {"saved": True, "note": note, "folder": folder}
