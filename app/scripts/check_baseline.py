from app.models import User, UserBookBaseline
from app.core.database import engine
from sqlmodel import Session, select
import sys
from typing import Optional

sys.path.insert(0, "..")


def find_baseline_for_email(email: str) -> Optional[UserBookBaseline]:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            print(f"No user with email {email}")
            return None
        baseline = session.exec(
            select(UserBookBaseline).where(UserBookBaseline.user_id == user.id)
        ).all()
        return baseline


def main():
    email = "test@example.com"
    baselines = find_baseline_for_email(email)
    if not baselines:
        print("No baseline rows found for", email)
        return
    for b in baselines:
        print("Baseline:", b.model_dump())


if __name__ == "__main__":
    main()
