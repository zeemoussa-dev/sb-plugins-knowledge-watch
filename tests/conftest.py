"""A stand-in Plugin API: data files in memory, the vault a real temporary folder.

Nothing is imported from the framework: a plugin may reach only `app.plugin_api`, so
its tests must not need more either.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class FakeApi:
    def __init__(self, vault: Path):
        self.root = vault
        self.files: dict[str, str] = {}
        self.registered: list[str] = []
        self.tools: dict[str, dict] = {}
        self.routers: list = []
        self.settings: dict[str, str] = {}
        self.jobs: list[tuple] = []
        self.pipeline_states: dict[str, dict] = {}
        self.writable = True
        self.caller = {"id": "u1", "name": "Operator", "disabled": False, "capabilities": ["manage_plugins"]}
        self.data = SimpleNamespace(read_text=self.files.get, write_text=self._write_data)
        self.vault = SimpleNamespace(write_note=self._write_note,
                                     may_read=lambda vault=None, person_id=None: True,
                                     may_write=lambda vault=None, person_id=None: self.writable)
        self.runtime = SimpleNamespace(run_cron_job=self._run)
        self.pipelines = SimpleNamespace(get=self.pipeline_states.get, set_enabled=self._set_enabled,
                                         set_schedule=self._set_schedule)
        self.people = SimpleNamespace(caller=lambda: self.caller)
        self.config = SimpleNamespace(get=lambda key, default=None: self.settings.get(key) or default,
                                      set=self.settings.__setitem__)

    def register_seed_data_file(self, path):
        self.registered.append(path)

    def register_router(self, router):
        self.routers.append(router)

    def register_agent_tool(self, name, *, description, handler, parameters=None):
        assert name not in self.tools, f"{name} registered twice"
        self.tools[name] = {"description": description, "handler": handler, "parameters": parameters}

    def _write_data(self, name, text):
        if self.registered and name not in self.registered:
            raise PermissionError(f"{name} is not a registered data file")
        self.files[name] = text

    def _write_note(self, folder, name, frontmatter, body, *, vault=None):
        assert not Path(folder).is_absolute(), "write_note takes a vault-relative folder"
        target = self.root / folder / f"{name}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        head = "\n".join(f"{k}: {json.dumps(v)}" for k, v in frontmatter.items())
        target.write_text(f"---\n{head}\n---\n{body}", encoding="utf-8")
        return f"{folder}/{name}.md"

    def _run(self, job, profile=None):
        self.jobs.append((job, profile))
        return True

    def _set_enabled(self, pid, on):
        self.pipeline_states[pid]["cron_enabled"] = on

    def _set_schedule(self, pid, cron):
        self.pipeline_states[pid]["schedule"] = cron

    def switch_on(self, pid: str) -> None:
        self.pipeline_states[pid] = {"id": pid, "name": pid, "cron_job_id": f"job-{pid}",
                                     "cron_profile_id": None, "cron_enabled": True, "schedule": "0 6 * * 0"}


@pytest.fixture()
def api(tmp_path):
    return FakeApi(tmp_path)


@pytest.fixture()
def registered(api):
    import backend
    backend.register(api)
    return api


def call(api, name, **args):
    return json.loads(api.tools[name]["handler"](args, {"agent_id": "industry-researcher", "person_id": None}))


def route(api, path: str, method: str = "GET"):
    for router in api.routers:
        for r in router.routes:
            if r.path == path and method in r.methods:
                return r.endpoint
    raise AssertionError(f"no route {method} {path}")
