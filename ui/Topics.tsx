import { useEffect, useState } from 'react';
import {
  Checkbox, ChoiceField, ChoicePicker, EditDrawer, EmptyState, Field, LoadingState, Notice, SettingRow,
  SettingsGroup, SettingsSheet, SummaryChips, Toolbar, useConfirmation,
} from '../../pluginHost/framework';
import {
  BLANK_TOPIC, fetchInterests, fetchItems, reason, refresh, resetInterests, saveInterests, type Category, type Item,
  type Topic,
} from './client';

const BLANK_CATEGORY: Category = { id: '', name: '', about: '', enabled: true, topics: [] };

function lines(text: string): string[] {
  return text.split(/[\n,]/).map((one) => one.trim()).filter(Boolean);
}

/** What one topic has filed lately, newest first, so the CBO sees what his tuning brings. */
function TopicNews({ category, topic }: { category: string; topic: string }) {
  const [found, setFound] = useState<Item[] | null>(null);
  const [failed, setFailed] = useState('');

  useEffect(() => {
    fetchItems(category, 90, '', topic).then((answer) => setFound(answer.items),
      (error) => setFailed(`Its news could not be read: ${reason(error)}`));
  }, [category, topic]);

  if (failed) return <Notice tone="error">{failed}</Notice>;
  if (!found) return <LoadingState rows={2} label="Loading its news" />;
  if (!found.length) return <p className="text-muted">Nothing filed under it in the last 90 days.</p>;
  return (
    <div className="item-list">
      {found.slice(0, 8).map((item) => (
        <div className="item-row kw-item" key={item.id}>
          <a href={item.url} target="_blank" rel="noreferrer noopener" className="kw-item-title">{item.title}</a>
          <p className="text-muted kw-item-meta">{item.source}{item.published ? `, ${item.published}` : ''}</p>
        </div>
      ))}
    </div>
  );
}

/** One topic: what the CBO wants to know about it and how its search is tuned. Save
 *  writes the whole list. A saved topic can be refreshed now and shows its news. */
function TopicDrawer({ categories, start, startCategory, isNew, saving, mayRun, onClose, onSave, onDelete, onRefreshed }: {
  categories: Category[]; start: Topic; startCategory: string; isNew: boolean; saving: boolean; mayRun: boolean;
  onClose: () => void; onSave: (category: string, topic: Topic) => void; onDelete: () => void;
  onRefreshed: (said: string) => void;
}) {
  const [category, setCategory] = useState(startCategory);
  const [draft, setDraft] = useState<Topic>(start);
  const [terms, setTerms] = useState(start.search_terms.join('\n'));
  const [sources, setSources] = useState(start.sources.join(', '));
  const [failed, setFailed] = useState('');
  const [busy, setBusy] = useState(false);
  const named = draft.name.trim().length > 0;

  function runNow() {
    setBusy(true);
    setFailed('');
    refresh(startCategory, start.name).then(() => onRefreshed(
      `${start.name} is being scanned now. The Settings tab shows it running, and its news appears here when it is done.`),
    (error) => { setFailed(`It could not be refreshed: ${reason(error)}`); setBusy(false); });
  }

  return (
    <EditDrawer
      title={isNew ? 'New topic' : start.name}
      description="Each topic is searched on its own. Tune the search here; the next scan uses it."
      onClose={onClose} saving={saving} canSave={named && Boolean(category)} wide
      onSave={() => onSave(category, { ...draft, search_terms: lines(terms), sources: lines(sources) })}
      secondary={isNew ? undefined : (
        <button type="button" className="btn" disabled={busy || saving || !mayRun} onClick={runNow}
                title={mayRun ? undefined : 'Refreshing needs write access to the vault'}>
          {busy ? 'Starting…' : 'Refresh this topic now'}
        </button>
      )}
      destructive={isNew ? undefined : <button type="button" className="btn btn-danger" onClick={onDelete}>Delete topic</button>}
    >
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        {isNew && (
          <ChoiceField label="Category" hint="The section of the digest it appears in.">
            <ChoicePicker label="Category" value={category} onChange={setCategory}
                          options={categories.map((one) => ({ value: one.id, label: one.name }))} />
          </ChoiceField>
        )}
        <Field label="Topic" hint="A company, a product, a technology or a rule. Name it as the press does."
               error={named ? undefined : 'Give it a name.'}>
          <input className="input" value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} />
        </Field>
        <Field label="What you want to know" hint="The researcher reads this before every search.">
          <textarea className="input" rows={3} value={draft.notes}
                    onChange={(event) => setDraft({ ...draft, notes: event.target.value })} />
        </Field>
        <Field label="Search terms" hint="One search per line, run every scan. Empty: the researcher chooses its own.">
          <textarea className="input mono" rows={4} value={terms} onChange={(event) => setTerms(event.target.value)} />
        </Field>
        <Field label="Look first at" hint="Domains to check first for this topic, comma-separated, such as oracle.com.">
          <input className="input" value={sources} onChange={(event) => setSources(event.target.value)} />
        </Field>
        <Field label="Leave out" hint="What not to file under it, such as consumer products or share-price moves.">
          <input className="input" value={draft.leave_out} onChange={(event) => setDraft({ ...draft, leave_out: event.target.value })} />
        </Field>
        {!isNew && (
          <div className="stack">
            <h3 className="kw-subtitle">Its news</h3>
            <TopicNews category={startCategory} topic={start.name} />
          </div>
        )}
      </div>
    </EditDrawer>
  );
}

function CategoryDrawer({ start, isNew, saving, onClose, onSave, onDelete }: {
  start: Category; isNew: boolean; saving: boolean;
  onClose: () => void; onSave: (category: Category) => void; onDelete: () => void;
}) {
  const [draft, setDraft] = useState<Category>(start);
  const named = draft.name.trim().length > 0;
  return (
    <EditDrawer
      title={isNew ? 'New category' : start.name}
      description="A category is one beat the researcher scans and one section of the weekly digest. Its topics are rows under it."
      onClose={onClose} saving={saving} canSave={named} onSave={() => onSave(draft)}
      destructive={isNew ? undefined : <button type="button" className="btn btn-danger" onClick={onDelete}>Delete category</button>}
    >
      <div className="stack">
        <Field label="Name" hint="Also the name of its section in the digest." error={named ? undefined : 'Give it a name.'}>
          <input className="input" value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} />
        </Field>
        <Field label="Why it matters to you" hint="Optional. The researcher is given it with every scan.">
          <input className="input" value={draft.about} onChange={(event) => setDraft({ ...draft, about: event.target.value })} />
        </Field>
        <Checkbox checked={draft.enabled} onChange={(checked) => setDraft({ ...draft, enabled: checked })}
                  label="Scan this category" hint="Off keeps its topics but leaves it out of the scans and the digest." />
      </div>
    </EditDrawer>
  );
}

type Open = { kind: 'topic'; category: number; topic: number } | { kind: 'new-topic' }
  | { kind: 'category'; category: number } | { kind: 'new-category' } | null;

/** The knowledge categories the CBO follows and the topics in each, as one sheet: a
 *  group per category, a row per topic, each edited in its drawer. */
export function Topics({ mayRun, onCount, onRefreshed }: {
  mayRun: boolean; onCount?: (count: number) => void; onRefreshed?: () => void;
}) {
  const [rows, setRows] = useState<Category[] | null>(null);
  const [failed, setFailed] = useState('');
  const [done, setDone] = useState('');
  const [open, setOpen] = useState<Open>(null);
  const [saving, setSaving] = useState(false);
  const { confirm, confirmation } = useConfirmation();

  useEffect(() => {
    fetchInterests().then((found) => setRows(found.categories), (error) => setFailed(`Your topics could not be read: ${reason(error)}`));
  }, []);
  useEffect(() => { if (rows) onCount?.(rows.reduce((sum, one) => sum + one.topics.length, 0)); }, [rows, onCount]);

  function keep(next: Category[], said: string) {
    setSaving(true);
    setFailed('');
    saveInterests(next).then((saved) => {
      setRows(saved.categories);
      setOpen(null);
      setDone(said);
      setSaving(false);
    }, (error) => { setFailed(`Your topics could not be saved: ${reason(error)}`); setSaving(false); });
  }

  async function deleteCategory(index: number) {
    if (!rows) return;
    const row = rows[index];
    if (!(await confirm({
      title: `Delete ${row.name}?`,
      body: `Its ${row.topics.length} topics are deleted and it is no longer scanned. News already filed under it stays on the News tab.`,
      confirmLabel: 'Delete category',
    }))) return;
    keep(rows.filter((_, i) => i !== index), `${row.name} was deleted. The next scan leaves it out.`);
  }

  async function deleteTopic(category: number, topic: number) {
    if (!rows) return;
    const name = rows[category].topics[topic].name;
    if (!(await confirm({
      title: `Delete ${name}?`,
      body: 'It is no longer searched. News already filed under it stays on the News tab.',
      confirmLabel: 'Delete topic',
    }))) return;
    keep(rows.map((row, i) => (i === category ? { ...row, topics: row.topics.filter((_, j) => j !== topic) } : row)),
      `${name} was deleted. The next scan leaves it out.`);
  }

  async function reset() {
    if (!(await confirm({
      title: 'Put back the shipped topics?',
      body: 'Your categories and topics are replaced by the six categories Knowledge Watch ships. News already filed stays.',
      confirmLabel: 'Put back the shipped ones',
    }))) return;
    setSaving(true);
    resetInterests().then((saved) => {
      setRows(saved.categories);
      setDone('The shipped categories and topics are back. The next scan uses them.');
      setSaving(false);
    }, (error) => { setFailed(`They could not be put back: ${reason(error)}`); setSaving(false); });
  }

  function saveTopic(categoryId: string, topic: Topic) {
    if (!rows) return;
    const next = rows.map((row, i) => {
      if (row.id !== categoryId) return row;
      if (open?.kind === 'topic' && open.category === i) {
        return { ...row, topics: row.topics.map((one, j) => (j === open.topic ? topic : one)) };
      }
      return { ...row, topics: [...row.topics, topic] };
    });
    keep(next, `${topic.name} was saved. The next scan uses it.`);
  }

  const topicOpen = open?.kind === 'topic' && rows ? rows[open.category]?.topics[open.topic] : undefined;

  return (
    <div className="stack">
      {failed && <Notice tone="error">{failed}</Notice>}
      {done && <Notice tone="success" onDismiss={() => setDone('')}>{done}</Notice>}
      <Toolbar end={(
        <>
          <button type="button" className="btn btn-ghost" disabled={saving || !rows} onClick={reset}>Put back the shipped ones</button>
          <button type="button" className="btn" disabled={saving || !rows} onClick={() => setOpen({ kind: 'new-category' })}>
            Add a category
          </button>
          <button type="button" className="btn btn-primary" disabled={saving || !rows?.length}
                  onClick={() => setOpen({ kind: 'new-topic' })}>
            Add a topic
          </button>
        </>
      )}>
        <span className="text-muted">Open a topic to say what you want to know, tune its search, see its news and refresh it.</span>
      </Toolbar>
      {!rows && !failed && <LoadingState rows={8} label="Loading your topics" />}
      {rows && rows.length === 0 && (
        <EmptyState icon="topic" title="No categories yet"
                    action={<button type="button" className="btn btn-primary" onClick={() => setOpen({ kind: 'new-category' })}>Add a category</button>}>
          Add the knowledge categories you want kept up to date, then the topics in each.
        </EmptyState>
      )}
      {rows && rows.length > 0 && (
        <SettingsSheet>
          {rows.map((row, c) => (
            <SettingsGroup key={row.id || c} title={row.name}
                           description={`${row.enabled ? 'Scanned' : 'Off: not scanned'} · ${row.topics.length} topics${row.about ? ` · ${row.about}` : ''}`}>
              {row.topics.map((topic, t) => (
                <SettingRow key={topic.name} icon="tag" label={topic.name}
                            summary={topic.search_terms.length
                              ? <SummaryChips items={topic.search_terms} max={3} empty="" />
                              : (topic.notes || 'The researcher chooses its own searches')}
                            hint={[topic.sources.length ? `looks first at ${topic.sources.join(', ')}` : '',
                              topic.leave_out ? `leaves out ${topic.leave_out}` : ''].filter(Boolean).join(' · ') || undefined}
                            onEdit={() => setOpen({ kind: 'topic', category: c, topic: t })} />
              ))}
              <SettingRow icon="tune" label="This category"
                          summary={row.enabled ? 'Scanned every scan' : 'Switched off'}
                          hint="Its name, why it matters to you, on or off, or delete it."
                          onEdit={() => setOpen({ kind: 'category', category: c })} />
            </SettingsGroup>
          ))}
        </SettingsSheet>
      )}
      {rows && (open?.kind === 'new-topic' || topicOpen) && (
        <TopicDrawer
          key={open?.kind === 'topic' ? `${open.category}-${open.topic}` : 'new'}
          categories={rows} isNew={open?.kind === 'new-topic'} saving={saving} mayRun={mayRun}
          start={topicOpen ?? BLANK_TOPIC}
          startCategory={open?.kind === 'topic' ? rows[open.category].id : (rows[0]?.id ?? '')}
          onClose={() => setOpen(null)} onSave={saveTopic}
          onDelete={() => { if (open?.kind === 'topic') deleteTopic(open.category, open.topic); }}
          onRefreshed={(said) => { setOpen(null); setDone(said); onRefreshed?.(); }}
        />
      )}
      {rows && (open?.kind === 'new-category' || open?.kind === 'category') && (
        <CategoryDrawer
          key={open.kind === 'category' ? `c-${open.category}` : 'new-c'}
          start={open.kind === 'category' ? rows[open.category] : BLANK_CATEGORY}
          isNew={open.kind === 'new-category'} saving={saving}
          onClose={() => setOpen(null)}
          onDelete={() => { if (open.kind === 'category') deleteCategory(open.category); }}
          onSave={(category) => keep(open.kind === 'category'
            ? rows.map((one, i) => (i === open.category ? { ...category, topics: one.topics } : one))
            : [...rows, category], `${category.name} was saved.${open.kind === 'new-category' ? ' Add its topics with Add a topic.' : ''}`)}
        />
      )}
      {confirmation}
    </div>
  );
}
