"""What the CBO wants to be kept up to date on: knowledge categories, and the topics he
is interested in inside each one.

A category is a beat ("Hyperscalers and cloud") with a line on why it matters to him;
each topic in it is one thing to watch ("Oracle OCI"), with his own note on what he wants
to know about it. He adds, renames, switches off and removes both on the Interests tab.
The researcher scans every category that is on, topic by topic; the digest has one
section per category that is on.

Stored in `data/KnowledgeWatch/interests.json`. A file that was never saved means the
categories this module ships.
"""
from __future__ import annotations

import json
import re

STORE = "data/KnowledgeWatch/interests.json"
MAX_CATEGORIES = 20
MAX_TOPICS = 30


def _t(name: str, notes: str = "") -> dict:
    return {"name": name, "notes": notes}


DEFAULT_CATEGORIES = [
    {"id": "models", "name": "AI models and providers",
     "about": "the frontier labs and the models Core42 hosts or competes with",
     "topics": [_t("OpenAI"), _t("Anthropic"), _t("Google DeepMind and Gemini"), _t("Meta and Llama"),
                _t("Mistral"), _t("xAI"),
                _t("Open-weight models", "DeepSeek, Qwen, Falcon, Jais and other open releases"),
                _t("Enterprise and government AI adoption", "large deployments, agents in production")]},
    {"id": "cloud", "name": "Hyperscalers and cloud",
     "about": "the clouds Core42 partners with and competes against",
     "topics": [_t("Microsoft Azure"), _t("AWS"), _t("Google Cloud"), _t("Oracle OCI"),
                _t("Neoclouds", "CoreWeave, Nebius, Lambda, Crusoe and other GPU clouds"),
                _t("Sovereign cloud offerings", "sovereign or in-country editions of the big clouds"),
                _t("Cloud regions and pricing in the Middle East")]},
    {"id": "sovereign", "name": "Sovereign AI and policy",
     "about": "the rules and national programmes that shape sovereign AI",
     "topics": [_t("National AI programmes"), _t("Data residency and sovereignty rules"),
                _t("US export controls on AI chips", "licences for the UAE and the Gulf in particular"),
                _t("EU AI Act"), _t("UAE and Saudi AI regulation")]},
    {"id": "infrastructure", "name": "Data centres, GPUs and power",
     "about": "the compute, the buildings and the power behind AI",
     "topics": [_t("NVIDIA"), _t("AMD"), _t("Custom silicon", "TPU, Trainium, Maia, Cerebras, Groq"),
                _t("Data centre builds and capacity deals"), _t("Power and cooling for AI data centres")]},
    {"id": "gulf", "name": "Gulf and UAE technology market",
     "about": "Core42's home market and its neighbours",
     "topics": [_t("G42 group"), _t("MGX"), _t("Stargate UAE"), _t("HUMAIN (Saudi Arabia)"),
                _t("Qatar AI and cloud"), _t("UAE government AI and digital programmes"),
                _t("Large Gulf technology tenders and deals")]},
    {"id": "watchlist", "name": "Competitors and partners",
     "about": "the named companies that matter to Core42's business",
     "topics": [_t("Core42", "Core42 itself in the press"), _t("G42"), _t("Microsoft"), _t("NVIDIA"),
                _t("OpenAI"), _t("Oracle"), _t("AWS"), _t("Google"), _t("Khazna Data Centers"),
                _t("Presight"), _t("Inception"), _t("AIQ"), _t("HUMAIN"), _t("e&"), _t("du")]},
]


def _text(value, limit: int = 300) -> str:
    return " ".join(str(value or "").split())[:limit]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "category"


def _defaults() -> list[dict]:
    return [{**c, "enabled": True, "topics": [dict(t) for t in c["topics"]]} for c in DEFAULT_CATEGORIES]


def read(api) -> list[dict]:
    raw = api.data.read_text(STORE)
    if not raw:
        return _defaults()
    try:
        found = json.loads(raw).get("categories")
    except (ValueError, AttributeError):
        return _defaults()
    return clean(found) if isinstance(found, list) else _defaults()


def enabled(api) -> list[dict]:
    return [c for c in read(api) if c["enabled"] and c["topics"]]


def get(api, category_id: str) -> dict | None:
    return next((c for c in read(api) if c["id"] == category_id), None)


def clean(categories) -> list[dict]:
    """What was sent, made safe to keep: names trimmed, ids unique, empty topics
    dropped. Raises on what cannot be kept at all."""
    if not isinstance(categories, list):
        raise ValueError("categories must be a list")
    if len(categories) > MAX_CATEGORIES:
        raise ValueError(f"at most {MAX_CATEGORIES} categories")
    kept, ids = [], set()
    for row in categories:
        if not isinstance(row, dict):
            continue
        name = _text(row.get("name"), 80)
        if not name:
            raise ValueError("every category needs a name")
        base = slug(_text(row.get("id"), 40) or name)
        cid, n = base, 2
        while cid in ids:
            cid, n = f"{base}-{n}", n + 1
        ids.add(cid)
        topics, names = [], set()
        for topic in row.get("topics") or []:
            if isinstance(topic, str):
                topic = {"name": topic}
            if not isinstance(topic, dict):
                continue
            tname = _text(topic.get("name"), 80)
            if not tname or tname.lower() in names:
                continue
            names.add(tname.lower())
            topics.append({"name": tname, "notes": _text(topic.get("notes"), 300)})
        if len(topics) > MAX_TOPICS:
            raise ValueError(f"{name}: at most {MAX_TOPICS} topics")
        kept.append({"id": cid, "name": name, "about": _text(row.get("about"), 300),
                     "enabled": row.get("enabled") is not False, "topics": topics})
    return kept


def save(api, categories) -> list[dict]:
    kept = clean(categories)
    api.data.write_text(STORE, json.dumps({"categories": kept}, ensure_ascii=False, indent=2))
    return kept


def reset(api) -> list[dict]:
    return save(api, _defaults())
