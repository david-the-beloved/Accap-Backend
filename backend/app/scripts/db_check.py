from sqlmodel import text
from app.core.database import engine
import sys
sys.path.insert(0, '..')


def main():
    with engine.connect() as conn:
        res = conn.exec(text('select now()'))
        print('db now:', res.fetchone())


if __name__ == '__main__':
    main()
