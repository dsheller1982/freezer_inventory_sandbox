import os
import time
from contextlib import contextmanager
from decimal import Decimal
import streamlit as st
import pymysql
from pymysql.cursors import DictCursor


class DatabaseError(RuntimeError):
    pass


def _env(primary: str, railway: str, default=None):
    return os.getenv(primary) or os.getenv(railway) or default



def connection_config():
    config = {
        "host": _env("DB_HOST", "MYSQLHOST", "127.0.0.1"),
        "port": int(_env("DB_PORT", "MYSQLPORT", "3306")),
        "user": _env("DB_USER", "MYSQLUSER", "freezer_demo"),
        "password": _env("DB_PASSWORD", "MYSQLPASSWORD", "freezer_demo_local"),
        "database": _env("DB_NAME", "MYSQLDATABASE", "freezer_demo"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
        "connect_timeout": 10,
        "read_timeout": 15,
        "write_timeout": 15,
    }

    # Streamlit Cloud reads connection settings from secrets.
    # Railway and local Docker continue using environment variables.
    try:
    streamlit_host = st.secrets.get("DB_HOST")
    except FileNotFoundError:
    streamlit_host = None

    if streamlit_host:
        config.update({
            "host": st.secrets["DB_HOST"],
            "port": int(st.secrets["DB_PORT"]),
            "user": st.secrets["DB_USER"],
            "password": st.secrets["DB_PASSWORD"],
            "database": st.secrets["DB_NAME"],
        })

        import ssl

          ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(
            cadata=st.secrets["DB_SSL_CA"]
        )
        config["ssl"] = ssl_context
    return config


def get_connection(retries: int = 3):
    last_error = None
    for attempt in range(retries):
        try:
            return pymysql.connect(**connection_config())
        except pymysql.MySQLError as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise DatabaseError(f"Could not connect after {retries} attempts: {last_error}")


@contextmanager
def transaction():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except DatabaseError:
        connection.rollback()
        raise
    except pymysql.MySQLError as exc:
        connection.rollback()
        raise DatabaseError(f"Database operation failed: {exc}") from exc
    finally:
        connection.close()


def fetch_inventory():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, item_name, quantity, location, category, exp_date
                   FROM freezer_inventory
                   ORDER BY item_name, location"""
            )
            return cursor.fetchall()
    except pymysql.MySQLError as exc:
        raise DatabaseError(str(exc)) from exc
    finally:
        connection.close()


def fetch_transactions(limit: int = 200):
    safe_limit = max(1, min(int(limit), 500))
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT created_at, action, item_name, quantity_change,
                           quantity_before, quantity_after, location
                    FROM inventory_transactions
                    ORDER BY id DESC LIMIT {safe_limit}"""
            )
            return cursor.fetchall()
    except pymysql.MySQLError as exc:
        raise DatabaseError(str(exc)) from exc
    finally:
        connection.close()


def _require_text(value, label: str, max_length: int) -> str:
    cleaned = " ".join((value or "").split())
    if not cleaned:
        raise DatabaseError(f"{label} is required.")
    if len(cleaned) > max_length:
        raise DatabaseError(f"{label} must be {max_length} characters or fewer.")
    return cleaned


def _positive_quantity(value) -> Decimal:
    try:
        quantity = Decimal(str(value))
    except Exception as exc:
        raise DatabaseError("Quantity must be a number.") from exc
    if quantity <= 0 or quantity > 999:
        raise DatabaseError("Quantity must be between 1 and 999.")
    return quantity


def _log(cursor, *, item_id, item_name, action, change, before, after, location, category):
    cursor.execute(
        """INSERT INTO inventory_transactions
           (item_id, item_name, action, quantity_change, quantity_before,
            quantity_after, location, category)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (item_id, item_name, action, change, before, after, location, category),
    )


def remove_item(item_id: int, amount):
    quantity = _positive_quantity(amount)
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, item_name, quantity, location, category
                   FROM freezer_inventory WHERE id = %s FOR UPDATE""",
                (item_id,),
            )
            item = cursor.fetchone()
            if not item:
                raise DatabaseError("That item no longer exists. Refresh and try again.")
            before = Decimal(item["quantity"])
            if quantity > before:
                raise DatabaseError(f"Only {before:g} are currently available.")
            after = before - quantity
            deleted = after == 0
            if deleted:
                cursor.execute("DELETE FROM freezer_inventory WHERE id = %s", (item_id,))
            else:
                cursor.execute(
                    "UPDATE freezer_inventory SET quantity = %s WHERE id = %s", (after, item_id)
                )
            _log(
                cursor,
                item_id=item_id,
                item_name=item["item_name"],
                action="remove_and_delete" if deleted else "remove",
                change=-quantity,
                before=before,
                after=after,
                location=item["location"],
                category=item["category"],
            )
    return {**item, "change": quantity, "before": before, "after": after, "deleted": deleted}


def restock_item(item_id: int, amount):
    quantity = _positive_quantity(amount)
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, item_name, quantity, location, category
                   FROM freezer_inventory WHERE id = %s FOR UPDATE""",
                (item_id,),
            )
            item = cursor.fetchone()
            if not item:
                raise DatabaseError("That item no longer exists. Refresh and try again.")
            before = Decimal(item["quantity"])
            after = before + quantity
            if after > 9999:
                raise DatabaseError("The resulting quantity would exceed the demo limit.")
            cursor.execute("UPDATE freezer_inventory SET quantity = %s WHERE id = %s", (after, item_id))
            _log(
                cursor,
                item_id=item_id,
                item_name=item["item_name"],
                action="restock",
                change=quantity,
                before=before,
                after=after,
                location=item["location"],
                category=item["category"],
            )
    return {**item, "change": quantity, "before": before, "after": after}


def add_new_item(name, quantity, location, category, expiration):
    name = _require_text(name, "Item name", 100)
    location = _require_text(location, "Location", 50)
    category = _require_text(category, "Category", 50)
    quantity = _positive_quantity(quantity)
    with transaction() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM freezer_inventory")
            if cursor.fetchone()["count"] >= 500:
                raise DatabaseError("The demo inventory has reached its 500-item safety limit. Reset it to continue.")
            cursor.execute(
                """INSERT INTO freezer_inventory
                   (item_name, quantity, location, category, exp_date)
                   VALUES (%s, %s, %s, %s, %s)""",
                (name, quantity, location, category, expiration),
            )
            item_id = cursor.lastrowid
            _log(
                cursor,
                item_id=item_id,
                item_name=name,
                action="add_new",
                change=quantity,
                before=0,
                after=quantity,
                location=location,
                category=category,
            )
    return {"id": item_id, "item_name": name, "after": quantity, "location": location}


def reset_demo():
    from reset_logic import reset_database

    reset_database()

