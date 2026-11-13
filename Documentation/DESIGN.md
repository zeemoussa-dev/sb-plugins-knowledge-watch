# Knowledge Watch -- design

## 1. What the operator approved (2026-11-13)

| Question | Answer |
|---|---|
| Cadence | **Weekly digest only.** No daily alerts. The web is scanned a few times a week. |
| When | **Sunday 18:00 Dubai.** Strategic weekly is Monday 07:00, so the two do not land together. |
| Vault | **One weekly note** under `Work/Knowledge Watch/`, so other agents find it through search. |
| Links | **"Don't link it to the other Plugins."** No Entities registry, no Strategic Entities list. |
| Interests | **"We need the ability to include the knowledge categories and topics he is interested in."** Categories and topics are his to edit, on the main screen. |
| Screens | **Follow the framework's UI guidelines.** |
| Name | **Knowledge Watch**, not Industry Watch: "we have Topics and Technology Researches as well". |

## 2. Shape

```
Interests (categories -> topics)         data/KnowledgeWatch/interests.json
        | scan_brief
        v
knowledge-researcher (web)  --save_items-->  data/KnowledgeWatch/items.json
   Knowledge scan, Sun/Tue/Thu 06:00 Dubai
        | digest_facts (items since the last digest)
        v
knowledge-editor (no web)   --save_digest--> data/KnowledgeWatch/digests.json
   Knowledge weekly, Sun 18:00 Dubai          + Work/Knowledge Watch/Knowledge Watch <date>.md
        | last reply
        v
framework Pipeline delivery -> chat (person:<id>) and email (cbo-agent mailbox)
```

## 3. Who judges what

| Decision | Who |
|---|---|
| Which stories matter, their summary, importance, why they matter to Core42, the organisations they name | the researcher |
| What makes the headlines, the order, what it means for Core42 | the editor |
| A missing link, a blocked domain, a duplicate link, the per-scan limit, unknown sections | code (mechanical) |

## 4. Not in 1.0

- Daily alerts (declined).
- Links to Entities hubs or Strategic Entities companies (declined). A story naming a strategic company is not filtered out: the CBO's watchlist decides.
- A Home card.
