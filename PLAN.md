# Es tu Cumple: proposed launch plan

Reviewed November 12, 2026. This is a recommendation from the repository review,
not a record of founder-approved scope or a delivery-date commitment.

## Recommendation

Keep the original product and the existing Python backend. A person saves birthdays
in WhatsApp and receives one message on days when someone has a birthday. Kapso
handles WhatsApp transport; FastAPI and SQLAlchemy handle the product's data and
commands. Continue with short commands in Mexican Spanish.

The next milestone is a reminder received on a real phone after more than 24 hours
without a user message. Passing local tests or exchanging sandbox replies does not
prove that central use case.

## What the review established

| Area | Current evidence | Implication |
| --- | --- | --- |
| Commands and storage | Add/list/delete/help, per-user contacts, optional birth year | Reuse the implementation. |
| Calendar dates | The command parser rejects impossible dates and accepts February 29 appropriately; schema fields still only validate ranges | The command fix is done. Keep validation consistent if another write path is added. |
| Local verification | On November 12, `venv/bin/python -m pytest backend/tests -q` passed all 96 tests | Useful regression coverage; outbound sends are mocked. |
| Kapso setup | Local preflight reports API key, phone-number ID, and webhook secret missing or invalid | Configure these privately before live tests. |
| Reminders | Templates, daily grouping, and sequential same-day suppression exist | Delivery, recovery, and overlapping runs remain unproven. |
| Scheduler | An explicitly constructed `CronTrigger` has no timezone; locally it resolves to America/New_York while the app is configured for America/Argentina/Buenos_Aires | Pass the configured timezone to the trigger and test it independently of the host timezone. |
| Webhooks | Signatures verified; replay tracking and deferred replies are in memory | Restarting can repeat a command or lose a reply. Batch retries can replay earlier committed commands. |
| Delivery status | A successful send response causes a reminder log entry; provider message IDs and later delivery/failure events are not tracked | API acceptance currently stands in for delivery. |
| Identity | Users require a phone number; phone-less BSUID events are ignored | A known limitation for a controlled phone-based test, and a compatibility gap before broader release. |
| Frontend | Unconnected coming-soon page, no package manifest | It is outside the critical path. |

The last founder-confirmed deployment status was “not deployed or in use.” This
review did not access a live deployment or the Kapso account.

## Delivery sequence

### 1. Prove the WhatsApp conversation

Use the README sandbox instructions, configure the three missing secrets locally,
activate the test phone, expose an HTTPS webhook, and keep reminders disabled.
Use a phone-number WhatsApp webhook with buffering off initially.

Run `hola → agregar María 25/05 → lista → borrar María → lista`. Repeat with a
second activated phone to check isolation. Check invalid dates and a repeated
webhook. Before deleting the contact, try `agregar MARÍA 26/05`. Expect the bot
to show the saved date (`25/05`) and `lista` to show one entry for María.
Record the date and outcome without retaining personal payloads in docs.

Done when both phones receive the expected replies and see only their own data.

### 2. Prove the actual reminder

Start production-number connection and template review early, alongside step 1.
Use one app-owned sender number for users of Es tu Cumple. Users should only need
to chat with the bot; they should not connect their own business accounts.

Submit a short reminder template with representative examples, such as:

> Recordatorio de Es tu Cumple: hoy cumple años {{1}}.

Use the exact approved template name, language, and parameter structure. Approval
and category are not guaranteed; check what Meta actually approves before
estimating recurring costs. If this use case cannot obtain an appropriate approved
template, resolve that with Kapso before building further features.

Fix the trigger timezone before testing automatic scheduling. Use test-only
birthdays matching the scheduled test date. Verify one controlled manual send and
then an automatic scheduled send after more than 24 hours of user inactivity.
Observe receipt on the phone. The manual scheduler command bypasses the reminder
toggle and must only be used with the intended production test configuration.

Done when an approved template reaches the test phone outside the service window
and an automatic run fires at the configured local hour.

Kapso's [sandbox cannot send templates](https://kapso.com/whatsapp-api-sandbox).
Outside the [24-hour service window](https://kapso.com/guides/whatsapp-pricing/how-pricing-works/the-24-hour-window),
proactive sends require an approved template. Meta controls
[template categories](https://kapso.com/guides/whatsapp-pricing/how-pricing-works/message-categories).

### 3. Make retries and restarts predictable

Keep this work in the existing application and database. The proposed changes are:

- Persist inbound message identity, command outcome, and reply status. Deduplicate
  by message ID scoped to the receiving number, including batch fallback/replay.
  Commit a command's mutation and its processed record together. A recovered reply
  must not rerun the command. Limit recovered free-form replies to the valid window.
- Persist reminder state and atomically claim each user/date before sending.
  Retain provider message IDs and distinguish accepted, delivered, failed, and
  uncertain outcomes. A database unique key added after sending cannot prevent
  concurrent external sends.
- Retry known transient failures with bounds. Reconcile ambiguous timeouts before
  resending; do not promise exactly-once delivery across the provider boundary.
- Subscribe to delivery/failure events and ensure status events never execute bot
  commands. Recover missed same-day work on startup and avoid stale next-day sends.

No separate queue service is proposed. A persistence/recovery design should be
reviewed before implementation; this review adds no queue system.

Done when replay after restart causes no second mutation, committed replies remain
recoverable, overlapping reminder attempts produce one claimed send, and a later
delivery failure is visible. Add focused tests for these failure cases.

Kapso documents [duplicate webhook handling](https://docs.kapso.ai/docs/platform/webhooks/security),
[limited retries and batch fallback](https://docs.kapso.ai/docs/platform/webhooks/advanced),
and [delivery/failure events](https://docs.kapso.ai/docs/platform/webhooks/message-events).

### 4. Finish the minimum pilot experience

Proposed additions, subject to founder decisions:

- Explain the reminder schedule and record the user's agreement to receive it.
  Add a clear stop/resume path and a confirmed delete-all-data path.
- Show contact IDs in `lista`, require disambiguation for existing duplicate
  names, and match names literally when deleting. To correct a saved date,
  users can delete and re-add the contact.
- Use one explicitly disclosed timezone and reminder hour for the first pilot.
  Select the timezone with the founder; neither the Argentine default nor the
  founder's device timezone establishes the audience's timezone.
- Decide and explain February 29 behavior in non-leap years. Keep optional birth
  years; do not collect birthday contacts' phone numbers for this reminder flow.
- Bound names and message sizes; split long lists and handle reminder overflow
  deliberately so a large list does not invalidate a send.

Before broader release, support BSUID-only users: retain a stable internal user ID,
store supported WhatsApp identifiers, reconcile phone/BSUID mappings without
merging unrelated accounts, handle identity changes, and route outbound messages
using Kapso's supported recipient field. Include migration and isolation tests.
A restricted phone-based pilot must explicitly acknowledge its identity limitation.

Kapso's [identity migration guide](https://docs.kapso.ai/docs/whatsapp/business-scoped-user-ids)
documents phone-less events and BSUID sends. This changes the technical assumption
that every WhatsApp user supplies a phone number; the no-password experience stays.

### 5. Deploy one maintainable instance

For the initial pilot, prefer one always-on Python instance, one Uvicorn worker,
and persistent SQLite storage with backups. Reuse APScheduler with an explicit
trigger timezone and same-day recovery. Confirm the host supports this operating
model; an ephemeral filesystem or sleeping instance is unsuitable for it.

Add reproducible startup instructions, versioned schema migrations, a database
restore check, safe error logs, and visibility into the last scheduler run and failed
sends. Review the old pinned dependencies before public exposure. Choose a host
and spending ceiling before provisioning anything. Consider a managed database and
an external scheduler only if the chosen host or later scale requires them.

Done when a deploy/restart preserves birthdays and pending state, the next reminder
runs correctly, and the founder can detect a missed job and restore a backup.

### 6. Run a small invited pilot

Use synthetic birthdays to exercise the full flow without waiting for real birthdays.
Pilot acceptance should include separate users, several birthdays on one day,
no birthday that day, opt-out, deletion, restart, replay, provider failure, and a
scheduled send outside the 24-hour window. Check that users understand how to add
and correct birthdays, then use their feedback to choose the next improvement.

These are proposed acceptance criteria. Pilot size and duration are
UNKNOWN — ask founder. Production readiness must be supported by observed results.

## Scope and cost

Keep the pilot focused on reminders to the user. Defer web accounts, OTP login,
contact imports, automatic greetings, AI parsing, payments, and a dashboard.
If command syntax causes difficulty in the pilot, assess guided WhatsApp input then.

Kapso currently lists a Free plan with 2,000 sent/received messages per month and one
connected number; applicable Meta fees are separate. Validate the account's current
allowances and template category before relying on this for the pilot. Count command
messages and replies as well as reminders. See [Kapso pricing](https://kapso.com/pricing).
This is an infrastructure consideration, not a proposal for product pricing.

## Founder decisions still needed

Pilot participants/market, timezone/hour, February 29 behavior, host and monthly
budget ceiling, retention/deletion policy, and pilot acceptance:
UNKNOWN — ask founder. They need not delay the sandbox test. Q4 launch remains the
recorded goal; this review does not invent a launch date.

Immediate next action: configure Kapso privately and complete step 1, while starting
the template feasibility check in step 2.
