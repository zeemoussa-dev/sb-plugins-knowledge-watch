import { useState } from 'react';
import { Checkbox, ChoiceField, ChoicePicker, EditDrawer, Field, Notice } from '../../pluginHost/framework';
import { reason, saveDelivery, type DeliveryChoices, type PipelineDetail, type PipelineEmail } from './client';

const PERSON = 'person:';

export function personOf(deliver: string): { id: string; channel: string } | null {
  if (!deliver.startsWith(PERSON)) return null;
  const [id, channel = ''] = deliver.slice(PERSON.length).split(':');
  return { id, channel };
}

function addresses(text: string): string[] {
  return text.split(/[,;\s]+/).map((one) => one.trim()).filter(Boolean);
}

/** One line on where the digest goes now, for its row on the sheet. */
export function deliverySummary(pipeline: PipelineDetail, choices: DeliveryChoices): string {
  const target = personOf(pipeline.deliver || '');
  const parts = [];
  if (target) parts.push(`chat to ${choices.people.find((p) => p.id === target.id)?.name ?? target.id}`);
  else if (pipeline.deliver && pipeline.deliver !== 'local') parts.push(`chat ${pipeline.deliver}`);
  if (pipeline.email) {
    const count = pipeline.email.people.length + pipeline.email.to.length;
    parts.push(`email from ${pipeline.email.account_id} to ${count} ${count === 1 ? 'recipient' : 'recipients'}`);
  }
  return parts.length ? parts.join(' · ') : 'Not sent: kept in the run history only';
}

/** Where the weekly digest goes: a person on their chat, and an email from a mailbox.
 *  The framework sends it at the end of the run, not an agent, so no model picks who
 *  gets it. This sets only the Pipeline's own `deliver` and `email`, through the app's
 *  Pipelines API, with the signed-in person's rights (Agent Ops). */
export function DeliveryDrawer({ pipeline, choices, onClose, onSaved }: {
  pipeline: PipelineDetail; choices: DeliveryChoices; onClose: () => void; onSaved: (saved: PipelineDetail) => void;
}) {
  const target = personOf(pipeline.deliver || '');
  const otherChat = Boolean(pipeline.deliver && !target && pipeline.deliver !== 'local');
  const [person, setPerson] = useState(target?.id ?? '');
  const [channel, setChannel] = useState(target?.channel ?? '');
  const [mail, setMail] = useState(Boolean(pipeline.email));
  const [account, setAccount] = useState(pipeline.email?.account_id ?? choices.accounts[0]?.id ?? '');
  const [people, setPeople] = useState<string[]>(pipeline.email?.people ?? []);
  const [typed, setTyped] = useState((pipeline.email?.to ?? []).join(', '));
  const [subject, setSubject] = useState(pipeline.email?.subject ?? '');
  const [failed, setFailed] = useState('');
  const [saving, setSaving] = useState(false);
  const chosen = choices.people.find((one) => one.id === person);

  function save() {
    setSaving(true);
    setFailed('');
    const deliver = person ? `${PERSON}${person}${channel ? `:${channel}` : ''}` : (otherChat ? pipeline.deliver : '');
    const email: PipelineEmail | null = mail && account
      ? { account_id: account, people, to: addresses(typed), subject }
      : null;
    saveDelivery(pipeline, deliver, email).then(onSaved, (error) => {
      setFailed(`Where it goes could not be saved: ${reason(error)}`);
      setSaving(false);
    });
  }

  return (
    <EditDrawer title="Where the digest goes"
                description="At the end of each weekly run the framework sends the digest. No agent sends it, and no agent picks who gets it."
                onClose={onClose} onSave={save} saving={saving}>
      <div className="stack">
        {failed && <Notice tone="error">{failed}</Notice>}
        {otherChat && <Notice tone="info">It also goes to the chat {pipeline.deliver}, set in the Pipeline editor.</Notice>}
        <ChoiceField label="Send it on chat to" hint="People with no chat linked cannot be chosen.">
          <ChoicePicker label="Send it on chat to" value={person} onChange={(value) => { setPerson(value); setChannel(''); }}
                        options={[{ value: '', label: otherChat ? 'Only the chat above' : 'Nobody on chat' },
                          ...choices.people.map((one) => ({
                            value: one.id, label: one.name, disabled: !one.channels.length,
                            hint: one.channels.length ? one.channels.map((c) => choices.channel_labels[c] ?? c).join(', ') : 'no chat linked',
                          }))]} />
        </ChoiceField>
        {chosen && chosen.channels.length > 1 && (
          <ChoiceField label="On">
            <ChoicePicker label="On" value={channel} onChange={setChannel}
                          options={[{ value: '', label: 'Their usual chat' },
                            ...chosen.channels.map((one) => ({ value: one, label: choices.channel_labels[one] ?? one }))]} />
          </ChoiceField>
        )}
        <Checkbox checked={mail} disabled={!choices.accounts.length} onChange={setMail} label="Also email it"
                  hint={choices.accounts.length ? 'From a mailbox you may send from.'
                    : 'You may send from no mailbox: its owner allows it on Settings › Accounts.'} />
        {mail && (
          <>
            <ChoiceField label="From">
              <ChoicePicker label="From" value={account} onChange={setAccount}
                            options={choices.accounts.map((one) => ({ value: one.id, label: one.name ?? one.id, hint: one.address }))} />
            </ChoiceField>
            <ChoiceField label="To these people" hint="Their address comes from their profile.">
              <div className="kw-checks">
                {choices.people.map((one) => (
                  <Checkbox key={one.id} disabled={!one.has_email} checked={people.includes(one.id)}
                            label={one.name} hint={one.has_email ? undefined : 'no address on their profile'}
                            onChange={(checked) => setPeople((was) => (checked ? [...was, one.id] : was.filter((o) => o !== one.id)))} />
                ))}
              </div>
            </ChoiceField>
            <Field label="And these addresses" hint="Comma-separated. Only addresses the mailbox may send to are accepted.">
              <input className="input" value={typed} onChange={(event) => setTyped(event.target.value)} />
            </Field>
            <Field label="Subject" hint="Empty means the Pipeline's name, Knowledge weekly.">
              <input className="input" value={subject} onChange={(event) => setSubject(event.target.value)} />
            </Field>
          </>
        )}
      </div>
    </EditDrawer>
  );
}
