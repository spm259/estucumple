from backend import bot, crud


def test_parse_add_ddmm():
    a = bot.parse_command("add Maria 25/05")
    assert a.kind == "add"
    assert a.name == "Maria"
    assert (a.day, a.month, a.year) == (25, 5, None)


def test_parse_add_with_year_and_multiword_name():
    a = bot.parse_command("add Maria Jose 25/05/1990")
    assert a.kind == "add"
    assert a.name == "Maria Jose"
    assert (a.day, a.month, a.year) == (25, 5, 1990)


def test_parse_add_iso():
    a = bot.parse_command("add Bob 1990-12-31")
    assert (a.day, a.month, a.year) == (31, 12, 1990)


def test_parse_add_invalid_date():
    a = bot.parse_command("add Maria 99/99")
    assert a.kind == "error"


def test_parse_add_missing_date():
    assert bot.parse_command("add Maria").kind == "error"


def test_parse_list_and_help_aliases():
    assert bot.parse_command("list").kind == "list"
    assert bot.parse_command("lista").kind == "list"
    assert bot.parse_command("hola").kind == "help"
    assert bot.parse_command("").kind == "help"


def test_parse_delete_by_name_and_id():
    by_name = bot.parse_command("delete Maria")
    assert by_name.kind == "delete" and by_name.name == "Maria"
    by_id = bot.parse_command("delete 7")
    assert by_id.kind == "delete" and by_id.contact_id == 7


def test_parse_unknown():
    assert bot.parse_command("xyzzy").kind == "error"


def test_handle_message_full_flow(db):
    phone = "5491122334455"

    reply = bot.handle_message(db, phone, "add Maria 25/05")
    assert "Maria" in reply and "25/05" in reply

    listing = bot.handle_message(db, phone, "list")
    assert "Maria" in listing

    deleted = bot.handle_message(db, phone, "delete Maria")
    assert "Maria" in deleted

    empty = bot.handle_message(db, phone, "list")
    assert "Todavía no" in empty


def test_handle_message_is_per_user(db):
    bot.handle_message(db, "111", "add Ana 01/01")
    other = bot.handle_message(db, "222", "list")
    assert "Ana" not in other  # users don't see each other's contacts
