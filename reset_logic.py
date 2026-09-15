from pathlib import Path

from database import DatabaseError, transaction


SEED_PATH = Path(__file__).resolve().parent / "sql" / "seed.sql"


def reset_database():
    seed_sql = SEED_PATH.read_text(encoding="utf-8")
    statements = [statement.strip() for statement in seed_sql.split(";") if statement.strip()]
    try:
        with transaction() as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
    except OSError as exc:
        raise DatabaseError(f"Could not read the seed data: {exc}") from exc

