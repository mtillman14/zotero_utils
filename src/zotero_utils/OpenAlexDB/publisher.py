import sqlite3
import json
from typing import Union, List

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Publisher:

    def __init__(self, publisher: pyalex.Publisher):
        if not isinstance(publisher, pyalex.Publisher):
            raise TypeError("publisher must be a pyalex.Publisher object")        
        self.publisher = publisher
        self.publisher_id = remove_base_url(publisher['id'])

    @staticmethod
    def create_publishers_from_web_api_by_ids(conn: sqlite3.Connection, publisher_ids: Union[List[str], str]) -> "Publisher":
        """
        Query the OpenAlex web API for a particular publisher(s) to create the pyalex.Publisher dict. Insert the publisher(s) into the database.
        """
        if not isinstance(publisher_ids, list):
            publisher_ids = [publisher_ids]
        pyalexPublishers = pyalex.Publishers().get([publisher_ids])
        publishers = [Publisher(p) for p in pyalexPublishers]
        for publisher in publishers:
            publisher.insert_or_replace_in_db(conn)
        return publishers
    
    @staticmethod
    def read_publishers_from_db_by_ids(conn: sqlite3.Connection, publisher_ids: Union[List[str], str]) -> "Publisher":
        """
        Query the database for a particular publisher to create its pyalex.Publisher dict. 
        """
        if not isinstance(publisher_ids, list):
            publisher_ids = [publisher_ids]
        publisher_dict = {}
        cursor = conn.cursor()
        # PUBLISHERS
        cursor.execute("SELECT * FROM publishers WHERE id=?", (remove_base_url(publisher_id),))
        publisher_id = cursor.fetchone()
        # PUBLISHERS COUNTS BY YEAR

        # PUBLISHERS IDS        
        return Publisher(pyalex.Publisher(publisher_dict))
    
    def delete(self, conn: sqlite3.Connection):
        """
        Delete the publisher from the database.
        """
        publisher_id = self.publisher_id
        conn.execute("DELETE FROM publishers WHERE id=?", (publisher_id,))
        conn.execute("DELETE FROM publishers_counts_by_year WHERE publisher_id=?", (publisher_id,))           
        conn.execute("DELETE FROM publishers_ids WHERE publisher_id=?", (publisher_id,))              

    def insert_or_replace_in_db(self, conn: sqlite3.Connection):
        """
        Insert the publisher into the database.
        """
        publisher = self.publisher
        # PUBLISHERS
        insert_tuple = (remove_base_url(publisher['id']), publisher['display_name'], publisher['alternate_titles'], publisher['country_codes'], publisher['hierarchy_level'], publisher['parent_publisher'], publisher['works_count'], publisher['cited_by_count'], publisher['sources_api_url'], publisher['updated_date'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO publishers (id, display_name, alternate_titles, country_codes, hierarchy_level, parent_publisher, works_count, cited_by_count, sources_api_url, updated_date) VALUES ({question_marks})", insert_tuple
        )        

        # PUBLISHERS COUNTS BY YEAR
        for count in publisher['counts_by_year']:
            insert_tuple = (remove_base_url(publisher['id']), count['year'], count['works_count'], count['cited_by_count'], count['oa_works_count'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO publishers_counts_by_year (publisher_id, year, works_count, cited_by_count, oa_works_count) VALUES ({question_marks})", insert_tuple
            )

        # PUBLISHERS IDS
        for id in publisher['ids']:
            insert_tuple = (remove_base_url(publisher['id']), publisher['openalex'], publisher['ror'], publisher['wikidata'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO publishers_ids (publisher_id, openalex, ror, wikidata) VALUES ({question_marks})", insert_tuple
            )
        
        conn.commit()