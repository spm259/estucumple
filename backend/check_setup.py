"""Local sandbox preflight. Does not call Kapso or reveal configuration values."""
from . import config


def sandbox_checks() -> dict[str, bool]:
    checks = {}
    for name in ("KAPSO_API_KEY", "KAPSO_PHONE_NUMBER_ID", "KAPSO_WEBHOOK_SECRET"):
        value = getattr(config, name).strip()
        checks[name] = bool(value) and not value.startswith("your-")
    checks["HTTPS_API_BASE"] = config.KAPSO_API_BASE.startswith("https://")
    checks["SANDBOX_REMINDERS_DISABLED"] = not config.ENABLE_REMINDERS
    return checks


def main() -> int:
    checks = sandbox_checks()
    for name, ready in checks.items():
        print(f'{name}: {"OK" if ready else "MISSING OR INVALID"}')
    if all(checks.values()):
        print("Local configuration is ready. Sandbox activation and live delivery are still unverified.")
        return 0
    print("Update .env using .env.example. Do not paste credentials into chat.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
