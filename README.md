# Es tu Cumple — Recordatorios de cumpleaños por WhatsApp

A simple, multi-user birthday reminder that works through WhatsApp. Users chat
with a WhatsApp bot to add/list/delete birthdays. An optional daily job sends a
reminder when someone's birthday arrives; it is disabled by default for sandbox testing. WhatsApp messaging is handled by
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
Phone-less BSUID events are currently ignored; they are not used as phone destinations.
The bot reminds the user. It does not send birthday greetings to their contacts.

Company and product context starts in [company-context/CLAUDE.md](company-context/CLAUDE.md).

## Bot commands

```
agregar <nombre> <DD/MM>          agregar María 25/05
agregar <nombre> <DD/MM/AAAA>     agregar María 25/05/1990
lista                            show saved birthdays
borrar <nombre>                  borrar María   (or: borrar <id>)
ayuda                            usage
```

English commands (`add`, `list`, `delete`, `help`) still work. Replies use Mexican Spanish.

## First session: sandbox conversation

1. **Use Python 3.12 and install dependencies** from the repo root:
   ```bash
   python3.12 -m venv venv
   venv/bin/python -m pip install -r requirements-dev.txt
   venv/bin/python -m pytest backend/tests -q
   ```
   A local `venv/` is already prepared in this checkout. The old nested
   `estucumple/venv/` uses Python 3.9; use the root environment above.

2. **Activate your phone** in the Kapso dashboard: WhatsApp → Sandbox → Add
   session. Send its activation code from your phone. Sandbox text conversations
   work without connecting a production number. Templates require production.
   See [Kapso sandbox](https://kapso.com/whatsapp-api-sandbox).

3. **Configure locally.** If `.env` does not exist, copy `.env.example` to `.env`.
   If it exists, keep its settings and add the missing fields from `.env.example`.
   Set `KAPSO_API_KEY`, the sandbox configuration's `KAPSO_PHONE_NUMBER_ID`, and
   `KAPSO_WEBHOOK_SECRET`. Use the same secret in Kapso's webhook settings.
   Keep `ENABLE_REMINDERS=false`. Do not share credentials in chat or commit them.
   ```bash
   venv/bin/python -m backend.check_setup
   ```
   This checks local configuration without printing values or contacting Kapso.
   A successful check does not prove sandbox activation or delivery.

4. **Start the API:**
   ```bash
   venv/bin/python -m uvicorn backend.main:app --reload
   ```
   In another terminal, use an installed HTTPS tunnel, for example:
   ```bash
   ngrok http 8000
   ```

5. **Register the WhatsApp webhook** on the sandbox configuration. Set its URL
   to `https://<tunnel-host>/webhooks/whatsapp`, its secret to your local
   `KAPSO_WEBHOOK_SECRET`, and subscribe to `whatsapp.message.received`.
   Use Kapso v2 format; leave buffering off for the initial test. Buffered v2,
   forwarded Meta, and legacy flat text shapes are also parsed.
   See [Kapso webhooks](https://docs.kapso.ai/docs/platform/webhooks/overview).

6. **Send from your activated phone:**
   ```text
   hola
   agregar María 25/05
   lista
   borrar María
   lista
   ```
   Expect help, a saved confirmation, the saved birthday, a deletion confirmation,
   and an empty-list hint. This completes the first session's live conversation
   check. It does not verify scheduled reminders.

Missing webhook secret returns `503`. Missing or invalid signatures return `403`.
Replies run after HTTP acknowledgment to avoid waiting on Kapso's outbound API.
These background sends and inbound deduplication are in memory. Restarts can
lose replies or permit duplicate commands; durable recovery remains launch work.

## Production reminder setup

1. **Connect a production number** and replace the sandbox phone-number ID.

2. **Create the reminder template** in the Kapso/Meta dashboard. Proactive
   messages sent outside the 24-hour customer-service window require an
   **approved template**. Create one named `birthday_reminder` (language `es`)
   with a single body parameter, e.g.:
   > 🎂 ¡Hoy es el cumpleaños de {{1}}! No te olvides de saludar.

3. **Enable reminders** with `ENABLE_REMINDERS=true` only after template approval.
   Set `REMINDER_TEMPLATE_NAME` and `REMINDER_TEMPLATE_LANG` to the approved
   template, then confirm `APP_TIMEZONE` and `REMINDER_HOUR`. Run the API:
   ```bash
   venv/bin/python -m uvicorn backend.main:app
   ```

4. **Expose the webhook** with a public HTTPS URL and
   register `https://<your-host>/webhooks/whatsapp` in the Kapso dashboard,
   using the same secret as `KAPSO_WEBHOOK_SECRET`. Subscribe to the
   `whatsapp.message.received` event.

## Testing

Unit tests (no network/credentials needed):
```bash
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python -m pytest backend/tests -q
```

End-to-end:
- Complete the sandbox conversation checklist above.
- With a production number and approved template, add a contact whose birthday
  is **today**, then fire the reminder job once:
  ```bash
  venv/bin/python -m backend.scheduler
  ```
  This manual command sends regardless of `ENABLE_REMINDERS`; never run it
  against the sandbox. Re-running it the same day sends nothing in the normal
  sequential flow (deduped via `reminder_log`). Confirm delivery on your phone.

## Notes / roadmap

- The parser is tested against documented Kapso v2, batched v2, forwarded Meta,
  and legacy text shapes. A real Kapso conversation still needs verification.
- The `frontend/` "coming soon" page is not wired up yet. Web access and
  WhatsApp-OTP login are earlier ideas, not approved V1 commitments.
- Reminders currently use a single `APP_TIMEZONE`; a per-user `timezone` column
  already exists for a future upgrade.
