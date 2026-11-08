from backend import check_setup, config


def test_preflight_does_not_print_secrets(monkeypatch, capsys):
    for name in ("KAPSO_API_KEY", "KAPSO_PHONE_NUMBER_ID", "KAPSO_WEBHOOK_SECRET"):
        monkeypatch.setattr(config, name, "private-value-do-not-print")
    monkeypatch.setattr(config, "ENABLE_REMINDERS", False)
    assert check_setup.main() == 0
    output = capsys.readouterr().out
    assert "private-value-do-not-print" not in output
    assert "live delivery are still unverified" in output


def test_preflight_catches_missing_or_placeholder_settings(monkeypatch, capsys):
    monkeypatch.setattr(config, "KAPSO_API_KEY", "your-kapso-project-api-key")
    monkeypatch.setattr(config, "KAPSO_PHONE_NUMBER_ID", "")
    monkeypatch.setattr(config, "KAPSO_WEBHOOK_SECRET", "secret")
    monkeypatch.setattr(config, "ENABLE_REMINDERS", True)
    assert check_setup.main() == 1
    output = capsys.readouterr().out
    assert "KAPSO_API_KEY: MISSING OR INVALID" in output
    assert "KAPSO_PHONE_NUMBER_ID: MISSING OR INVALID" in output
    assert "SANDBOX_REMINDERS_DISABLED: MISSING OR INVALID" in output
