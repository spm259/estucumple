# Status

As of 2026-10-05.

## Now
- Founder confirms Es tu Cumple is not deployed or in use.
- WhatsApp commands, per-user storage, and a daily reminder job exist in code.
- All 60 backend tests pass locally on Python 3.12, including signed webhook and Spanish command flows with mocked outbound sends.
- Live WhatsApp conversation and reminder delivery remain unverified.
- Kapso v2, buffered v2, forwarded Meta, and legacy text payloads are parsed. Phone-less BSUID events are ignored.
- Webhooks require valid signatures. Replies run after acknowledgment; scheduling defaults to off for the sandbox.
- Frontend is an unconnected coming-soon page with no package manifest.
- Bot copy uses Mexican Spanish and Spanish commands, with English aliases preserved.

## This week
The first session's code and local checks are complete. The next check is a real sandbox conversation.
Launch is the Q4 goal. Other weekly priorities and launch date: UNKNOWN — ask founder.

## Blockers
Local Kapso API key, sandbox phone-number ID, and webhook secret are missing. Sandbox activation and a public HTTPS webhook are still needed.
Production reminder-template approval: UNKNOWN — ask founder.
Durable deduplication, reply recovery, and full calendar validation remain unresolved launch work.

## Open questions
- What evidence and checks define a successful V1 launch?
- Which tasks should happen this week?
- What time and budget limits should guide implementation?
- What consent, retention, and approval rules apply?
- Is helping users send greetings limited to reminders, or is any additional workflow intended?

Sources: founder answers on 2026-10-04; code, local preflight, and backend tests on 2026-10-05. No live provider or production checks were performed.
