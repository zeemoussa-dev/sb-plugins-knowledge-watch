import { apiFetch, ApiError } from '../../pluginHost/api';

const BASE = '/plugins/knowledge-watch';

function send<T>(path: string, method: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, { method, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
}

/** What the backend refused, in its own words. */
export function reason(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      return JSON.parse(error.message).detail ?? error.message;
    } catch {
      return error.message;
    }
  }
  return String(error);
}

// -- the CBO's interests ------------------------------------------------------------

export interface Topic {
  name: string;
  notes: string;
  /** Searches the CBO wants run for this topic. */
  search_terms: string[];
  /** Domains to look at first for this topic. */
  sources: string[];
  /** What he does not want filed under it. */
  leave_out: string;
}

export const BLANK_TOPIC: Topic = { name: '', notes: '', search_terms: [], sources: [], leave_out: '' };

export interface Category {
  id: string;
  name: string;
  about: string;
  enabled: boolean;
  topics: Topic[];
}

export function fetchInterests(): Promise<{ categories: Category[]; limits: { categories: number; topics: number } }> {
  return apiFetch(`${BASE}/interests`);
}

export function saveInterests(categories: Category[]): Promise<{ categories: Category[] }> {
  return send(`${BASE}/interests`, 'PUT', { categories });
}

export function resetInterests(): Promise<{ categories: Category[] }> {
  return send(`${BASE}/interests/reset`, 'POST');
}

// -- the news and the digests -------------------------------------------------------

export interface Item {
  id: string;
  url: string;
  title: string;
  source: string;
  published: string;
  category: string;
  category_name: string;
  topic: string;
  summary: string;
  why_it_matters: string;
  importance: 'high' | 'medium' | 'low';
  companies: string[];
  found_at: string;
}

export function fetchItems(category: string, days: number, q: string, topic = ''): Promise<{
  items: Item[]; categories: { id: string; name: string }[];
}> {
  const query = new URLSearchParams({ category, topic, days: String(days), q });
  return apiFetch(`${BASE}/items?${query.toString()}`);
}

export interface DigestEntry {
  id: string;
  at: string;
  week: string;
  headline: string;
  items: number;
  note: string;
}

export interface Digest extends DigestEntry {
  sections: Record<string, string>;
  markdown: string;
  sources: string[];
}

export function fetchDigests(): Promise<DigestEntry[]> {
  return apiFetch(`${BASE}/digests`);
}

export function fetchDigest(id: string): Promise<Digest> {
  return apiFetch(`${BASE}/digests/${encodeURIComponent(id)}`);
}

export interface PipelineState {
  id: string;
  installed: boolean;
  name?: string;
  cron_job_id?: string | null;
  cron_enabled?: boolean | null;
  schedule?: string | null;
  last_run?: string | null;
  next_run?: string | null;
  last_status?: string | null;
}

export type RunState = 'requested' | 'running' | 'done' | 'failed' | 'stopped';

export interface Run {
  id: string;
  kind: 'scan' | 'digest';
  trigger: 'schedule' | 'run now' | 'refresh';
  state: RunState;
  requested_at: string;
  started_at: string;
  finished_at: string;
  category: string;
  topic: string;
  by: string;
  categories: string[];
  /** Every category the run is to scan; `categories` are those handed out so far. */
  expected?: string[];
  category_names?: string[];
  filed: Record<string, number>;
  refused: Record<string, number>;
  problem: string;
  reply: string;
}

export type PipelineHealth = 'missing' | 'no job' | 'running' | 'failed' | 'stopped' | 'off' | 'on';

export interface PipelineView extends PipelineState {
  kind: 'scan' | 'digest';
  state: PipelineHealth;
  why: string;
  run: Run | null;
}

export interface Status {
  categories: number;
  topics: number;
  items_week: number;
  last_scans: { category: string; category_id: string; at?: string; saved?: number; refused?: number; queries?: string[] }[];
  pipelines: PipelineView[];
  runs: Run[];
  may_run: boolean;
  may_admin: boolean;
}

export function refresh(category: string, topic = ''): Promise<{ started: boolean; run: Run }> {
  return send(`${BASE}/refresh`, 'POST', { category, topic });
}

export function fetchStatus(): Promise<Status> {
  return apiFetch(`${BASE}/status`);
}

// -- research notes ------------------------------------------------------------------

export interface ResearchNote {
  category: string;
  topic: string;
  title: string;
  at: string;
  note: string;
  by: string;
  summary: string;
}

export function fetchResearch(category: string, topic: string): Promise<ResearchNote[]> {
  const query = new URLSearchParams({ category, topic });
  return apiFetch(`${BASE}/research?${query.toString()}`);
}

/** The vault's own note page, by the note's path or name. */
export function notePath(note: string): string {
  const stem = note.split('/').pop()?.replace(/\.md$/, '') ?? note;
  return `/browse/${encodeURIComponent(stem)}`;
}

// -- the Experts, and who may ask them (the app's own agents API) ---------------------

export const EXPERTS = [
  { id: 'industry-expert', name: 'Industry Expert', about: 'The industry and the market: competitors, partners, hyperscalers, model providers, deals and the Gulf market.' },
  { id: 'knowledge-expert', name: 'Knowledge Expert', about: 'Technologies and topics: what they are, where they stand, research filed in the vault, and your topics.' },
] as const;

/** The install's own Primary: whoever has no Primary of their own talks to it. */
export const INSTALL_PRIMARY = 'default';

export interface AgentDetail {
  id: string;
  name: string;
  depends_on: string[];
}

export function fetchAgent(id: string): Promise<AgentDetail> {
  return apiFetch(`/agents/${encodeURIComponent(id)}`);
}

/** Who may ask an agent is its `depends_on`. Changing it needs `manage_agents`. */
export function saveAskers(id: string, dependsOn: string[]): Promise<unknown> {
  return send(`/agents/${encodeURIComponent(id)}`, 'PATCH', { depends_on: dependsOn });
}

/** The agent the signed-in person talks to; none means the install's Primary. */
export function fetchMyPrimary(): Promise<{ agent_id: string | null; own: boolean }> {
  return apiFetch('/me/primary');
}

// -- the plugin's Settings page ---------------------------------------------------

export interface PluginSettings {
  values: Record<string, string>;
  defaults: Record<string, string>;
  pipelines: PipelineState[];
}

export function fetchSettings(): Promise<PluginSettings> {
  return apiFetch(`${BASE}/settings`);
}

export function saveSettings(values: Record<string, string>): Promise<{
  values: Record<string, string>; refused: Record<string, string>;
}> {
  return send(`${BASE}/settings`, 'PUT', values);
}

export function changePipeline(id: string, change: { enabled?: boolean; schedule?: string }): Promise<PipelineState> {
  return send(`${BASE}/pipelines/${encodeURIComponent(id)}`, 'PUT', change);
}

export function runPipeline(id: string): Promise<{ started: boolean; note: string }> {
  return send(`${BASE}/pipelines/${encodeURIComponent(id)}/run`, 'POST');
}

// -- the framework's own Pipelines API: where the digest goes ------------------------

export interface DeliveryChoices {
  people: { id: string; name: string; channels: string[]; has_email: boolean }[];
  channel_labels: Record<string, string>;
  accounts: { id: string; name?: string; address?: string; label?: string }[];
}

export interface PipelineEmail {
  account_id: string;
  to: string[];
  people: string[];
  subject: string;
  set_by?: string;
}

export interface PipelineDetail {
  id: string;
  name: string;
  description: string;
  section_id: string;
  steps: { id: string; name: string; description?: string; type: string; agent_id: string; instruction: string }[];
  cron_enabled: boolean | null;
  cron_schedule: string | null;
  deliver: string;
  email: PipelineEmail | null;
}

export function fetchDeliveryChoices(): Promise<DeliveryChoices> {
  return apiFetch('/pipelines/delivery-choices');
}

export function fetchPipeline(id: string): Promise<PipelineDetail> {
  return apiFetch(`/pipelines/${encodeURIComponent(id)}`);
}

/** Saves where the result goes, keeping everything else as it is: `PUT
 *  /pipelines/{id}` takes the whole Pipeline, so its steps, schedule and on/off are
 *  sent back unchanged. */
export function saveDelivery(pipeline: PipelineDetail, deliver: string, email: PipelineEmail | null): Promise<PipelineDetail> {
  return send(`/pipelines/${encodeURIComponent(pipeline.id)}`, 'PUT', {
    name: pipeline.name,
    description: pipeline.description,
    section_id: pipeline.section_id || null,
    steps: pipeline.steps.map((step) => ({
      id: step.id, name: step.name, agent_id: step.agent_id, instruction: step.instruction, type: step.type,
    })),
    schedule: pipeline.cron_schedule ?? '',
    scheduled: Boolean(pipeline.cron_enabled),
    deliver,
    email: email ? { account_id: email.account_id, to: email.to, people: email.people, subject: email.subject } : null,
  });
}
