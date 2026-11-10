# Product

## Intended V1
A command-based WhatsApp birthday reminder bot for individuals.
The user can save, list, and delete birthdays and receive a birthday-day reminder.
The founder's desired outcome is helping people wish others happy birthday on WhatsApp.

## Implemented behavior
- `agregar <nombre> <DD/MM>` saves a birthday; birth year is optional.
- `lista`, `borrar <nombre>` or `borrar <id>`, and `ayuda` manage saved birthdays.
- English aliases still work. Phone number identifies each user; phone-less BSUID events are ignored.
- Signed webhooks parse Kapso v2, buffered v2, forwarded Meta, and legacy text shapes. Replies run after acknowledgment.
- The daily job groups today's birthday names into one reminder per user.
- Scheduling is disabled by default. Production templates are required before enabling it.
- Reminder logs suppress repeat sends for the same user and date in the normal sequential flow.

## Current exclusions
The code does not send birthday greetings to contacts, import an address book, or provide payments.
The frontend is a coming-soon page, not a working web app.
Web access, WhatsApp-OTP login, and per-user scheduling are not implemented; approval for future scope is UNKNOWN — ask founder.

## Core objects
- User: WhatsApp number, optional name, stored timezone.
- Contact: belongs to a user; name, birth month/day, optional birth year. No contact phone number is stored.
- ReminderLog: user and calendar date of a sent reminder.

## Definition of done
Founder-approved launch criteria: UNKNOWN — ask founder.
The README describes live checks for add/list/delete, a birthday-today reminder, and same-day deduplication. These are documented checks, not verified results.

Sources: `README.md`, `backend/bot.py`, `backend/models.py`, `backend/scheduler.py`, `frontend/page.tsx`; founder answers on 2026-10-04.
