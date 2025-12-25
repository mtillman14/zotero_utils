import sqlite3

def get_all_item_ids(conn: sqlite3.Connection) -> list:
    """Return all itemIDs in the database."""

    sqlite_str = """SELECT itemID FROM items"""
    cursor = conn.cursor()
    sql_result = cursor.execute(sqlite_str).fetchall()
    item_ids = [result[0] for result in sql_result]
    return item_ids