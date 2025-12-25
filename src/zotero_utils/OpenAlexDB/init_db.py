import os
import sqlite3

# Schema from here: https://docs.openalex.org/download-all-data/upload-to-your-database/load-to-a-relational-database
# Other API docs:
# https://docs.openalex.org/api-entities/entities-overview
# https://docs.openalex.org/how-to-use-the-api/get-single-entities
def init_openalex_db(file_path: str) -> sqlite3.Connection:
    """Initialize the OpenAlex SQLite database"""
    if os.path.exists(file_path):
        os.remove(file_path)
    
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()

    # Execute the SQL commands in init_db.sql
    with open("src/zotero_utils/OpenAlexDB/init_db.sql", "r") as f:
        sql_commands = f.read()

    cursor.executescript(sql_commands)
    return conn