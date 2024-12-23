import sqlite3
import os
from enum import Enum
import csv
import uuid

import requests
import typer
from base_dag import DAG

from .Classes.item import get_items, get_openalex_work_id
from .Counts.counts import count_items_by_author, count_num_distinct_authors, count_authors_per_item
from .Items.get_all_items import get_all_item_ids
from .Visualizations.pie_chart import pie_chart
from .Visualizations.stacked_bar_chart import stacked_bar_chart
from .Visualizations.stem_plot import stem_plot
from .constants import ZOTERO_DB_FILE_HELP, TYPE_HELP, NUM_GROUPS_HELP, ZOTERO_ENDPOINTS_DICT

app = typer.Typer()

# def get_connection(zotero_db_file: str):
#     """Establish a connection to the SQLite database."""
#     if not zotero_db_file or isinstance(zotero_db_file, typer.models.OptionInfo):
#         zotero_db_file = os.path.join(os.path.expanduser('~'), 'Zotero', 'zotero.sqlite') # cross-platform
#     if not os.path.exists(zotero_db_file):
#         raise FileNotFoundError(f"Database file not found: {zotero_db_file}")
#     try:        
#         return sqlite3.connect(zotero_db_file)
#     except sqlite3.OperationalError:
#         raise Exception("Zotero must be closed to connect to the database.")

class MetaType(str, Enum):
    """The meta class for the different types of options."""

class VisType(MetaType):
    """Enum to define the --vis-type options."""
    bar = "bar"
    pie = "pie"

class ItemsSourceOptions(MetaType):
    """Enum to define the `show-dag` options."""
    user = "user"
    group = "group"


    
def resolve_type(type: MetaType):
    """Resolve the type to a string. typer.models.OptionInfo is its type when not run from the command line."""
    if isinstance(type, typer.models.OptionInfo):
        return type.default
    return type.value

@app.command()
def show_creators_per_item(zotero_db_file: str = typer.Option(default=None, help=ZOTERO_DB_FILE_HELP),
                           num_groups: int = typer.Option(20, help=NUM_GROUPS_HELP),
                           type: VisType = typer.Option(VisType.bar, help=TYPE_HELP)):
    """
    Show a chart of the number of creators per research item in the Zotero database.
    
    Args:
        zotero_db_file: Path to the Zotero SQLite database file.
    """
    conn = get_connection(zotero_db_file)
    try:        
        type = resolve_type(type)
        item_ids = get_all_item_ids(conn)
        counts = count_authors_per_item(item_ids, conn)
        title_str = "Number of Authors Per Item"
        if type=="bar":
            stacked_bar_chart(counts, num_groups=num_groups, sort_by='labels', title_str=title_str)
        elif type=="pie":
            pie_chart(counts, num_groups=20, title_str=title_str, sort_by="labels")        
    finally:
        conn.close()

@app.command()
def show_items_per_creator(zotero_db_file: str = typer.Option(default=None, help=ZOTERO_DB_FILE_HELP), 
                           num_groups: int = typer.Option(20, help=NUM_GROUPS_HELP),
                           type: VisType = typer.Option(VisType.bar, help=TYPE_HELP)):
    """
    Show a chart of the number of items from the top N creators in the Zotero database.
    
    Args:
        zotero_db_file: Path to the Zotero SQLite database file.
        num_groups: Number of groups to display in the chart (default is 20).
    """
    conn = get_connection(zotero_db_file)
    try:        
        type = resolve_type(type)
        item_ids = get_all_item_ids(conn)
        counts = count_items_by_author(item_ids, conn)
        title_str = "Item Count Per Author"
        if type=="bar":
            stacked_bar_chart(counts, num_groups=num_groups, sort_by='values', title_str=title_str)
        elif type=="pie":
            pie_chart(counts, num_groups=num_groups, title_str=title_str, sort_by="values")        
    finally:
        conn.close()

@app.command()
def count_distinct_authors(zotero_db_file: str = typer.Option(default=None, help=ZOTERO_DB_FILE_HELP)):
    """
    Count the number of distinct authors in the Zotero database.
    
    Args:
        zotero_db_file: Path to the Zotero SQLite database file.
    """
    conn = get_connection(zotero_db_file)
    try:        
        item_ids = get_all_item_ids(conn)
        authors_count = count_num_distinct_authors(item_ids, conn)
        print(f"Number of authors: {authors_count}")
    finally:
        conn.close()


@app.command()
def show_timeline_date_published(zotero_db_file: str = typer.Option(default=None, help=ZOTERO_DB_FILE_HELP), 
                                 show_details: bool = typer.Option(default=True, help="Show the individual publications for each year. Hovering over each point reveals information about each individual publication.")):
    """
    Show the timeline of when the articles in the Zotero database were published.

    Args:
        zotero_db_file (str, optional): Path to the Zotero SQLite database file.
    """
    conn = get_connection(zotero_db_file)
    try:        
        item_ids = get_all_item_ids(conn)
        items_list = []
        for item_id in item_ids:
            item = get_item(item_id, conn)
            if item and item.date_published is not None:
                items_list.append(item)
        stem_plot([item.to_dict() for item in items_list], show_details=show_details)
    finally:
        conn.close()

@app.command()
def show_dag(md_dir: str = typer.Option(default=os.path.join(os.path.expanduser("~"), 'zotero-utils', f'md-files-{uuid.uuid4()}'), help="Directory to save the markdown files of the DAG to."),
             source: ItemsSourceOptions = typer.Option('user', help="Source of the items (user or group)")
             ):
    """
    Show a directed acyclic graph of the relationships between items in the Zotero database.

    Args:
        md_dir (str, optional): Path to save the DAG.
    """
    md_dir = resolve_type(md_dir)
    source = resolve_type(source)
    items = get_items(source=source)

    # 2. Get each Item's OpenAlex Work ID, store in a dict as key: work_id.
    work_ids = {}
    for item in items:
        item_data = item.get('data', {})
        work_id = get_openalex_work_id(item_data)
        work_ids[work_id] = item

    # 3. Ping the OpenAlex API (or cache) to get the references for each item. Parse them for citation information, stored as a dict, where keys and values are both OpenAlex Work ID's.
    # NOTE: Cache results in a .csv file to avoid pinging the API every time.
    cache_file = 'work_id_citations.csv'
    work_ids_dict = {}
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            csv_reader = csv.reader(f)
            next(csv_reader) # Skip the header row
            for row in csv_reader:
                if row[0] not in work_ids_dict:
                    work_ids_dict[row[0]] = []
                work_ids_dict[row[0]].append(row[1])            

    base_url = 'https://api.openalex.org/works/'    
    for count, openalex_work_id in enumerate(work_ids.keys()):
        if openalex_work_id in work_ids_dict or openalex_work_id is None:
            continue
        url = f'{base_url}{openalex_work_id}'
        try:
            # Query the OpenAlex API.
            response = requests.get(url)
            response.raise_for_status() # Raise an exception for HTTP errors.
            print(f"Fetched {count+1} of {len(work_ids.keys())}")

            # Parse the JSON response
            data = response.json()
            referenced_works = data.get('referenced_works', [])

            # Parse the list of URL's for their OpenAlex Work ID's (get the last part of the URL, after the last slash).
            work_ids_list = [work.split('/')[-1] for work in referenced_works]

            # Put the work_ids in the dict.
            work_ids_dict[openalex_work_id] = work_ids_list
        except requests.RequestException as e:
            print(f"Error fetching cited works for {openalex_work_id}: {e}")
            continue

    # 4. Create the DAG from the dict using my base-dag library.
    dag = DAG()
    for key, value in work_ids_dict.items():
        for val in value:
            try:
                dag.add_edge(key, val)    
            except:
                continue

    # 5. Save the DAG to the cache file.
    with open(cache_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Source", "Target"]) # Write header row
        writer.writerows(dag.edges)

    # 6. Write the DAG to the directory of markdown files.
    callables_dict = {}
    callables_dict['title'] = lambda x: work_ids[x].get('data', {}).get('title')
    callables_dict['id'] = lambda x: work_ids[x].get('key')
    dag.to_md_files(md_dir, callables_dict)
    

def main():
    """Entry point for the CLI when run as 'zotero-utils ...'"""
    app()