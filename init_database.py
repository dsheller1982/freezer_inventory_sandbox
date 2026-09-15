from pathlib import Path

from database import transaction
from reset_logic import reset_database


def apply_schema():
    path = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    statements = [statement.strip() for statement in path.read_text(encoding="utf-8").split(";") if statement.strip()]
    with transaction() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)


if __name__ == "__main__":
    apply_schema()
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM freezer_inventory")
            needs_seed = cursor.fetchone()["count"] == 0
    if needs_seed:
        reset_database()
        print("Schema initialized and demo data loaded.")
    else:
        print("Schema is current; existing demo data was preserved.")
