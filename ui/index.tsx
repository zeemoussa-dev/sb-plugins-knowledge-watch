import type { PluginUi } from '../../pluginHost/types';
import { KnowledgeWatchPage } from './KnowledgeWatchPage';
import { SettingsPage } from './SettingsPage';
import './knowledge-watch.css';

const ui: PluginUi = {
  routes: [{ path: '/knowledge-watch', component: KnowledgeWatchPage }],
  nav: [{ to: '/knowledge-watch', label: 'Knowledge Watch', icon: 'newspaper', group: 'knowledge' }],
  settingsPages: [
    {
      path: '',
      label: 'Knowledge Watch',
      description: 'The Knowledge scan and Knowledge weekly Pipelines, where the digest goes, and how the web is scanned.',
      component: SettingsPage,
    },
  ],
  help: [
    {
      id: 'knowledge-watch',
      title: 'Knowledge Watch',
      summary: 'Your weekly digest on the industry, the technologies and the topics you follow, every item filed, and your categories and topics.',
      body: '**Weekly digest** is the Sunday digest, newest first: headlines, one section per category and what '
        + 'to watch next week. It is also sent to you by chat and email, and filed as a note in the vault; '
        + '**Open the note** opens it there.\n\n'
        + '**News** lists every item the researcher filed, with its source, date and why it matters to Core42 '
        + '(the researcher\'s inference). Filter by category, period or words.\n\n'
        + '**Topics** is yours to change: **Add a topic**, open one to say what you want to know, give it its own '
        + 'search terms, sources to look at first and what to leave out, see its news, and **Refresh this topic now**.\n\n'
        + '**Settings** shows each job: on, off, running, failed or stopped, and why when it does not work. '
        + '**Refresh now** scans everything now, **Write the digest now** writes the digest, and each category '
        + 'can be refreshed on its own. Its **Agents** card links the Industry Expert and the Knowledge Expert '
        + 'to the install\'s Primary or to yours.\n\n'
        + 'Ask the **Industry Expert** about the market and the **Knowledge Expert** about a technology. Either '
        + 'one adds or tunes a topic, researches a topic into the vault, or refreshes the news when you ask. '
        + 'See the Knowledge Watch Guide in the Wiki for more.',
      keywords: ['industry', 'news', 'digest', 'weekly', 'ai', 'cloud', 'sovereign', 'gpu', 'data centre',
        'gulf', 'competitors', 'partners', 'topics', 'categories', 'interests', 'refresh', 'running', 'failed',
        'search terms', 'notes', 'expert', 'industry expert', 'knowledge expert', 'primary', 'research'],
      href: '/knowledge-watch',
    },
    {
      id: 'knowledge-watch-settings',
      title: 'Knowledge Watch settings',
      summary: 'The two Pipelines, where the weekly digest goes, and how the web is scanned.',
      body: 'Switch on **Knowledge scan** (Sunday, Tuesday and Thursday 06:00 Dubai) and **Knowledge weekly** '
        + '(Sunday 18:00 Dubai) here, change their schedules, or run one now. **Where the digest goes** sends it '
        + 'to a person on their chat, and by email from a mailbox you may send from. The settings set the vault '
        + 'folder, preferred and blocked sources, how far back a scan looks, and the scan and digest prompts. '
        + 'Every setting is optional: empty means the default.',
      keywords: ['settings', 'pipeline', 'schedule', 'delivery', 'email', 'sources', 'prompt'],
      href: '/settings/plugins/knowledge-watch',
    },
  ],
};

export default ui;
