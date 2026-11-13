"""The agent tools: how this plugin's two agents gather and file.

Each is offered as `knowledge_watch_<name>` and given to an agent on its grants
(`plugins: ["knowledge-watch"]`). The handlers hand over and file; they decide nothing
about what matters. Arguments come from a model, so each is checked, and a bad one is
answered as an error the agent reads.
"""
from __future__ import annotations

import json

from . import digests, interests, items, runs, settings


def _answer(value) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def describe(topic: dict) -> str:
    """One topic as the prompt names it, with how the CBO tuned its search."""
    parts = [topic["notes"]] if topic.get("notes") else []
    if topic.get("search_terms"):
        parts.append("search for: " + ", ".join(topic["search_terms"]))
    if topic.get("sources"):
        parts.append("look first at: " + ", ".join(topic["sources"]))
    if topic.get("leave_out"):
        parts.append("leave out: " + topic["leave_out"])
    return f"{topic['name']} ({'; '.join(parts)})" if parts else topic["name"]


def scan_prompt(api, category: dict, since: str) -> str:
    topics = "; ".join(describe(t) for t in category["topics"])
    values = {"category": category["name"], "category_about": category["about"] or "no note",
              "since": since, "topics": topics,
              "preferred": ", ".join(settings.domains(api, "preferred_domains")) or "none set"}
    template = settings.get(api, "scan_prompt")
    try:
        return template.format(**values)
    except (KeyError, IndexError, ValueError):
        # A hand-written prompt with a brace the template does not know is used as
        # written, with the facts after it, rather than refused.
        return template + "\n\n" + "\n".join(f"{k}: {v}" for k, v in values.items())


def scan_brief(api, category_id: str = "", topic_name: str = "", *, next_one: bool = False) -> dict:
    """What to scan. `next_one` hands out one category at a time, the next one this run
    has not scanned yet: a Pipeline step scans one category in its own turn, because a
    whole scan is far more searches than one turn's budget."""
    chosen = interests.enabled(api)
    expected = [c["id"] for c in chosen]
    if next_one:
        open_run = runs.open_run(api, "scan")
        if open_run is None and runs.just_finished(api):
            return {"categories": [], "note": "Every category has been scanned in this run."}
        handed = set((open_run or {}).get("categories") or [])
        chosen = [c for c in chosen if c["id"] not in handed][:1]
        if not chosen:
            runs.close_scan(api)
            return {"categories": [], "note": "Every category has been scanned in this run."}
    elif category_id:
        chosen = [c for c in interests.read(api) if c["id"] == category_id and c["topics"]]
        if not chosen:
            raise ValueError(f"{category_id!r} is not a category with topics")
    if topic_name:
        found = [{**c, "topics": [t for t in c["topics"] if t["name"].lower() == topic_name.lower()]} for c in chosen]
        chosen = [c for c in found if c["topics"]]
        if not chosen:
            raise ValueError(f"{topic_name!r} is not a topic of {category_id or 'any category'}")
    runs.begin(api, "scan", [c["id"] for c in chosen],
               expected=expected if next_one or not (category_id or topic_name) else [c["id"] for c in chosen])
    jobs = []
    for category in chosen:
        since = items.since(api, category["id"])
        jobs.append({"category": category["id"], "name": category["name"], "about": category["about"],
                     "topics": category["topics"], "since": since,
                     "prompt": scan_prompt(api, category, since),
                     "already_filed": items.already_filed(api, category["id"])})
    return {"categories": jobs, "max_items_per_category": settings.max_items(api),
            "preferred_sources": settings.domains(api, "preferred_domains"),
            "blocked_sources": settings.domains(api, "blocked_domains")}


def register(api) -> None:
    def brief(args, context=None):
        args = args or {}
        return _answer(scan_brief(api, str(args.get("category") or "").strip(), str(args.get("topic") or "").strip(),
                                  next_one=bool(args.get("next"))))

    def report_problem(args, context=None):
        args = args or {}
        kind = str(args.get("kind") or "scan")
        run = runs.problem(api, kind if kind in runs.KINDS else "scan", str(args.get("problem") or ""))
        return _answer({"recorded": True, "run": run.get("id")})

    def save_items(args, context=None):
        args = args or {}
        return _answer(items.save(api, args.get("category"), args.get("items") or [],
                                  queries=args.get("queries") or [], note=str(args.get("note") or "")))

    def digest_facts(args, context=None):
        return _answer(digests.facts(api))

    def save_digest(args, context=None):
        args = args or {}
        return _answer(digests.save(api, args.get("sections") or {}, sources=args.get("sources") or []))

    def recent_items(args, context=None):
        args = args or {}
        try:
            days = min(max(int(args.get("days") or 30), 1), items.KEEP_DAYS)
        except (TypeError, ValueError):
            days = 30
        found = items.recent(api, category=str(args.get("category") or ""), days=days,
                             query=str(args.get("query") or ""), limit=50)
        return _answer({"items": found, "categories": [{"id": c["id"], "name": c["name"]}
                                                       for c in interests.read(api)]})

    api.register_agent_tool(
        "scan_brief", handler=brief,
        description=("What to scan the web for now: each knowledge category that is on, with the topics the CBO "
                     "is interested in (each with his note, his own search terms, the sources to look at first and "
                     "what to leave out), the date to look back to, the prompt to scan it with, and what that "
                     "category already holds so nothing is filed twice. Also the preferred and blocked sources "
                     "and the most items to file per category. `next` true hands out the next category this "
                     "run has not scanned yet, one at a time, and none when every one is done. `category` "
                     "narrows it to one category, and `topic` to one topic of it."),
        parameters={"type": "object", "properties": {"next": {"type": "boolean"}, "category": {"type": "string"},
                                                     "topic": {"type": "string"}}})
    api.register_agent_tool(
        "report_problem", handler=report_problem,
        description=("Records why a scan or a digest could not go on -- web search failing or missing, a tool "
                     "refusing -- so the Knowledge Watch screen shows it. `kind` is scan (default) or digest; "
                     "`problem` is what happened, in the tool's own words."),
        parameters={"type": "object", "properties": {
            "kind": {"type": "string", "enum": list(runs.KINDS)}, "problem": {"type": "string"}},
            "required": ["problem"]})
    api.register_agent_tool(
        "save_items", handler=save_items,
        description=("Files the stories found for one category. Each item: `url` (required), `title`, `source`, "
                     "`published` (YYYY-MM-DD, the source's own date), `topic` (one of the category's topics), "
                     "`summary` (what happened, facts only), `why_it_matters` (what it means for Core42 -- your "
                     "inference), `importance` (high, medium or low) and `companies` (the organisations it names). "
                     "`queries` lists what you searched. Call it once per category, with an empty `items` when "
                     "nothing new was found. A story already filed, from a blocked source or without a link is "
                     "refused and listed."),
        parameters={"type": "object", "properties": {
            "category": {"type": "string"},
            "items": {"type": "array", "items": {"type": "object", "properties": {
                "url": {"type": "string"}, "title": {"type": "string"}, "source": {"type": "string"},
                "published": {"type": "string"}, "topic": {"type": "string"}, "summary": {"type": "string"},
                "why_it_matters": {"type": "string"},
                "importance": {"type": "string", "enum": list(items.IMPORTANCE)},
                "companies": {"type": "array", "items": {"type": "string"}}},
                "required": ["url", "title", "summary"]}},
            "queries": {"type": "array", "items": {"type": "string"}},
            "note": {"type": "string"}},
            "required": ["category", "items"]})
    api.register_agent_tool(
        "digest_facts", handler=digest_facts, parameters={"type": "object", "properties": {}},
        description=("What the weekly digest is written from: the week, the sections it has in order, the house "
                     "prompt, and every item filed since the last digest, grouped by category, with the scans "
                     "that ran and the last digest's headlines."))
    api.register_agent_tool(
        "save_digest", handler=save_digest,
        description=("Files the weekly digest. `sections` maps each section digest_facts listed to its markdown; "
                     "`sources` lists the links it cites. A section not on the list is refused. It is kept for "
                     "the screen and filed as a note in the vault; the answer gives the whole digest as filed."),
        parameters={"type": "object", "properties": {
            "sections": {"type": "object", "additionalProperties": {"type": "string"}},
            "sources": {"type": "array", "items": {"type": "string"}}},
            "required": ["sections"]})
    api.register_agent_tool(
        "recent_items", handler=recent_items,
        description=("The news items filed recently, newest first, for answering a question about the industry: "
                     "`category` (an id), `days` (default 30) and `query` (words in the title, summary, topic or "
                     "companies) narrow it."),
        parameters={"type": "object", "properties": {
            "category": {"type": "string"}, "days": {"type": "integer", "minimum": 1, "maximum": 180},
            "query": {"type": "string"}}})
