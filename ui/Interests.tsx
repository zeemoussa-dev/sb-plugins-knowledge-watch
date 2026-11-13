import { useEffect, useState } from 'react';
import {
  Checkbox, EditDrawer, EmptyState, Field, IconButton, LoadingState, Notice, SettingRow, SettingsGroup,
  SettingsSheet, SummaryChips, Toolbar, useConfirmation,
} from '../../pluginHost/framework';
import { fetchInterests, reason, resetInterests, saveInterests, type Category, type Topic } from './client';

const BLANK: Category = { id: '', name: '', about: '', enabled: true, topics: [{ name: '', notes: '' }] };

/** One category in its drawer: its name, why it matters, whether it is scanned, and
 *  its topics. Save writes the whole list; Cancel drops what was typed. */
function CategoryDrawer({ start, isNew, onClose, onSave, onDelete, saving }: {
  start: Category; isNew: boolean; saving: boolean;
  onClose: () => void; onSave: (category: Category) => void; onDelete: () => void;
}) {
  const [draft, setDraft] = useState<Category>(start);
  const named = draft.name.trim().length > 0;

  function topic(index: number, patch: Partial<Topic>) {
    setDraft({ ...draft, topics: draft.topics.map((one, i) => (i === index ? { ...one, ...patch } : one)) });
  }

  return (
    <EditDrawer
      title={isNew ? 'New category' : draft.name || 'Category'}
      description="A category is one beat the researcher scans and one section of the weekly digest."
      onClose={onClose} saving={saving} canSave={named}
      onSave={() => onSave({ ...draft, topics: draft.topics.filter((one) => one.name.trim()) })}
      destructive={isNew ? undefined : (
        <button type="button" className="btn btn-danger" onClick={onDelete}>Delete category</button>
      )}
      wide
    >
      <div className="stack">
        <Field label="Name" hint="Also the name of its section in the digest." error={named ? undefined : 'Give it a name.'}>
          <input className="input" value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} />
        </Field>
        <Field label="Why it matters to you" hint="Optional. The researcher is given it with every scan.">
          <input className="input" value={draft.about} onChange={(event) => setDraft({ ...draft, about: event.target.value })} />
        </Field>
        <Checkbox checked={draft.enabled} onChange={(checked) => setDraft({ ...draft, enabled: checked })}
                  label="Scan this category"
                  hint="Off keeps its topics but leaves it out of the scans and the digest." />
        <div className="iw-topics">
          <h3 className="iw-topics-title">Topics</h3>
          <p className="text-muted">Each topic is searched on its own. The note says what you want to know about it.</p>
          {draft.topics.map((one, index) => (
            <div className="iw-topic" key={index}>
              <Field label={`Topic ${index + 1}`}>
                <input className="input" value={one.name} onChange={(event) => topic(index, { name: event.target.value })} />
              </Field>
              <Field label="What you want to know">
                <input className="input" value={one.notes} onChange={(event) => topic(index, { notes: event.target.value })} />
              </Field>
              <IconButton icon="close" label={`Remove ${one.name || `topic ${index + 1}`}`}
                          onClick={() => setDraft({ ...draft, topics: draft.topics.filter((_, i) => i !== index) })} />
            </div>
          ))}
          <div>
            <button type="button" className="btn btn-sm"
                    onClick={() => setDraft({ ...draft, topics: [...draft.topics, { name: '', notes: '' }] })}>
              Add a topic
            </button>
          </div>
        </div>
      </div>
    </EditDrawer>
  );
}

/** The knowledge categories the CBO wants kept up to date, and the topics he is
 *  interested in inside each, as one sheet: a row per category, edited in a drawer.
 *  The researcher scans every category that is on; the digest has a section for each. */
export function Interests({ onCount }: { onCount?: (count: number) => void }) {
  const [rows, setRows] = useState<Category[] | null>(null);
  const [failed, setFailed] = useState('');
  const [done, setDone] = useState('');
  const [open, setOpen] = useState<number | 'new' | null>(null);
  const [saving, setSaving] = useState(false);
  const { confirm, confirmation } = useConfirmation();

  useEffect(() => {
    fetchInterests().then((found) => { setRows(found.categories); onCount?.(found.categories.length); },
      (error) => setFailed(reason(error)));
  }, [onCount]);

  function keep(next: Category[], said: string) {
    setSaving(true);
    setFailed('');
    saveInterests(next).then((saved) => {
      setRows(saved.categories);
      onCount?.(saved.categories.length);
      setOpen(null);
      setDone(said);
      setSaving(false);
    }, (error) => { setFailed(`The interests could not be saved: ${reason(error)}`); setSaving(false); });
  }

  async function remove(index: number) {
    if (!rows) return;
    const row = rows[index];
    if (!(await confirm({
      title: `Delete ${row.name}?`,
      body: `Its ${row.topics.length} topics are deleted and it is no longer scanned. News already filed under it stays on the News tab.`,
      confirmLabel: 'Delete category',
    }))) return;
    keep(rows.filter((_, i) => i !== index), `${row.name} was deleted. The next scan leaves it out.`);
  }

  async function reset() {
    if (!(await confirm({
      title: 'Put back the shipped categories?',
      body: 'Your categories and topics are replaced by the six Industry Watch ships. News already filed stays.',
      confirmLabel: 'Put back the shipped ones',
    }))) return;
    setSaving(true);
    resetInterests().then((saved) => {
      setRows(saved.categories);
      onCount?.(saved.categories.length);
      setDone('The shipped categories are back. The next scan uses them.');
      setSaving(false);
    }, (error) => { setFailed(`The categories could not be put back: ${reason(error)}`); setSaving(false); });
  }

  const editing = open === 'new' ? BLANK : (rows && open !== null ? rows[open] : null);

  return (
    <div className="stack">
      {failed && <Notice tone="error">{failed}</Notice>}
      {done && <Notice tone="success" onDismiss={() => setDone('')}>{done}</Notice>}
      <Toolbar end={(
        <>
          <button type="button" className="btn btn-ghost" disabled={saving || !rows} onClick={reset}>
            Put back the shipped ones
          </button>
          <button type="button" className="btn btn-primary" disabled={saving || !rows} onClick={() => setOpen('new')}>
            Add a category
          </button>
        </>
      )}>
        <span className="text-muted">
          Each category is a beat the researcher scans and a section of your weekly digest. A change counts from the next scan.
        </span>
      </Toolbar>
      {!rows && !failed && <LoadingState rows={6} label="Loading your interests" />}
      {rows && rows.length === 0 && (
        <EmptyState icon="interests" title="No categories yet"
                    action={<button type="button" className="btn btn-primary" onClick={() => setOpen('new')}>Add a category</button>}>
          Add the knowledge categories you want kept up to date, and the topics in each.
        </EmptyState>
      )}
      {rows && rows.length > 0 && (
        <SettingsSheet>
          <SettingsGroup title="Knowledge categories"
                         description={`${rows.filter((r) => r.enabled).length} of ${rows.length} are scanned.`}>
            {rows.map((row, index) => (
              <SettingRow key={row.id || index} icon={row.enabled ? 'topic' : 'block'} label={row.name}
                          summary={<SummaryChips items={row.topics.map((t) => t.name)} max={5} empty="No topics yet" />}
                          hint={row.enabled ? (row.about || `${row.topics.length} topics`) : 'Off: not scanned'}
                          onEdit={() => setOpen(index)} />
            ))}
          </SettingsGroup>
        </SettingsSheet>
      )}
      {editing && (
        <CategoryDrawer
          key={open === 'new' ? 'new' : editing.id}
          start={{ ...editing, topics: editing.topics.length ? editing.topics : [{ name: '', notes: '' }] }}
          isNew={open === 'new'} saving={saving}
          onClose={() => setOpen(null)}
          onDelete={() => { if (typeof open === 'number') remove(open); }}
          onSave={(category) => {
            const next = open === 'new' ? [...(rows ?? []), category]
              : (rows ?? []).map((one, i) => (i === open ? category : one));
            keep(next, `${category.name} was saved. The next scan uses it.`);
          }}
        />
      )}
      {confirmation}
    </div>
  );
}
