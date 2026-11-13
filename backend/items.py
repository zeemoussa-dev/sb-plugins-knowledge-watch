"""The news items the researcher filed, and each scan it ran.

An item is one story: its link, title, source, the source's own date, the category and
topic it was filed under, a summary, why it matters to Core42 (the researcher's
inference, marked as such on every screen), how much it matters, and the organisations
it names. The researcher decides all of that; this module only checks the shape, refuses
a story without a link or from a blocked source, and keeps one copy of each link.

Stored in `data/KnowledgeWatch/items.json`, newest first, for `KEEP_DAYS`.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from . import interests, runs, settings

STORE = "data/KnowledgeWatch/items.json"
KEEP_DAYS = 180
MAX_SCANS = 200
IMPORTANCE = ("high", "medium", "low")
_TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ocid", "cmpid", "guccounter"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(moment: datetime | None = None) -> str:
    return (moment or now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(text: str) -> datetime | None:
    text = str(text or "").strip()
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _text(value, limit: int = 600) -> str:
    return " ".join(str(value or "").split())[:limit]


def normal_url(url: str) -> str:
    """One spelling of a link, so the same story found twice is filed once: no
    fragment, no tracking parameters, no `www.`, no trailing slash."""
    parts = urlsplit(str(url or "").strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return ""
    host = parts.netloc.lower().removeprefix("www.")
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if not (k.lower().startswith("utm_") or k.lower() in _TRACKING)])
    return urlunsplit(("https", host, parts.path.rstrip("/") or "/", query, ""))


def domain_of(url: str) -> str:
    return urlsplit(normal_url(url)).netloc


def _blocked(domain: str, blocked: list[str]) -> bool:
    return any(domain == b or domain.endswith("." + b) for b in blocked)


def _read(api) -> dict:
    raw = api.data.read_text(STORE)
    try:
        found = json.loads(raw) if raw else {}
    except ValueError:
        found = {}
    return {"items": list(found.get("items") or []), "scans": list(found.get("scans") or [])}


def _write(api, book: dict) -> None:
    edge = now() - timedelta(days=KEEP_DAYS)
    book["items"] = [i for i in book["items"] if (parse(i.get("found_at")) or now()) >= edge]
    book["scans"] = book["scans"][:MAX_SCANS]
    api.data.write_text(STORE, json.dumps(book, ensure_ascii=False, indent=1))


def all_items(api) -> list[dict]:
    return _read(api)["items"]


def scans(api) -> list[dict]:
    return _read(api)["scans"]


def last_scan(api, category_id: str) -> dict | None:
    return next((s for s in scans(api) if s.get("category") == category_id), None)


def since(api, category_id: str) -> str:
    """The date a scan of this category looks back to: its last scan, never further
    back than the horizon."""
    horizon = (now() - timedelta(days=settings.horizon_days(api))).date()
    last = parse((last_scan(api, category_id) or {}).get("at"))
    start = max(horizon, (last - timedelta(days=1)).date()) if last else horizon
    return start.isoformat()


def recent(api, *, category: str = "", topic: str = "", days: int = 30, query: str = "",
           limit: int = 200) -> list[dict]:
    edge = now() - timedelta(days=days)
    q = query.lower().strip()
    found = []
    for item in all_items(api):
        if category and item.get("category") != category:
            continue
        if topic and str(item.get("topic") or "").lower() != topic.lower():
            continue
        if (parse(item.get("found_at")) or now()) < edge:
            continue
        if q and q not in " ".join([item.get("title", ""), item.get("summary", ""), item.get("topic", ""),
                                    " ".join(item.get("companies") or [])]).lower():
            continue
        found.append(item)
    return found[:limit]


def already_filed(api, category_id: str) -> list[dict]:
    """What this category already holds from the last month, so a scan does not file
    a story twice under another link."""
    return [{"title": i.get("title"), "url": i.get("url"), "published": i.get("published")}
            for i in recent(api, category=category_id, days=30, limit=60)]


def save(api, category_id: str, rows, *, queries=None, note: str = "") -> dict:
    category = interests.get(api, str(category_id or ""))
    if category is None:
        raise ValueError(f"{category_id!r} is not a category; `scan_brief` lists the ones that are")
    if not isinstance(rows, list):
        raise ValueError("items must be a list")
    topics = {t["name"].lower(): t["name"] for t in category["topics"]}
    blocked = settings.domains(api, "blocked_domains")
    limit = settings.max_items(api)
    book = _read(api)
    seen = {normal_url(i.get("url", "")) for i in book["items"]}
    saved, refused = [], []
    for row in rows:
        if not isinstance(row, dict):
            refused.append({"item": str(row)[:80], "why": "not an item"})
            continue
        url = normal_url(row.get("url"))
        title = _text(row.get("title"), 300)
        summary = _text(row.get("summary"), 1200)
        why = None
        if not url:
            why = "no link"
        elif not title or not summary:
            why = "an item needs a title and a summary"
        elif _blocked(domain_of(url), blocked):
            why = f"{domain_of(url)} is a blocked source"
        elif url in seen:
            why = "already filed"
        elif len(saved) >= limit:
            why = f"at most {limit} items per category per scan"
        if why:
            refused.append({"item": title or str(row.get("url"))[:120], "why": why})
            continue
        published = _text(row.get("published"), 10)
        try:
            date.fromisoformat(published)
        except ValueError:
            published = ""
        topic = _text(row.get("topic"), 80)
        importance = _text(row.get("importance"), 10).lower()
        item = {
            "id": hashlib.sha1(url.encode("utf-8")).hexdigest()[:12],
            "url": url,
            "title": title,
            "source": _text(row.get("source"), 80) or domain_of(url),
            "published": published,
            "category": category["id"],
            "topic": topics.get(topic.lower(), topic),
            "summary": summary,
            "why_it_matters": _text(row.get("why_it_matters"), 800),
            "importance": importance if importance in IMPORTANCE else "medium",
            "companies": [_text(c, 80) for c in (row.get("companies") or []) if _text(c, 80)][:12],
            "found_at": stamp(),
        }
        seen.add(url)
        saved.append(item)
    book["items"] = saved + book["items"]
    book["scans"].insert(0, {"at": stamp(), "category": category["id"], "saved": len(saved),
                             "refused": len(refused), "queries": [_text(q, 200) for q in (queries or [])][:20],
                             "note": _text(note, 300)})
    _write(api, book)
    runs.filed(api, category["id"], len(saved), len(refused))
    return {"saved": len(saved), "refused": refused, "category": category["id"]}
