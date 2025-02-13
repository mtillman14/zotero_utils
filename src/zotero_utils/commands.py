import json
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

    # 1. Get all of the items from the Zotero database. Store them to dict where keys are the OpenAlex Work ID's.
    zotero_items = get_items(source=source)
    zotero_items_by_work_id = {}
    for zotero_item in zotero_items:
        zotero_item_data = zotero_item.get('data', {})
        work_id = get_openalex_work_id(zotero_item_data)
        if work_id is not None:
            zotero_items_by_work_id[work_id] = zotero_item

    # 2. Get any OpenAlex items from cache
    openalex_cache_file = 'openalex_items.json'
    openalex_items_by_work_id = {}
    if os.path.exists(openalex_cache_file):
        with open(openalex_cache_file, 'r') as f:
            openalex_items_by_work_id = json.load(f)

    # 3. Get the dict of edges from the cache file.
    edges_cache_file = 'edges_list.csv'
    edges_dict = {}
    if os.path.exists(edges_cache_file):
        with open(edges_cache_file, 'r') as f:
            csv_reader = csv.reader(f)
            next(csv_reader)
            for row in csv_reader:
                if row[0] not in edges_dict:
                    edges_dict[row[0]] = []
                edges_dict[row[0]].append(row[1])
    
    # 3. For each Zotero item, get the referenced work ID's from the cache file. If not present, query the OpenAlex API for referenced work ID's.
    count = 0
    for open_alex_work_id, zotero_item in zotero_items_by_work_id.items():
        count += 1        
        # if count>=20:
        #     break # TESTING ONLY
        zotero_item_data = zotero_item.get('data', {})
        if open_alex_work_id in edges_dict:
            # Get the referenced works from the cache
            referenced_works = edges_dict[open_alex_work_id]
            print(f"Fetched from cache: referenced works for Zotero item ({count} of {len(zotero_items_by_work_id.keys())})")
        else:
            # Query the OpenAlex API for the referenced works
            url = f'https://api.openalex.org/works/{open_alex_work_id}'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            referenced_works_raw = data.get('referenced_works', [])
            referenced_works = [work.split('/')[-1] for work in referenced_works_raw]            
            edges_dict[open_alex_work_id] = referenced_works # Add the referenced works to the edges dict
            print(f"Fetched from OpenAlex API: referenced works for Zotero item ({count} of {len(zotero_items_by_work_id.keys())})")

        # Get the details of each referenced work from either the cache or the OpenAlex API.
        for work_id in referenced_works:
            if work_id in zotero_items_by_work_id:
                continue
            elif work_id in openalex_items_by_work_id:
                # Get the item from the OpenAlex items cache.
                print(f'Fetched from cache: referenced OpenAlex item ({count} of {len(zotero_items_by_work_id.keys())})')
                continue

            # Query the OpenAlex API for the work.
            url = f'https://api.openalex.org/works/{work_id}'
            response = requests.get(url)
            try:
                response.raise_for_status()
            except:
                print(f"Error fetching OpenAlex item {work_id}: {response.status_code}")
                continue
            openalex_items_by_work_id[work_id] = response.json()
            print(f'Fetched from OpenAlex API: referenced OpenAlex item ({count} of {len(zotero_items_by_work_id.keys())})')

        # 4. Save the OpenAlex items to the cache file.
        with open(openalex_cache_file, 'w') as f:
            json.dump(openalex_items_by_work_id, f)

        # 5. Save the edges to the cache file.
        with open(edges_cache_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Target"])
            for source, targets in edges_dict.items():
                for target in targets:
                    writer.writerow([source, target])

    # 6. Create the DAG from the edges dict.
    dag = DAG()
    for key, value in edges_dict.items():
        for val in value:
            try:
                # Sometimes works have the wrong ID, so this fails. Just skip those.
                dag.add_edge(key, val)
            except:
                continue

    # 7. Write the DAG to the directory of markdown files.
    openalex_types_dict = {}
    openalex_types_dict['article'] = 'publication'
    openalex_types_dict['book'] = 'publication'
    zotero_types_dict = {}
    zotero_types_dict['journalArticle'] = 'publication'
    zotero_callables_dict = {}
    zotero_callables_dict['title'] = lambda x: zotero_items_by_work_id[x].get('data', {}).get('title')
    zotero_callables_dict['authors'] = lambda x: get_creators_zotero(zotero_items_by_work_id[x].get('data', {}))
    zotero_callables_dict['year'] = lambda x: zotero_items_by_work_id[x].get('data', {}).get('date')
    zotero_callables_dict['type'] = lambda x: zotero_types_dict.get(zotero_items_by_work_id[x].get('data', {}).get('itemType'), 'publication')
    openalex_callables_dict = {}
    openalex_callables_dict['title'] = lambda x: openalex_items_by_work_id[x].get('title')
    openalex_callables_dict['authors'] = lambda x: get_creators_openalex(openalex_items_by_work_id[x])
    openalex_callables_dict['year'] = lambda x: openalex_items_by_work_id[x].get('publication_year')
    openalex_callables_dict['type'] = lambda x: openalex_types_dict.get(openalex_items_by_work_id[x].get('type'), 'publication')
    callables_dicts = []
    callables_dicts.append(zotero_callables_dict)
    callables_dicts.append(openalex_callables_dict)
    dag.to_md_files(md_dir, callables_dicts)

def get_creators_zotero(item_data: dict) -> str:
    """Get the creators of the item from the Zotero item data."""
    creators = item_data.get('creators', [])
    return ", ".join([f"{creator.get('lastName', '')}, {creator.get('firstName', '')}" for creator in creators])

def get_creators_openalex(item_data: dict) -> str:
    """Get the creators of the item from the OpenAlex item data."""
    authors = item_data.get('authorships', [])
    return ", ".join([f"{author['author']['display_name']}" for author in authors])
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # 2. Get each Item's OpenAlex Work ID, store in a dict as key: work_id.
    # zotero_items_by_work_id = {}
    # for zotero_item in zotero_items:
    #     zotero_item_data = zotero_item.get('data', {})
    #     work_id = get_openalex_work_id(zotero_item_data)
    #     zotero_items_by_work_id[work_id] = zotero_item

    # # 3. Ping the OpenAlex API (or cache) to get the references for each item. Parse them for citation information, stored as a dict, where keys and values are both OpenAlex Work ID's.
    # # NOTE: Cache results in a .csv file to avoid pinging the API every time.
    # cache_file = 'edges_list.csv'
    # cited_work_ids_dict = {}
    # if os.path.exists(cache_file):
    #     with open(cache_file, 'r') as f:
    #         csv_reader = csv.reader(f)
    #         next(csv_reader) # Skip the header row
    #         for row in csv_reader:
    #             if row[0] not in cited_work_ids_dict:
    #                 cited_work_ids_dict[row[0]] = []
    #             cited_work_ids_dict[row[0]].append(row[1])            

    # # Query the OpenAlex API for the works cited by each work ID that is not in the cache (not in Zotero)
    # base_url = 'https://api.openalex.org/works/'
    # openalex_items_by_work_id = {}
    # for count, openalex_work_id in enumerate(zotero_items_by_work_id.keys()):
    #     if openalex_work_id is None:
    #         continue
    #     url = f'{base_url}{openalex_work_id}'
    #     try:
    #         if openalex_work_id in cited_work_ids_dict:
    #             work_ids_list = cited_work_ids_dict[openalex_work_id]
    #         else:
    #             # Query the OpenAlex API.
    #             response = requests.get(url)
    #             response.raise_for_status() # Raise an exception for HTTP errors.
    #             print(f"Fetched {count+1} of {len(zotero_items_by_work_id.keys())}")

    #             # Parse the JSON response
    #             data = response.json()
    #             referenced_works = data.get('referenced_works', [])

    #             # Parse the list of URL's for their OpenAlex Work ID's (get the last part of the URL, after the last slash).
    #             work_ids_list = [work.split('/')[-1] for work in referenced_works]

    #             # Put the work_ids in the dict.
    #             cited_work_ids_dict[openalex_work_id] = work_ids_list

    #         # Add the cited works to the dict.
    #         # 1. Remove the work ID's that are in the cited_work_ids_dict.
    #         work_ids_not_in_zotero = [work_id for work_id in work_ids_list if work_id not in zotero_items_by_work_id.keys()]

    #         # Add the details of the OpenAlex cited works to the dict.
    #         openalex_items_by_work_id.update({work_id: requests.get(f'{base_url}{work_id}').json() for work_id in work_ids_not_in_zotero})
    #     except requests.RequestException as e:
    #         print(f"Error fetching cited works for {openalex_work_id}: {e}")
    #         continue
        
    # # 4. Create the DAG from the `cited_work_ids_dict` (which is just a dict of OpenAlex Work ID's with a list of OpenAlex Work ID's that they cite) using my base-dag library.
    # # Includes work ID's that both are and are not in Zotero.
    # dag = DAG()
    # for key, value in cited_work_ids_dict.items():
    #     for val in value:
    #         try:
    #             dag.add_edge(key, val)    
    #         except:
    #             continue

    # # 5. Save the DAG to the cache file.
    # with open(cache_file, 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["Source", "Target"]) # Write header row
    #     writer.writerows(dag.edges)

    # # 6. Write the DAG to the directory of markdown files.
    # # Now I have one dict of Zotero items by OpenAlex Work ID (source or target nodes) and another dict of OpenAlex items by OpenAlex Work ID (target nodes only).
    # # Need to parse the Zotero and OpenAlex items to get all of the metadata for each type.        
    # zotero_callables_dict = {}
    # zotero_callables_dict['title'] = lambda x: zotero_items_by_work_id[x].get('data', {}).get('title')
    # zotero_callables_dict['authors'] = lambda x: zotero_items_by_work_id[x].get('data', {}).get('creators')
    # zotero_callables_dict['year'] = lambda x: zotero_items_by_work_id[x].get('data', {}).get('date')
    # zotero_callables_dict['type'] = lambda x: zotero_items_by_work_id[x].get('data', {}).get('itemType')
    # openalex_callables_dict = {}
    # openalex_callables_dict['title'] = lambda x: openalex_items_by_work_id[x].get('title')
    # openalex_callables_dict['authors'] = lambda x: openalex_items_by_work_id[x].get('authors')
    # openalex_callables_dict['year'] = lambda x: openalex_items_by_work_id[x].get('year')
    # openalex_callables_dict['type'] = lambda x: openalex_items_by_work_id[x].get('type')
    # callables_dicts = []    
    # callables_dicts.append(zotero_callables_dict)
    # callables_dicts.append(openalex_callables_dict)
    # dag.to_md_files(md_dir, callables_dicts)
    

def main():
    """Entry point for the CLI when run as 'zotero-utils ...'"""
    app()