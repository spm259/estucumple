# estucumple — Recordatorio de Cumpleaños por WhatsApp

A simple, multi-user birthday reminder that works through WhatsApp. Users chat
with a WhatsApp bot to add/list/delete birthdays, and a daily job sends a
reminder when someone's birthday arrives. WhatsApp messaging is handled by
[Kapso](https://kapso.ai) (a REST API that mirrors Meta's WhatsApp Cloud API).

## How it works

```
WhatsApp user --(inbound)--> Kapso --webhook--> POST /webhooks/whatsapp
                                                      |  parse: add / list / delete / help
                                                   per-user storage (phone = identity)
                                                      |
                                          reply via WhatsApp (free-form, within 24h)

APScheduler (daily) --> "whose birthday is today?" --> send reminder template
```

A user is identified by their WhatsApp phone number — no signup or password.

## Bot commands

```
add <nombre> <DD/MM>          add Maria 25/05
add <nombre> <DD/MM/AAAA>     add Maria 25/05/1990
list                          show saved birthdays
delete <nombre>               delete Maria   (or: delete <id>)
help                          usage
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt        # add -dev for tests
   ```

2. **Configure environment** — copy `.env.example` to `.env` and fill in your
   Kapso credentials (API key, phone number id, webhook secret).

3. **Create the reminder template** in the Kapso/Meta dashboard. Proactive
   messages sent outside the 24-hour customer-service window require an
   **approved template**. Create one named `birthday_reminder` (language `es`)
   with a single body parameter, e.g.:
   > 🎂 ¡Hoy es el cumpleaños de {{1}}! No te olvides de saludar.

4. **Run the API**
   ```bash
   uvicorn backend.main:app --reload
   ```

5. **Expose the webhook** with a public HTTPS URL (e.g. `ngrok http 8000`) and
   register `https://<your-host>/webhooks/whatsapp` in the Kapso dashboard,
   using the same secret as `KAPSO_WEBHOOK_SECRET`. Subscribe to the
   `whatsapp.message.received` event.

## Testing

Unit tests (no network/credentials needed):
```bash
pip install -r requirements-dev.txt
pytest backend/tests
```

End-to-end:
- Message the bot `add Maria 25/05`, `list`, `delete Maria` and confirm replies.
- Add a contact whose birthday is **today**, then fire the reminder job once:
  ```bash
  python -m backend.scheduler
  ```
  Re-running it the same day sends nothing (deduped via `reminder_log`).

## Notes / roadmap

- The inbound webhook parser (`backend/main.py: extract_messages`) handles both
  Meta-nested and flattened payloads; confirm against a real Kapso event.
- The `frontend/` "coming soon" page is not wired up yet. A future web-app phase
  will reuse `crud.py` / `whatsapp.py` and add WhatsApp-OTP login.
- Reminders currently use a single `APP_TIMEZONE`; a per-user `timezone` column
  already exists for a future upgrade.
