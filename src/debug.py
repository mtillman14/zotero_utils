# src/debug_commands.py
import sys
from pathlib import Path

# Add the src directory to Python path to make the package imports work
src_dir = str(Path(__file__).parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from zotero_utils.commands import *
from zotero_utils.OpenAlexDB.init_db import init_openalex_db

from pyalex import Works
from zotero_utils.OpenAlexDB.work import Work

def main():
    # You can set breakpoints in this function
    # zotero_db_path = None  # Set this to your Zotero database path if needed
    # show_dag()

    file_path = 'openalex.db'
    conn = init_openalex_db(file_path)
    example_json_path = 'src/zotero_utils/OpenAlexDB/example_work.json'
    with open(example_json_path, 'r') as f:
        work = json.load(f)
    work = Works().get([work["id"],"https://openalex.org/W2214831219"])
    zwork = Work(work)
    zwork.insert_or_replace_in_db(conn)


if __name__ == "__main__":
    main()