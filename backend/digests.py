"""The weekly digest: what it is written from, and filing it.

The editor agent writes it from the items the researcher filed since the last digest;
this module hands over those items, grouped by category, and files what comes back:
in `data/KnowledgeWatch/digests.json` for the screen, and as one note in the vault
(`<vault folder>/Knowledge Watch <date>.md`) so other agents find it through search.
The text the CBO receives is the Pipeline's last reply, sent by the framework.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from . import interests, items, runs, settings

STORE = "data/KnowledgeWatch/digests.json"
KEEP = 104
HEADLINES = "Headlines"
NEXT = "Watch next week"
# Dubai keeps one offset all year, so a fixed zone needs no time zone database.
DUBAI = timezone(timedelta(hours=4))
MAX_WINDOW_DAYS = 14


def _read(api) -> list[dict]:
    raw = api.data.read_text(STORE)
    try:
        found = json.loads(raw) if raw else {}
    except ValueError:
        found = {}
    return list(found.get("digests") or [])


def listed(api) -> list[dict]:
    return [{k: d.get(k) for k in ("id", "at", "week", "headline", "items", "note")} for d in _read(api)]


def read(api, digest_id: str) -> dict | None:
    return next((d for d in _read(api) if d.get("id") == digest_id), None)


def latest(api) -> dict | None:
    found = _read(api)
    return found[0] if found else None


def sections(api) -> list[str]:
    return [HEADLINES] + [c["name"] for c in interests.enabled(api)] + [NEXT]


def window(api) -> tuple[datetime, datetime]:
    """From the last digest (or a week ago) to now, never more than two weeks."""
    end = items.now()
    last = items.parse((latest(api) or {}).get("at"))
    start = last or end - timedelta(days=7)
    return max(start, end - timedelta(days=MAX_WINDOW_DAYS)), end


def week_label(moment: datetime | None = None) -> str:
    return (moment or items.now()).astimezone(DUBAI).date().isoformat()


def facts(api) -> dict:
    start, end = window(api)
    grouped = []
    total = 0
    for category in interests.enabled(api):
        rows = [i for i in items.all_items(api)
                if i.get("category") == category["id"] and start < (items.parse(i.get("found_at")) or end) <= end]
        total += len(rows)
        grouped.append({"category": category["name"], "about": category["about"],
                        "topics": [t["name"] for t in category["topics"]],
                        "items": [{k: i.get(k) for k in ("title", "url", "source", "published", "topic", "summary",
                                                         "why_it_matters", "importance", "companies")}
                                  for i in rows]})
    previous = latest(api)
    runs.begin(api, "digest", [])
    return {
        "week": week_label(end),
        "from": items.stamp(start), "to": items.stamp(end),
        "sections": sections(api),
        "prompt": settings.get(api, "digest_prompt"),
        "item_count": total,
        # The weekly's last reply is what is sent: NOTHING sends nothing (framework BUG-121 fix).
        "reply_when_empty": "NOTHING",
        "note": ("No items were filed since the last digest. File no digest and reply with exactly NOTHING, so "
                 "nothing is sent.") if total == 0 else "",
        "categories": grouped,
        "previous_headlines": (previous or {}).get("sections", {}).get(HEADLINES, ""),
        "scans": [{k: s.get(k) for k in ("at", "category", "saved")}
                  for s in items.scans(api) if start < (items.parse(s.get("at")) or end) <= end],
    }


def markdown(week: str, chosen: dict[str, str], order: list[str]) -> str:
    parts = [f"Knowledge Watch, week to {week}"]
    for name in order:
        if chosen.get(name):
            parts.append(f"## {name}\n\n{chosen[name]}")
    return "\n\n".join(parts) + "\n"


def save(api, sent_sections, *, sources=None) -> dict:
    if not isinstance(sent_sections, dict) or not sent_sections:
        raise ValueError("`sections` maps each section name to its markdown")
    order = sections(api)
    refused = [name for name in sent_sections if name not in order]
    if refused:
        raise ValueError(f"not a section of this digest: {', '.join(refused)}; the sections are {', '.join(order)}")
    chosen = {name: str(sent_sections.get(name) or "").strip() for name in order}
    if not chosen[HEADLINES]:
        raise ValueError(f"the digest needs its {HEADLINES} section")
    start, end = window(api)
    if not any(start < (items.parse(i.get("found_at")) or end) <= end for i in items.all_items(api)):
        raise ValueError("No items were filed since the last digest, so there is no digest to file: reply with "
                         "exactly NOTHING, so nothing is sent.")
    week = week_label(end)
    text = markdown(week, chosen, order)
    count = sum(1 for i in items.all_items(api) if start < (items.parse(i.get("found_at")) or end) <= end)
    first = next((line.lstrip("-*0123456789. ").replace("**", "").strip()
                  for line in chosen[HEADLINES].splitlines() if line.strip()), "")
    note = ""
    folder = settings.vault_folder(api)
    try:
        note = api.vault.write_note(folder, f"Knowledge Watch {week}", {
            "type": "Digest",
            "name": f"Knowledge Watch, week to {week}",
            "date": week,
            "tags": ["kind/knowledge-watch"],
        }, text)
    except Exception as exc:  # the digest is still filed and sent; the screen says why the note is not
        note = f"not filed in the vault: {exc}"
    digest = {"id": f"{week}-{end.strftime('%H%M%S')}", "at": items.stamp(end), "week": week,
              "headline": first[:300], "items": count, "sections": chosen, "markdown": text,
              "sources": [str(s)[:300] for s in (sources or [])][:100], "note": note}
    found = [digest] + _read(api)
    api.data.write_text(STORE, json.dumps({"digests": found[:KEEP]}, ensure_ascii=False, indent=1))
    runs.digest_done(api)
    return {"saved": True, "id": digest["id"], "note": note, "markdown": text}
