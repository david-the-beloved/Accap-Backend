from app.core.config import settings
from app.services.email_service import send_streak_reminder


def main() -> None:
    # Send to configured SMTP user or fallback to smtp_from_email
    target = settings.smtp_user or settings.smtp_from_email or "test@example.com"
    print(f"Sending test email to: {target}")
    send_streak_reminder(target)
    print("send_streak_reminder finished")


if __name__ == "__main__":
    main()
