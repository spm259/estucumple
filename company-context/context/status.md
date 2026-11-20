# Status

As of 2026-11-19.

## Now
- Last founder-confirmed status: Es tu Cumple is not deployed or in use. This review did not inspect a deployment or the provider account.
- WhatsApp commands, per-user storage, and a daily reminder job exist in code.
- All 103 backend tests pass locally, including signed webhook and Spanish command flows with mocked outbound sends.
- The birthday command now rejects impossible calendar dates; February 29 in non-leap reminder years remains undecided.
- Adding the same contact name again ignores letter case and returns the original saved birthday for that user.
- Live WhatsApp conversation and reminder delivery remain unverified.
- Kapso v2, buffered v2, forwarded Meta, and legacy text payloads are parsed. Phone-less BSUID events are ignored.
- Webhooks require valid signatures. Replies run after acknowledgment; scheduling defaults to off for the sandbox.
- Frontend is an unconnected coming-soon page with no package manifest.
- Bot copy uses Mexican Spanish and Spanish commands, with English aliases preserved.

## This week
The first session's code and local checks are complete. The next check is a real sandbox conversation.
Launch is the Q4 goal. The [proposed plan](../../PLAN.md) records the November 12 review and delivery sequence; it is not founder-approved scope. Weekly priorities and launch date: UNKNOWN — ask founder.

## Blockers
On November 12, local preflight reported the Kapso API key, sandbox phone-number ID, and webhook secret missing or invalid. Sandbox activation and a public HTTPS webhook are still needed.
Production reminder-template approval: UNKNOWN — ask founder.
Durable deduplication, reply recovery, and delivery tracking remain unresolved launch work.
The November 12 review confirmed that the reminder trigger defaults to the host timezone. It needs to use `APP_TIMEZONE`.
Phone-less BSUID users are ignored by the current implementation; support remains a broader-release compatibility gap.

## Open questions
- What evidence and checks define a successful V1 launch?
- Which tasks should happen this week?
- What time and budget limits should guide implementation?
- What consent, retention, and approval rules apply?
- Is helping users send greetings limited to reminders, or is any additional workflow intended?

Sources include founder answers from October 4, the November 12 preflight and timezone check, and the November 19 code review and backend tests. Live provider and production verification are pending.
