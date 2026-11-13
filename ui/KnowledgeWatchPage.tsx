import { useCallback, useEffect, useState } from 'react';
import {
  Card, ChoiceField, ChoicePicker, EmptyState, LoadingState, Notice, PageHeader, SearchField, SegmentedChoice,
  StatTiles, StatusBadge, Tabs, Toolbar,
} from '../../pluginHost/framework';
import { NoteText } from '../../pluginHost/noteText';
import { useUrlState } from '../../pluginHost/state';
import {
  fetchDigest, fetchDigests, fetchItems, fetchStatus, reason, type Digest, type DigestEntry, type Item, type Status,
} from './client';
import { Interests } from './Interests';

export const PAGE = '/knowledge-watch';
const TABS = ['digest', 'news', 'interests'] as const;
type Tab = (typeof TABS)[number];
const PERIODS = ['7', '30', '90', '180'] as const;
type Period = (typeof PERIODS)[number];
const IMPORTANCE_TONE: Record<Item['importance'], 'accent' | 'info' | 'neutral'> = { high: 'accent', medium: 'info', low: 'neutral' };

function when(stamp: string | null | undefined): string {
  return stamp ? stamp.slice(0, 16).replace('T', ' ') : '';
}

function Overview({ status, digests }: { status: Status | null; digests: DigestEntry[] | null }) {
  if (!status) return <LoadingState rows={1} label="Loading the figures" />;
  const off = status.pipelines.filter((p) => !p.installed || !p.cron_enabled);
  return (
    <>
      <StatTiles label="Knowledge Watch at a glance" stats={[
        { key: 'categories', label: 'Categories scanned', value: status.categories },
        { key: 'topics', label: 'Topics followed', value: status.topics },
        { key: 'week', label: 'Items in the last 7 days', value: status.items_week },
        { key: 'digest', label: 'Last digest', value: digests?.[0]?.week ?? 'none yet',
          note: digests?.[0] ? `${digests[0].items} items` : 'Sunday 18:00 Dubai' },
      ]} />
      {off.length > 0 && (
        <Notice tone="info">
          {off.map((p) => p.name ?? p.id).join(' and ')} {off.length > 1 ? 'are' : 'is'} switched off, so
          {off.length > 1 ? ' they do' : ' it does'} not run. An Admin switches {off.length > 1 ? 'them' : 'it'} on
          in Admin Center, on the Knowledge Watch settings page.
        </Notice>
      )}
    </>
  );
}

function Digests({ rows, failed }: { rows: DigestEntry[] | null; failed: string }) {
  const [chosen, setChosen] = useUrlState<string>('digest', '');
  const [open, setOpen] = useState<Digest | null>(null);
  const [error, setError] = useState('');
  const id = chosen || rows?.[0]?.id || '';

  useEffect(() => {
    if (!id) return;
    setError('');
    fetchDigest(id).then(setOpen, (problem) => setError(`The digest could not be read: ${reason(problem)}`));
  }, [id]);

  if (failed) return <Notice tone="error">{failed}</Notice>;
  if (!rows) return <LoadingState rows={6} label="Loading the digests" />;
  if (!rows.length) {
    return (
      <EmptyState icon="newspaper" title="No digest yet">
        Knowledge weekly writes one every Sunday at 18:00 Dubai from what the scans filed that week.
      </EmptyState>
    );
  }
  // Newest first: the digest you want is almost always this week's.
  return (
    <div className="stack">
      {rows.length > 1 && (
        <ChoiceField label="Week">
          <ChoicePicker label="Week" value={id} onChange={setChosen}
                        options={rows.map((row) => ({ value: row.id, label: `Week to ${row.week}`, hint: `${row.items} items` }))} />
        </ChoiceField>
      )}
      {error && <Notice tone="error">{error}</Notice>}
      {!open && !error && <LoadingState rows={8} label="Loading the digest" />}
      {open && (
        <Card title={`Week to ${open.week}`}
              description={`Written by the Knowledge Editor on ${when(open.at)} from ${open.items} items the Knowledge Researcher filed.`}>
          {open.note.startsWith('not filed') && <Notice tone="warning">The vault note was {open.note}.</Notice>}
          <NoteText text={open.markdown} />
          {open.note && !open.note.startsWith('not filed') && (
            <p className="text-muted">Filed in the vault as <span className="mono">{open.note}</span>.</p>
          )}
        </Card>
      )}
    </div>
  );
}

function News({ onCount }: { onCount: (count: number) => void }) {
  const [category, setCategory] = useUrlState<string>('category', '');
  const [period, setPeriod] = useUrlState<Period>('days', '30', { valid: PERIODS });
  const [q, setQ] = useState('');
  const [found, setFound] = useState<{ items: Item[]; categories: { id: string; name: string }[] } | null>(null);
  const [failed, setFailed] = useState('');

  useEffect(() => {
    const timer = window.setTimeout(() => {
      fetchItems(category, Number(period), q).then((answer) => {
        setFound(answer);
        setFailed('');
        if (!category && !q && period === '30') onCount(answer.items.length);
      }, (error) => setFailed(`The news could not be read: ${reason(error)}. Try again in a moment.`));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [category, period, q, onCount]);

  const filtered = Boolean(category || q);
  const categoryName = found?.categories.find((one) => one.id === category)?.name;

  return (
    <div className="stack">
      <Toolbar>
        <SearchField value={q} onChange={setQ} placeholder="Search titles, topics and companies" />
        <SegmentedChoice label="Period" value={period} onChange={(value) => setPeriod(value as Period)}
                         options={[{ value: '7', label: '7 days' }, { value: '30', label: '30 days' },
                           { value: '90', label: '90 days' }, { value: '180', label: '180 days' }]} />
      </Toolbar>
      {found && found.categories.length > 0 && (
        <ChoiceField label="Category">
          <ChoicePicker label="Category" value={category} onChange={setCategory}
                        options={[{ value: '', label: 'Every category' },
                          ...found.categories.map((one) => ({ value: one.id, label: one.name }))]} />
        </ChoiceField>
      )}
      {failed && <Notice tone="error">{failed}</Notice>}
      {!found && !failed && <LoadingState rows={6} label="Loading the news" />}
      {found && found.items.length === 0 && (filtered ? (
        <EmptyState icon="search_off" title="Nothing matches"
                    action={<button type="button" className="btn" onClick={() => { setCategory(''); setQ(''); }}>Clear the filter</button>}>
          No item{categoryName ? ` in ${categoryName}` : ''}{q ? ` mentions “${q}”` : ''} in the last {period} days.
        </EmptyState>
      ) : (
        <EmptyState icon="newspaper" title="No news filed yet">
          Knowledge scan files items on Sunday, Tuesday and Thursday at 06:00 Dubai once it is switched on.
        </EmptyState>
      ))}
      {found && found.items.length > 0 && (
        // Newest first, as filed: this is the week's history.
        <Card padded={false}>
          <div className="item-list">
            {found.items.map((item) => (
              <article className="item-row kw-item" key={item.id}>
                <div className="kw-item-head">
                  <StatusBadge tone={IMPORTANCE_TONE[item.importance]}>{item.importance}</StatusBadge>
                  <a href={item.url} target="_blank" rel="noreferrer noopener" className="kw-item-title">{item.title}</a>
                </div>
                <p className="text-muted kw-item-meta">
                  {item.source}{item.published ? `, ${item.published}` : ''} · {item.category_name}
                  {item.topic ? ` › ${item.topic}` : ''}
                </p>
                <p className="kw-item-text">{item.summary}</p>
                {item.why_it_matters && (
                  <p className="kw-item-text text-muted">
                    <strong>Why it matters, the researcher&apos;s inference:</strong> {item.why_it_matters}
                  </p>
                )}
                {item.companies.length > 0 && (
                  <div className="kw-tags">{item.companies.map((one) => <span className="badge" key={one}>{one}</span>)}</div>
                )}
              </article>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

/** The CBO's industry, technology and topic news: the weekly digests, every item filed, and the knowledge
 *  categories and topics he wants followed, one section per tab. */
export function KnowledgeWatchPage() {
  const [tab, setTab] = useUrlState<Tab>('tab', 'digest', { valid: TABS });
  const [status, setStatus] = useState<Status | null>(null);
  const [digests, setDigests] = useState<DigestEntry[] | null>(null);
  const [digestsFailed, setDigestsFailed] = useState('');
  const [newsCount, setNewsCount] = useState<number | undefined>(undefined);
  const [categoryCount, setCategoryCount] = useState<number | undefined>(undefined);
  const countNews = useCallback((count: number) => setNewsCount(count), []);
  const countCategories = useCallback((count: number) => setCategoryCount(count), []);

  useEffect(() => {
    fetchStatus().then((found) => { setStatus(found); setCategoryCount((was) => was ?? found.categories); },
      () => setStatus(null));
    fetchDigests().then(setDigests, (error) => setDigestsFailed(`The digests could not be read: ${reason(error)}`));
  }, []);

  return (
    <>
      <PageHeader title="Knowledge Watch"
                  description="The industry, the technologies and the topics you follow, in the knowledge categories you choose." />
      <div className="stack">
        <Overview status={status} digests={digests} />
        <Tabs label="Knowledge Watch" value={tab} onChange={(value) => setTab(value as Tab)}
              tabs={[{ value: 'digest', label: 'Weekly digest', count: digests?.length },
                { value: 'news', label: 'News', count: newsCount ?? status?.items_week },
                { value: 'interests', label: 'Interests', count: categoryCount }]} />
        {tab === 'digest' && <Digests rows={digests} failed={digestsFailed} />}
        {tab === 'news' && <News onCount={countNews} />}
        {tab === 'interests' && <Interests onCount={countCategories} />}
      </div>
    </>
  );
}
