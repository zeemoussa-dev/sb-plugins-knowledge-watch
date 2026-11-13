"""Knowledge Watch -- a Second Brain plugin.

Keeps the CBO up to date on the technology and industry landscape, in the knowledge
categories and topics he chooses.

- **The work** is two Background Agents this plugin ships, run by two Pipelines: the
  researcher scans the web a few times a week and files dated, sourced items; the
  editor writes the weekly digest from them. They gather and file through the agent
  tools registered here, which judge nothing.
- **The digest** is the weekly Pipeline's last reply, which the framework sends by chat
  and email, and is also filed as a note in the vault.

It reads no other plugin (the operator's decision): the companies it watches are the
topics the CBO names, not the Entities registry.

Everything it needs from the framework arrives through the Plugin API handed to
`register`; this package imports nothing from the framework itself.
"""
from __future__ import annotations

from . import digests, interests, items, runs, tools
from .routes import build_router


def register(api) -> None:
    # A data file this plugin has not registered cannot be read or written.
    for path in (interests.STORE, items.STORE, digests.STORE, runs.STORE):
        api.register_seed_data_file(path)
    api.register_router(build_router(api))
    tools.register(api)
