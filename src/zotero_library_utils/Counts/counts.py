import sqlite3

from Classes.creator import get_creator

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