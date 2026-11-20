# Constraints

## Resources
One founder. Limited personal time and a low budget.
Hours available, budget ceiling, and required infrastructure: UNKNOWN — ask founder.
Codex is the intended build assistant. Keep changes small and maintainable.

## Product and technical limits
V1 is WhatsApp-based. The current implementation uses Kapso, FastAPI, SQLAlchemy, and APScheduler; SQLite is the default.
Kapso is the provider requested by the founder for the November 12, 2026 revisit.
The reminder job uses one app-wide timezone; stored user timezones are not used for scheduling.
The WhatsApp command parser validates real calendar dates, including optional birth years. Schema fields still only validate ranges. February 29 reminder behavior is undefined for non-leap years.
The reminder CronTrigger lacks an explicit timezone and currently uses the host timezone, which can differ from APP_TIMEZONE.
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

Sources: founder answers on 2026-10-04 and provider request on 2026-11-12; code review and local trigger-timezone check on 2026-11-12; `README.md`, `backend/config.py`, `backend/main.py`, `backend/bot.py`, `backend/schemas.py`, `backend/scheduler.py`, `frontend/page.tsx`.
