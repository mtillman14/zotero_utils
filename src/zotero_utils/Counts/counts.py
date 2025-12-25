import sqlite3

from ..Classes.creator import get_creator

def count_items_by_author(item_ids: list, conn: sqlite3.Connection) -> dict:
    """Given a list of item ID's, return a dictionary where the keys are authors and the values are the number of items."""
    item_ids_str = "?, " * len(item_ids)
    item_ids_str = item_ids_str[0:-2]
    sqlite_str = f"""SELECT itemID, creatorID FROM itemCreators WHERE itemID IN ({item_ids_str})"""
    cursor = conn.cursor()
    sql_result = cursor.execute(sqlite_str, item_ids).fetchall()

    creator_counts_dict = {} # Keep track of the counts
    creator_cache_dict = {} # Keep a cache of already observed creators.

    # Get count of items for each creatorID
    for result in sql_result:
        creator_id = result[1]
        if creator_id not in creator_cache_dict:
            creator = get_creator(creator_id, conn)            
        else:
            creator = creator_cache_dict[creator_id]

        # Remove everything in the first name after the first space, to remove middle initials.
        last_name = creator.last_name
        if " " not in creator.first_name:
            first_name = creator.first_name
        else:
            space_index = creator.first_name.index(" ")
            first_name = creator.first_name[0:space_index]
        creator_name = last_name + ", " + first_name
        
        if creator_name not in creator_counts_dict:
            creator_counts_dict[creator_name] = 0
            creator_cache_dict[creator_id] = creator
        creator_counts_dict[creator_name] += 1

    sorted_dict = dict(sorted(creator_counts_dict.items(), key=lambda item: item[1], reverse=True))
    return sorted_dict

def count_num_distinct_authors(item_ids: list, conn: sqlite3.Connection) -> int:
    """Count how many different authors there are for the given item ID's."""

    item_ids_str = "?, " * len(item_ids)
    item_ids_str = item_ids_str[0:-2]
    sqlite_str = f"""SELECT itemID, creatorID FROM itemCreators WHERE itemID IN ({item_ids_str})"""
    cursor = conn.cursor()
    sql_result = cursor.execute(sqlite_str, item_ids).fetchall()

    creator_ids = [result[1] for result in sql_result]
    unique_creator_ids = list(set(creator_ids))
    return len(unique_creator_ids)

def count_authors_per_item(item_ids: list, conn: sqlite3.Connection) -> dict:
    """Count how many items have N authors. Returns dict with number of authors as keys, values are number of items."""
    authors_count_dict = {}
    cursor = conn.cursor()
    for item_id in item_ids:
        sqlite_str = "SELECT creatorID FROM itemCreators WHERE itemID = ?"
        sqlite_fetched = cursor.execute(sqlite_str, (item_id,)).fetchall()        
        if not sqlite_fetched:
            continue
        sqlite_result = [v[0] for v in sqlite_fetched]
        num_creators = len(sqlite_result)
        if num_creators not in authors_count_dict:
            authors_count_dict[num_creators] = 0
            # Fill in missing lower values
            # for idx in range(1,num_creators):
            #     if idx not in authors_count_dict:
            #         authors_count_dict[idx] = 0
        authors_count_dict[num_creators] += 1
    return authors_count_dict