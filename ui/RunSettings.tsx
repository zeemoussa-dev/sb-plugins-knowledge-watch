import { useState } from 'react';
import { Link } from 'react-router';
import {
  Card, DataTable, LoadingState, NameCell, Notice, ProgressBar, StatusBadge, Switch, type Column,
} from '../../pluginHost/framework';
import {
  changePipeline, reason, refresh, runPipeline, type PipelineHealth, type PipelineView, type Run, type RunState,
  type Status,
} from './client';
import { SETTINGS_PATH } from './SettingsPage';

type Tone = 'success' | 'info' | 'warning' | 'danger' | 'neutral';

const HEALTH: Record<PipelineHealth, { tone: Tone; label: string }> = {
  on: { tone: 'success', label: 'On' },
  running: { tone: 'info', label: 'Running' },
  failed: { tone: 'danger', label: 'Failed' },
  stopped: { tone: 'warning', label: 'Stopped' },
  off: { tone: 'neutral', label: 'Off' },
  'no job': { tone: 'warning', label: 'No job' },
  missing: { tone: 'danger', label: 'Missing' },
};

const RUN: Record<RunState, { tone: Tone; label: string }> = {
  requested: { tone: 'info', label: 'Starting' },
  running: { tone: 'info', label: 'Running' },
  done: { tone: 'success', label: 'Done' },
  failed: { tone: 'danger', label: 'Failed' },
  stopped: { tone: 'warning', label: 'Stopped' },
};

const TRIGGER: Record<Run['trigger'], string> = { schedule: 'On its schedule', 'run now': 'Run now', refresh: 'Refresh' };

export function when(stamp: string | null | undefined): string {
  if (!stamp) return '';
  const moment = new Date(stamp);
  if (Number.isNaN(moment.getTime())) return stamp.slice(0, 16);
  return moment.toLocaleString(undefined, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function scheduleText(schedule: string | null | undefined): string {
  return (schedule ?? '').replace(/^CRON_TZ=\S+\s+/, '');
}

function PipelineCard({ view, mayRun, mayAdmin, onChanged }: {
  view: PipelineView; mayRun: boolean; mayAdmin: boolean; onChanged: (said: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState('');
  const health = HEALTH[view.state];
  const name = view.name ?? view.id;
  const run = view.run;
  const expected = run?.categories.length ?? 0;
  const filedCount = run ? Object.keys(run.filed).length : 0;

  function start() {
    setBusy(true);
    setFailed('');
    runPipeline(view.id).then((answer) => {
      setBusy(false);
      if (answer.started) onChanged(`${name} started. It shows as running here until it is done.`);
      else setFailed(`${name} did not start: ${answer.note}.`);
    }, (error) => { setBusy(false); setFailed(`${name} could not be started: ${reason(error)}`); });
  }

  function switchTo(on: boolean) {
    setFailed('');
    changePipeline(view.id, { enabled: on }).then(() => onChanged(`${name} is switched ${on ? 'on' : 'off'}.`),
      (error) => setFailed(`${name} could not be switched ${on ? 'on' : 'off'}: ${reason(error)}`));
  }

  return (
    <Card title={name}
          description={view.kind === 'scan'
            ? 'Searches the web for every topic and files what it finds. It sends nothing.'
            : 'Writes the weekly digest from what was filed, and sends it.'}
          actions={<StatusBadge tone={health.tone}>{health.label}</StatusBadge>}>
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        {view.why && view.state !== 'running' && (
          <Notice tone={view.state === 'off' ? 'info' : 'warning'}>{view.why}</Notice>
        )}
        {run && (
          <ProgressBar value={view.kind === 'scan' ? filedCount : 0} max={Math.max(expected, 1)}
                       label={view.kind === 'scan'
                         ? `${run.state === 'requested' ? 'Starting' : 'Running'} since ${when(run.started_at)}: ${filedCount} of ${expected || '?'} categories filed`
                         : `Writing the digest since ${when(run.started_at)}`}
                       format={(value, max) => `${value} of ${max}`} />
        )}
        <div className="kv-list">
          <div className="kv-row">
            <span className="kv-key">Schedule</span>
            <span><span className="mono">{scheduleText(view.schedule) || 'none'}</span> (Dubai)</span>
          </div>
          <div className="kv-row">
            <span className="kv-key">Last run</span>
            <span>{view.last_run ? `${when(view.last_run)}, ${view.last_status ?? 'no status'}` : 'Never run'}</span>
          </div>
          <div className="kv-row">
            <span className="kv-key">Next run</span>
            <span>{view.cron_enabled && view.next_run ? when(view.next_run) : 'Not scheduled while it is off'}</span>
          </div>
        </div>
        <div className="kw-actions">
          <button type="button" className="btn btn-primary" disabled={busy || !mayRun || !view.cron_enabled || Boolean(run)}
                  onClick={start}
                  title={!view.cron_enabled ? 'Only a Pipeline that is on can be run' : undefined}>
            {busy ? 'Starting…' : (view.kind === 'scan' ? 'Refresh now' : 'Write the digest now')}
          </button>
          {mayAdmin && view.cron_job_id && (
            <Switch checked={Boolean(view.cron_enabled)} onChange={switchTo} label="Runs on its schedule" />
          )}
        </div>
      </div>
    </Card>
  );
}

/** How Knowledge Watch is doing, for the person who reads it: each Pipeline's state and,
 *  when it does not work, why; a refresh now; when each category was last scanned; and
 *  the recent runs. Delivery, sources and prompts stay on the Admin settings page. */
export function RunSettings({ status, failed, onChanged }: {
  status: Status | null; failed: string; onChanged: (said: string) => void;
}) {
  const [said, setSaid] = useState('');
  const [problem, setProblem] = useState('');

  function refreshCategory(category: string, name: string) {
    setProblem('');
    refresh(category).then(() => onChanged(`${name} is being scanned now.`),
      (error) => setProblem(`${name} could not be refreshed: ${reason(error)}`));
  }

  if (failed) return <Notice tone="error">{failed}</Notice>;
  if (!status) return <LoadingState rows={6} label="Loading how it is doing" />;

  const scanning = status.pipelines.some((p) => p.kind === 'scan' && p.run);
  const columns: Column<Status['last_scans'][number]>[] = [
    { key: 'name', header: 'Category', render: (row) => <NameCell name={row.category} sub={row.queries?.length ? `searched: ${row.queries.slice(0, 2).join('; ')}` : undefined} /> },
    { key: 'at', header: 'Last scanned', render: (row) => (row.at ? when(row.at) : 'Never'), align: 'end' },
    { key: 'saved', header: 'Filed', render: (row) => (row.at ? String(row.saved ?? 0) : '–'), align: 'end' },
    { key: 'refused', header: 'Refused', render: (row) => (row.at ? String(row.refused ?? 0) : '–'), align: 'end', hideBelow: 'md' },
    { key: 'refresh', header: '', align: 'end', render: (row) => (
      <button type="button" className="btn btn-ghost btn-sm" disabled={!status.may_run || scanning}
              onClick={() => refreshCategory(row.category_id, row.category)}>Refresh</button>
    ) },
  ];
  const runColumns: Column<Run>[] = [
    { key: 'what', header: 'Run', render: (run) => (
      <NameCell name={`${run.kind === 'scan' ? 'Scan' : 'Digest'} · ${TRIGGER[run.trigger]}`}
                sub={run.topic ? `topic ${run.topic}` : (run.category_names?.join(', ') || undefined)} />
    ) },
    { key: 'state', header: 'State', render: (run) => <StatusBadge tone={RUN[run.state].tone}>{RUN[run.state].label}</StatusBadge> },
    { key: 'started', header: 'Started', render: (run) => when(run.started_at), align: 'end' },
    { key: 'filed', header: 'Filed', align: 'end', hideBelow: 'md',
      render: (run) => (run.kind === 'scan' ? String(Object.values(run.filed).reduce((a, b) => a + b, 0)) : '–') },
    { key: 'why', header: 'What happened', hideBelow: 'sm',
      render: (run) => run.problem || run.reply || (run.by ? `asked by ${run.by}` : '') },
  ];

  return (
    <div className="stack">
      {problem && <Notice tone="error">{problem}</Notice>}
      {said && <Notice tone="success" onDismiss={() => setSaid('')}>{said}</Notice>}
      {!status.may_run && (
        <Notice tone="info">You can see how it is doing. Starting a run needs write access to the vault.</Notice>
      )}
      <div className="kw-grid">
        {status.pipelines.map((view) => (
          <PipelineCard key={view.id} view={view} mayRun={status.may_run} mayAdmin={status.may_admin}
                        onChanged={(text) => { setSaid(text); onChanged(text); }} />
        ))}
      </div>
      <Card title="Each category" description="When it was last scanned and what it filed. Refresh scans one category now.">
        <DataTable label="Each category's last scan" columns={columns} rows={status.last_scans}
                   rowKey={(row) => row.category_id} />
      </Card>
      <Card title="Recent runs" description="Newest first. A run that fails says why, in the words of the tool that failed.">
        <DataTable label="Recent runs" columns={runColumns} rows={status.runs} rowKey={(run) => run.id}
                   empty={<p className="text-muted">No run yet. Refresh now starts the first scan.</p>} />
      </Card>
      {status.may_admin && (
        <p className="text-muted">
          Where the digest goes, the sources and the prompts are on the{' '}
          <Link to={SETTINGS_PATH}>Admin settings page</Link>.
        </p>
      )}
    </div>
  );
}
