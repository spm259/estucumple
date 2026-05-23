"""Parses inbound WhatsApp commands and produces Spanish replies.

Strict command grammar (no NLP):
    add <nombre> <DD/MM[/AAAA]>   |  add <nombre> <AAAA-MM-DD>
    list
    delete <nombre>  |  delete <id>
    help
"""
import re
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from . import crud, schemas

HELP_TEXT = (
    "🎂 *Recordatorio de Cumpleaños*\n\n"
    "Comandos disponibles:\n"
    "• *add* <nombre> <DD/MM> — agregar un cumpleaños\n"
    "   ej: add Maria 25/05  (o  add Maria 25/05/1990)\n"
    "• *list* — ver tus cumpleaños guardados\n"
    "• *delete* <nombre> — eliminar un cumpleaños\n"
    "• *help* — mostrar esta ayuda"
)

_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")


@dataclass
class Action:
    kind: str  # "add" | "list" | "delete" | "help" | "error"
    name: Optional[str] = None
    month: Optional[int] = None
    day: Optional[int] = None
    year: Optional[int] = None
    contact_id: Optional[int] = None
    message: Optional[str] = None  # error detail / usage hint


def _parse_date(token: str) -> Optional[tuple]:
    """Return (day, month, year|None) or None if the token isn't a valid date."""
    iso = _ISO.match(token)
    if iso:
        year, month, day = (int(x) for x in iso.groups())
    else:
        parts = re.split(r"[/\-.]", token)
        if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
            return None
        day, month = int(parts[0]), int(parts[1])
        year = int(parts[2]) if len(parts) == 3 else None
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return day, month, year


def parse_command(text: str) -> Action:
    text = (text or "").strip()
    if not text:
        return Action(kind="help")

    tokens = text.split()
    cmd = tokens[0].lower()

    if cmd in ("help", "ayuda", "start", "hi", "hola"):
        return Action(kind="help")

    if cmd in ("list", "lista", "ls"):
        return Action(kind="list")

    if cmd in ("add", "agregar", "nuevo"):
        if len(tokens) < 3:
            return Action(
                kind="error",
                message="Formato: add <nombre> <DD/MM>. Ej: add Maria 25/05",
            )
        date = _parse_date(tokens[-1])
        if date is None:
            return Action(
                kind="error",
                message="Fecha inválida. Usá DD/MM o DD/MM/AAAA. Ej: 25/05",
            )
        name = " ".join(tokens[1:-1]).strip()
        if not name:
            return Action(kind="error", message="Falta el nombre.")
        day, month, year = date
        return Action(kind="add", name=name, day=day, month=month, year=year)

    if cmd in ("delete", "eliminar", "borrar", "del", "rm"):
        if len(tokens) < 2:
            return Action(
                kind="error", message="Formato: delete <nombre>. Ej: delete Maria"
            )
        arg = " ".join(tokens[1:]).strip()
        if arg.isdigit():
            return Action(kind="delete", contact_id=int(arg))
        return Action(kind="delete", name=arg)

    return Action(
        kind="error", message="No entendí ese comando. Escribí *help* para ver las opciones."
    )


def _format_date(c) -> str:
    base = f"{c.birth_day:02d}/{c.birth_month:02d}"
    return f"{base}/{c.birth_year}" if c.birth_year else base


def handle_message(db: Session, from_phone: str, text: str) -> str:
    """Process one inbound message and return the reply text."""
    user = crud.get_or_create_user_by_phone(db, from_phone)
    action = parse_command(text)

    if action.kind == "help":
        return HELP_TEXT

    if action.kind == "error":
        return action.message or HELP_TEXT

    if action.kind == "add":
        contact = crud.create_contact(
            db,
            user.id,
            schemas.ContactCreate(
                name=action.name,
                birth_month=action.month,
                birth_day=action.day,
                birth_year=action.year,
            ),
        )
        return f"✅ Guardado: {contact.name} — {_format_date(contact)}"

    if action.kind == "list":
        contacts = crud.list_contacts(db, user.id)
        if not contacts:
            return "Todavía no tenés cumpleaños guardados. Probá: add Maria 25/05"
        lines = [f"• {c.name} — {_format_date(c)}" for c in contacts]
        return "🎉 Tus cumpleaños:\n" + "\n".join(lines)

    if action.kind == "delete":
        if action.contact_id is not None:
            removed = crud.delete_contact_by_id(db, user.id, action.contact_id)
        else:
            removed = crud.delete_contact_by_name(db, user.id, action.name)
        if removed:
            return f"🗑️ Eliminado: {removed.name}"
        return "No encontré ese contacto."

    return HELP_TEXT
