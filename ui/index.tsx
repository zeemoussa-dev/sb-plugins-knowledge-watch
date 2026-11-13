import type { PluginUi } from '../../pluginHost/types';
import { IndustryWatchPage } from './IndustryWatchPage';
import { SettingsPage } from './SettingsPage';
import './industry-watch.css';

const ui: PluginUi = {
  routes: [{ path: '/industry-watch', component: IndustryWatchPage }],
  nav: [{ to: '/industry-watch', label: 'Industry Watch', icon: 'newspaper', group: 'knowledge' }],
  settingsPages: [
    {
      path: '',
      label: 'Industry Watch',
      description: 'The Industry scan and Industry weekly Pipelines, where the digest goes, and how the web is scanned.',
      component: SettingsPage,
    },
  ],
  help: [
    {
      id: 'industry-watch',
      title: 'Industry Watch',
      summary: 'Your weekly industry digest, every news item filed, and the categories and topics you follow.',
      body: '**Weekly digest** is the Sunday digest, newest first: headlines, one section per category and what '
        + 'to watch next week. It is also sent to you by chat and email, and filed as a note in the vault.\n\n'
        + '**News** lists every item the researcher filed, with its source, date and why it matters to Core42 '
        + '(the researcher\'s inference). Filter by category, period or words.\n\n'
        + '**Interests** is yours to change: add a knowledge category, add the topics you want followed in it, '
        + 'each with a note on what you want to know, or switch a category off. The next scan uses them. '
        + 'See the Industry Watch Guide in the Wiki for more.',
      keywords: ['industry', 'news', 'digest', 'weekly', 'ai', 'cloud', 'sovereign', 'gpu', 'data centre',
        'gulf', 'competitors', 'partners', 'topics', 'categories', 'interests'],
      href: '/industry-watch',
    },
    {
      id: 'industry-watch-settings',
      title: 'Industry Watch settings',
      summary: 'The two Pipelines, where the weekly digest goes, and how the web is scanned.',
      body: 'Switch on **Industry scan** (Sunday, Tuesday and Thursday 06:00 Dubai) and **Industry weekly** '
        + '(Sunday 18:00 Dubai) here, change their schedules, or run one now. **Where the digest goes** sends it '
        + 'to a person on their chat, and by email from a mailbox you may send from. The settings set the vault '
        + 'folder, preferred and blocked sources, how far back a scan looks, and the scan and digest prompts. '
        + 'Every setting is optional: empty means the default.',
      keywords: ['settings', 'pipeline', 'schedule', 'delivery', 'email', 'sources', 'prompt'],
      href: '/settings/plugins/industry-watch',
    },
  ],
};

export default ui;
