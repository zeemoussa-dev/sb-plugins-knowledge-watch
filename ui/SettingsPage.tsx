import { useCallback, useEffect, useState } from 'react';
import {
  Checkbox, EditDrawer, Field, LoadingState, Notice, NumberStepper, PageHeader, SettingRow, SettingsGroup,
  SettingsSheet, SummaryChips,
} from '../../pluginHost/framework';
import {
  changePipeline, fetchDeliveryChoices, fetchPipeline, fetchSettings, reason, runPipeline, saveSettings,
  type DeliveryChoices, type PipelineDetail, type PipelineState, type PluginSettings,
} from './client';
import { DeliveryDrawer, deliverySummary } from './Delivery';

export const SETTINGS_PATH = '/settings/plugins/knowledge-watch';

type TextKey = 'vault_folder' | 'preferred_domains' | 'blocked_domains' | 'scan_prompt' | 'digest_prompt';
type Open = { kind: 'pipeline'; id: string } | { kind: 'delivery' } | { kind: 'text'; key: TextKey }
  | { kind: 'scan-size' } | null;

const TEXTS: Record<TextKey, { label: string; hint: string; long: boolean }> = {
  vault_folder: { label: 'Vault folder', hint: 'Where each weekly digest is filed as a note, vault-relative.', long: false },
  preferred_domains: { label: 'Preferred sources', hint: 'Domains the researcher looks at first, comma-separated.', long: true },
  blocked_domains: { label: 'Blocked sources', hint: 'Domains never filed, comma-separated. A subdomain is blocked too.', long: false },
  scan_prompt: { label: 'How the web is scanned', hint: '{category}, {category_about}, {since}, {topics} and {preferred} are filled in.', long: true },
  digest_prompt: { label: 'How the digest is written', hint: 'The house style the editor follows.', long: true },
};

function domains(text: string): string[] {
  return text.split(/[,;]/).map((one) => one.trim()).filter(Boolean);
}

function pipelineSummary(state: PipelineState): string {
  if (!state.installed) return 'Not installed';
  const parts = [state.cron_job_id ? (state.cron_enabled ? 'On' : 'Off') : 'No job yet'];
  if (state.schedule) parts.push(state.schedule);
  parts.push(state.last_run ? `last ${state.last_run.slice(0, 16).replace('T', ' ')} (${state.last_status ?? '?'})` : 'never run');
  return parts.join(' · ');
}

/** A Pipeline's drawer: on or off, its schedule, and Run now. Save applies the first two. */
function PipelineDrawer({ state, onClose, onSaved, onSaid }: {
  state: PipelineState; onClose: () => void; onSaved: (said: string) => void; onSaid: (said: string) => void;
}) {
  const [on, setOn] = useState(Boolean(state.cron_enabled));
  const [schedule, setSchedule] = useState(state.schedule ?? '');
  const [failed, setFailed] = useState('');
  const [saving, setSaving] = useState(false);
  const name = state.name ?? state.id;

  function save() {
    setSaving(true);
    setFailed('');
    const change: { enabled?: boolean; schedule?: string } = {};
    if (schedule.trim() && schedule !== (state.schedule ?? '')) change.schedule = schedule.trim();
    if (on !== Boolean(state.cron_enabled)) change.enabled = on;
    changePipeline(state.id, change).then(() => onSaved(`${name} was saved: ${on ? 'on' : 'off'}, ${schedule}.`),
      (error) => { setFailed(`${name} could not be saved: ${reason(error)}`); setSaving(false); });
  }

  function run() {
    runPipeline(state.id).then((answer) => onSaid(answer.started
      ? `${name} started. Its report appears in Agent Activity.` : `${name} did not start: ${answer.note}.`),
    (error) => setFailed(`${name} could not be started: ${reason(error)}`));
  }

  return (
    <EditDrawer title={name} onClose={onClose} onSave={save} saving={saving}
                description={state.id === 'knowledge-scan'
                  ? 'Searches the web for every category and topic on the Topics tab and files what it finds. It sends nothing.'
                  : 'Writes the weekly digest from the items filed since the last one, and sends it where you set.'}
                secondary={(
                  <button type="button" className="btn" disabled={!state.cron_enabled || saving} onClick={run}
                          title={state.cron_enabled ? undefined : 'Only a Pipeline that is on can be run'}>
                    Run now
                  </button>
                )}>
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        <Checkbox checked={on} onChange={setOn} disabled={!state.cron_job_id} label="Switched on"
                  hint={state.cron_job_id ? 'Off keeps the schedule but never runs it.' : 'Give it a schedule first; the job is made on Save.'} />
        <Field label="Schedule" hint="A cron line. CRON_TZ=Asia/Dubai first reads the times in Dubai.">
          <input className="input mono" value={schedule} onChange={(event) => setSchedule(event.target.value)} />
        </Field>
        {state.next_run && <p className="text-muted">Next run {state.next_run.slice(0, 16).replace('T', ' ')} UTC.</p>}
      </div>
    </EditDrawer>
  );
}

/** One plugin setting's drawer: a line or a long text. Saving the default as written
 *  stores it as empty, so a later shipped default reaches this install. */
function TextDrawer({ settingKey, settings, onClose, onSaved }: {
  settingKey: TextKey; settings: PluginSettings; onClose: () => void; onSaved: (said: string) => void;
}) {
  const meta = TEXTS[settingKey];
  const [value, setValue] = useState(settings.values[settingKey] ?? '');
  const [failed, setFailed] = useState('');
  const [saving, setSaving] = useState(false);

  function save() {
    setSaving(true);
    saveSettings({ [settingKey]: value }).then((answer) => {
      const refused = answer.refused[settingKey];
      if (refused) { setFailed(`${meta.label} was not saved: ${refused}`); setSaving(false); return; }
      onSaved(`${meta.label} was saved. The next run uses it.`);
    }, (error) => { setFailed(`${meta.label} could not be saved: ${reason(error)}`); setSaving(false); });
  }

  return (
    <EditDrawer title={meta.label} onClose={onClose} onSave={save} saving={saving} wide={meta.long}
                secondary={(
                  <button type="button" className="btn btn-ghost" onClick={() => setValue(settings.defaults[settingKey] ?? '')}>
                    Use the default
                  </button>
                )}>
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        <Field label={meta.label} hint={meta.hint}>
          {meta.long
            ? <textarea className="input" rows={12} value={value} onChange={(event) => setValue(event.target.value)} />
            : <input className="input" value={value} onChange={(event) => setValue(event.target.value)} />}
        </Field>
      </div>
    </EditDrawer>
  );
}

function ScanSizeDrawer({ settings, onClose, onSaved }: {
  settings: PluginSettings; onClose: () => void; onSaved: (said: string) => void;
}) {
  const [horizon, setHorizon] = useState(Number(settings.values.horizon_days) || 7);
  const [most, setMost] = useState(Number(settings.values.max_items) || 6);
  const [failed, setFailed] = useState('');
  const [saving, setSaving] = useState(false);

  function save() {
    setSaving(true);
    saveSettings({ horizon_days: String(horizon), max_items: String(most) }).then((answer) => {
      const refused = Object.entries(answer.refused);
      if (refused.length) { setFailed(`Not saved: ${refused.map(([k, v]) => `${k} (${v})`).join('; ')}`); setSaving(false); return; }
      onSaved('How much a scan files was saved.');
    }, (error) => { setFailed(`It could not be saved: ${reason(error)}`); setSaving(false); });
  }

  return (
    <EditDrawer title="How much a scan files" onClose={onClose} onSave={save} saving={saving}>
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        <Field label="Look back" hint="How far back a scan looks for a category never scanned. Later scans look back to the last one.">
          <NumberStepper label="Look back" value={horizon} onChange={setHorizon} min={1} max={60} unit="days" />
        </Field>
        <Field label="Items per category per scan" hint="The researcher files the ones that matter most, up to this many.">
          <NumberStepper label="Items per category per scan" value={most} onChange={setMost} min={1} max={20} unit="items" />
        </Field>
      </div>
    </EditDrawer>
  );
}

/** The plugin's settings as one sheet: when it runs, where the digest goes, and how
 *  the web is scanned. An Admin Center page: the backend refuses a change without
 *  `manage_plugins`. The CBO's own categories and topics are on the Knowledge Watch
 *  screen's Topics tab. */
export function SettingsPage() {
  const [settings, setSettings] = useState<PluginSettings | null>(null);
  const [weekly, setWeekly] = useState<PipelineDetail | null>(null);
  const [choices, setChoices] = useState<DeliveryChoices | null>(null);
  const [deliveryFailed, setDeliveryFailed] = useState('');
  const [failed, setFailed] = useState('');
  const [done, setDone] = useState('');
  const [open, setOpen] = useState<Open>(null);

  const load = useCallback(() => {
    fetchSettings().then(setSettings, (error) => setFailed(`The settings could not be read: ${reason(error)}`));
    Promise.all([fetchDeliveryChoices(), fetchPipeline('knowledge-weekly')]).then(([offered, found]) => {
      setChoices(offered);
      setWeekly(found);
    }, (error) => setDeliveryFailed(reason(error)));
  }, []);
  useEffect(load, [load]);

  function saved(said: string) {
    setOpen(null);
    setDone(said);
    load();
  }

  const openPipeline = open?.kind === 'pipeline' ? settings?.pipelines.find((p) => p.id === open.id) : undefined;

  return (
    <>
      <PageHeader title="Knowledge Watch" description="When it runs, where the weekly digest goes, and how the web is scanned." />
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        {done && <Notice tone="success" onDismiss={() => setDone('')}>{done}</Notice>}
        {!settings && !failed && <LoadingState rows={8} label="Loading the settings" />}
        {settings && (
          <SettingsSheet>
            <SettingsGroup title="When it runs"
                           description="Both arrive switched off. Scanning needs a web search provider in Admin Center.">
              {settings.pipelines.map((state) => (
                <SettingRow key={state.id} icon={state.id === 'knowledge-scan' ? 'travel_explore' : 'newspaper'}
                            label={state.name ?? state.id} summary={pipelineSummary(state)}
                            hint={state.id === 'knowledge-scan' ? 'Files news; sends nothing.' : 'Writes and sends the digest.'}
                            disabled={!state.installed} onEdit={() => setOpen({ kind: 'pipeline', id: state.id })} />
              ))}
            </SettingsGroup>
            <SettingsGroup title="Where the digest goes">
              <SettingRow icon="send" label="Knowledge weekly"
                          summary={weekly && choices ? deliverySummary(weekly, choices)
                            : (deliveryFailed ? 'Needs the Agent Ops capability' : 'Loading…')}
                          hint={deliveryFailed ? deliveryFailed : 'By chat and by email, sent by the framework.'}
                          disabled={!weekly || !choices} onEdit={() => setOpen({ kind: 'delivery' })} />
            </SettingsGroup>
            <SettingsGroup title="How the web is scanned">
              <SettingRow icon="verified" label="Preferred sources"
                          summary={<SummaryChips items={domains(settings.values.preferred_domains)} max={5} empty="None" />}
                          onEdit={() => setOpen({ kind: 'text', key: 'preferred_domains' })} />
              <SettingRow icon="block" label="Blocked sources"
                          summary={<SummaryChips items={domains(settings.values.blocked_domains)} max={5} empty="None blocked" />}
                          onEdit={() => setOpen({ kind: 'text', key: 'blocked_domains' })} />
              <SettingRow icon="tune" label="How much a scan files"
                          summary={`Looks back ${settings.values.horizon_days} days · up to ${settings.values.max_items} items per category`}
                          onEdit={() => setOpen({ kind: 'scan-size' })} />
              <SettingRow icon="description" label="How the web is scanned"
                          summary={settings.values.scan_prompt === settings.defaults.scan_prompt ? 'The shipped prompt' : 'Your own prompt'}
                          onEdit={() => setOpen({ kind: 'text', key: 'scan_prompt' })} />
            </SettingsGroup>
            <SettingsGroup title="The digest">
              <SettingRow icon="edit_note" label="How the digest is written"
                          summary={settings.values.digest_prompt === settings.defaults.digest_prompt ? 'The shipped style' : 'Your own style'}
                          onEdit={() => setOpen({ kind: 'text', key: 'digest_prompt' })} />
              <SettingRow icon="folder" label="Vault folder" summary={<span className="mono">{settings.values.vault_folder}</span>}
                          hint="Each digest is also filed here as a note."
                          onEdit={() => setOpen({ kind: 'text', key: 'vault_folder' })} />
            </SettingsGroup>
          </SettingsSheet>
        )}
      </div>
      {openPipeline && (
        <PipelineDrawer state={openPipeline} onClose={() => setOpen(null)} onSaved={saved}
                        onSaid={(said) => { setOpen(null); setDone(said); }} />
      )}
      {open?.kind === 'delivery' && weekly && choices && (
        <DeliveryDrawer pipeline={weekly} choices={choices} onClose={() => setOpen(null)}
                        onSaved={(found) => { setWeekly(found); setOpen(null); setDone('Where the digest goes was saved. The next weekly is sent there.'); }} />
      )}
      {open?.kind === 'text' && settings && (
        <TextDrawer settingKey={open.key} settings={settings} onClose={() => setOpen(null)} onSaved={saved} />
      )}
      {open?.kind === 'scan-size' && settings && (
        <ScanSizeDrawer settings={settings} onClose={() => setOpen(null)} onSaved={saved} />
      )}
    </>
  );
}
