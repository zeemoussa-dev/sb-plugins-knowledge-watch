# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this repository is

**The Knowledge Watch plugin** for Second Brain OS: the CBO's news on his industry, the technologies and the topics he follows, in the
knowledge categories and topics he chooses, scanned by a researcher agent and written
up weekly by an editor agent. The design is `Documentation/DESIGN.md`.

## Boundaries

- **A plugin imports only `app.plugin_api`.** No framework file is copied in.
- **Code gathers, the agent judges.** `backend/` hands over and files; it decides
  nothing about what matters. Mechanical checks only: a link, a blocked domain, a
  duplicate link, the per-scan limit. No regex judges relevance and nothing in the
  backend calls a model.
- **The researcher has the web and no vault. The editor has neither web nor shell.**
- **Sending is the framework's Pipeline delivery.** The editor's last reply is the
  digest. Nothing in the backend or the agents sends.
- **It reads no other plugin** (operator, 2026-11-13: "Don't link it to the other
  Plugins"). Keep `requires` and `optional` empty.
- **Screens follow the framework's `Documentation/Framework/UI-Guidelines.md`**: its
  components only, no `<select>`, settings as a sheet of rows with edit drawers, all
  four states, colours from tokens only.
- **A missing framework capability is logged in the framework repository** as a
  `REQ-SB-NN`, with the operator's OK, never worked around here.

## Commands

| Command | Where |
|---|---|
| `python -m pytest` | repository root, any Python 3.11+ with `pytest` and `fastapi` |
| `python scripts/check_plugin.py <this repo>` | the framework's `src/backend`, read-only use |

## Rules

- Read before writing; minimal changes; separate commits per logical change; never force-push `main`.
- Update `CHANGELOG.md` for everything created or changed. Tag each release `v<version>`.
- Add inline comments only where the WHY is non-obvious.
