# Constraints

## Resources
One founder. Limited personal time and a low budget.
Hours available, budget ceiling, and required infrastructure: UNKNOWN — ask founder.
Codex is the intended build assistant. Keep changes small and maintainable.

## Product and technical limits
V1 is WhatsApp-based. The current implementation uses Kapso, FastAPI, SQLAlchemy, and APScheduler; SQLite is the default.
Kapso is implemented, but a permanent provider requirement is UNKNOWN — ask founder.
The reminder job uses one app-wide timezone; stored user timezones are not used for scheduling.
Date validation checks day/month ranges, not full calendar validity. February 29 behavior is undefined for non-leap years.
Inbound deduplication and deferred replies are in memory and can be lost on restart. Reminder logs do not establish a concurrent-send guarantee.
The frontend has no package manifest or connected signup action.

## Trust and legal
Protect WhatsApp numbers, saved names, birthdays, and credentials. Never copy `.env` values into documentation.
Webhooks reject missing secrets or invalid signatures. Code existence does not prove secure deployment.
Phone-less BSUID events are ignored until supported identity and reply routing are implemented.
The README requires an approved WhatsApp template for proactive reminders. Approval and live provider behavior are unconfirmed.
Consent, retention, deletion policy, legal jurisdiction, and compliance requirements: UNKNOWN — ask founder.

## Hard no's and approvals
Do not invent business facts or broaden the approved V1.
Founder-specific hard no's and approval thresholds for deployment, spending, or external actions: UNKNOWN — ask founder.

Sources: founder answers on 2026-10-04; `README.md`, `backend/config.py`, `backend/main.py`, `backend/bot.py`, `backend/scheduler.py`, `frontend/page.tsx`.
