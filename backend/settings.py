"""The plugin-wide settings, as `plugin.json` declares them, with what an empty one means.

Read through `api.config` and changed on the Settings page through `api.config.set`.
Every value is optional: empty always means the default written here, so an install
that never opens the Settings page still has a working plugin.
"""
from __future__ import annotations

PREFERRED_DOMAINS = [
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com", "theinformation.com",
    "techcrunch.com", "theverge.com", "datacenterdynamics.com", "semianalysis.com",
    "thenationalnews.com", "wam.ae", "zawya.com", "gulfnews.com", "khaleejtimes.com", "arabnews.com",
    "agbi.com", "openai.com", "anthropic.com", "blog.google", "blogs.microsoft.com",
    "aboutamazon.com", "nvidianews.nvidia.com", "oracle.com", "g42.ai", "core42.ai",
]

SCAN_PROMPT = """You keep the Chief Business Officer of Core42 -- the UAE sovereign cloud
and AI infrastructure company in the G42 group -- up to date on his industry. For the
category "{category}" ({category_about}), look for what happened since {since} on each
topic: {topics}.

Prefer primary sources (the company's own announcement, a regulator, a filing) and
established press; the preferred sources are {preferred}. A story counts when it changes
something for a sovereign cloud and AI infrastructure provider in the Gulf: a launch, a
price or capacity move, a deal, funding, a partnership, a regulation, a leadership change,
a market entry in the region. Commentary, rumour and listicles do not, unless a reliable
outlet reports something new. Give every item its link and the source's own date."""

DIGEST_PROMPT = """Write for the CBO of Core42, who knows the industry well and has ten
minutes on Sunday evening. Lead with what moved. One or two sentences per story, names and
numbers exact, each with its source and date. Close each section with what it means for
Core42 when there is something to say, marked as your inference. Skip what does not
matter; a quiet section gets one line saying so."""

DEFAULTS = {
    "vault_folder": "Work/Industry Watch",
    "preferred_domains": ", ".join(PREFERRED_DOMAINS),
    "blocked_domains": "",
    "horizon_days": "7",
    "max_items": "6",
    "scan_prompt": SCAN_PROMPT,
    "digest_prompt": DIGEST_PROMPT,
}


def get(api, key: str) -> str:
    config = getattr(api, "config", None)
    value = None
    if config is not None:
        try:
            value = config.get(key)
        except Exception:
            value = None
    value = str(value or "").strip()
    return value or DEFAULTS[key]


def domains(api, key: str) -> list[str]:
    found = []
    for part in get(api, key).replace(";", ",").split(","):
        part = part.strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.")
        part = part.split("/")[0]
        if part and part not in found:
            found.append(part)
    return found


def number(api, key: str, low: int, high: int) -> int:
    try:
        value = int(get(api, key))
    except ValueError:
        value = int(DEFAULTS[key])
    return min(max(value, low), high)


def horizon_days(api) -> int:
    return number(api, "horizon_days", 1, 60)


def max_items(api) -> int:
    return number(api, "max_items", 1, 20)


def vault_folder(api) -> str:
    return get(api, "vault_folder").strip("/\\") or DEFAULTS["vault_folder"]


def all_values(api) -> dict[str, str]:
    return {key: get(api, key) for key in DEFAULTS}
