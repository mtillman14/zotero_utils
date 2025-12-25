import sqlite3

class Creator:

    def __init__(self,
                 first_name: str,
                 last_name: str,
                 orcid_id: str = None,
                 institutions: list = [],
                 creator_id: int = None):
        self.first_name = first_name
        self.last_name = last_name
        self.orcid_id = orcid_id
        self.institutions = institutions
        self.creator_id = creator_id

def get_creator(creator_id: int, conn: sqlite3.Connection) -> Creator:
    """Return a Creator object given a creator ID."""

    sqlite_str = """SELECT firstName, lastName FROM creators WHERE creatorID = ?"""
    cursor = conn.cursor()
    sql_result = cursor.execute(sqlite_str, (creator_id,)).fetchone()    
    first_name = sql_result[0]
    last_name = sql_result[1]
    return Creator(first_name, last_name, creator_id=creator_id)