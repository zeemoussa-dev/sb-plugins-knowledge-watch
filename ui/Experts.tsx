import { useCallback, useEffect, useState } from 'react';
import { Card, LoadingState, Notice, StatusBadge, SummaryChips } from '../../pluginHost/framework';
import {
  EXPERTS, INSTALL_PRIMARY, fetchAgent, fetchMyPrimary, reason, saveAskers, type AgentDetail,
} from './client';

interface Mine {
  agentId: string;
  own: boolean;
  problem: string;
}

/** The two Experts the CBO and his Primary ask, and who may ask them. Linking a Primary
 *  adds it to the Expert's `depends_on` through the app's own agents API, with the
 *  signed-in person's rights (`manage_agents`); the plugin's backend changes no agent. */
export function Experts() {
  const [agents, setAgents] = useState<Record<string, AgentDetail | string>>({});
  const [mine, setMine] = useState<Mine | null>(null);
  const [failed, setFailed] = useState('');
  const [done, setDone] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    EXPERTS.forEach((expert) => {
      fetchAgent(expert.id).then((found) => setAgents((was) => ({ ...was, [expert.id]: found })),
        (error) => setAgents((was) => ({ ...was, [expert.id]: reason(error) })));
    });
  }, []);

  useEffect(() => {
    load();
    fetchMyPrimary().then((found) => setMine({ agentId: found.agent_id || INSTALL_PRIMARY, own: Boolean(found.own), problem: '' }),
      (error) => setMine({ agentId: INSTALL_PRIMARY, own: false, problem: reason(error) }));
  }, [load]);

  async function link(primary: string, label: string) {
    setBusy(true);
    setFailed('');
    setDone('');
    const problems: string[] = [];
    for (const expert of EXPERTS) {
      const found = agents[expert.id];
      if (!found || typeof found === 'string') { problems.push(`${expert.name} is not on this install`); continue; }
      if (found.depends_on.includes(primary)) continue;
      try {
        await saveAskers(expert.id, [...found.depends_on, primary]);
      } catch (error) {
        problems.push(`${expert.name}: ${reason(error)}`);
      }
    }
    setBusy(false);
    load();
    if (problems.length) setFailed(`Not every Expert could be linked: ${problems.join('; ')}.`);
    else setDone(`${label} may now ask the Industry Expert and the Knowledge Expert.`);
  }

  const loaded = EXPERTS.every((expert) => agents[expert.id] !== undefined);
  const linkedTo = (primary: string) => EXPERTS.every((expert) => {
    const found = agents[expert.id];
    return found && typeof found !== 'string' && found.depends_on.includes(primary);
  });

  return (
    <Card title="Agents"
          description="Two Experts you, or your Primary, can ask. Both answer from the news filed here and the web, research a topic into the vault, refresh the knowledge data, and keep your topics.">
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        {done && <Notice tone="success" onDismiss={() => setDone('')}>{done}</Notice>}
        {!loaded && <LoadingState rows={2} label="Loading the Experts" />}
        {loaded && (
          <div className="item-list">
            {EXPERTS.map((expert) => {
              const found = agents[expert.id];
              return (
                <div className="item-row kw-item" key={expert.id}>
                  <div className="kw-item-head">
                    <strong>{expert.name}</strong>
                    <span className="mono text-muted">{expert.id}</span>
                    {typeof found === 'string'
                      ? <StatusBadge tone="danger">Missing</StatusBadge>
                      : <StatusBadge tone="success">Installed</StatusBadge>}
                  </div>
                  <p className="text-muted kw-item-meta">{expert.about}</p>
                  {typeof found === 'string'
                    ? <p className="kw-item-text">{found}. Reinstall the plugin to bring it back.</p>
                    : (
                      <div className="kw-item-head">
                        <span className="text-muted kw-item-meta">Who may ask it:</span>
                        <SummaryChips items={found.depends_on} max={6} empty="No agent yet" />
                      </div>
                    )}
                </div>
              );
            })}
          </div>
        )}
        {mine?.problem && <Notice tone="info">Which Primary you talk to could not be read: {mine.problem}. The install's Primary is used.</Notice>}
        <div className="kw-actions">
          <button type="button" className="btn" disabled={busy || !loaded || linkedTo(INSTALL_PRIMARY)}
                  onClick={() => link(INSTALL_PRIMARY, "The install's Primary")}>
            {linkedTo(INSTALL_PRIMARY) ? "Linked to the install's Primary" : "Link to the install's Primary"}
          </button>
          <button type="button" className="btn btn-primary"
                  disabled={busy || !loaded || !mine || linkedTo(mine.agentId)}
                  onClick={() => mine && link(mine.agentId, 'Your Primary')}>
            {busy ? 'Linking…' : (mine && linkedTo(mine.agentId) ? 'Linked to your Primary' : 'Link to my Primary')}
          </button>
          {mine && (
            <span className="text-muted">
              You talk to <span className="mono">{mine.agentId}</span>{mine.own ? ', your own Primary' : ", the install's Primary"}.
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
