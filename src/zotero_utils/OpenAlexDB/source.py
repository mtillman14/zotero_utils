import sqlite3
import json
from typing import Union, List

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Source:

    def __init__(self, source: pyalex.Source):
        if not isinstance(source, pyalex.Source):
            raise TypeError("source must be a pyalex.Source object")        
        self.source = source
        self.source_id = remove_base_url(source['id'])

    @staticmethod
    def create_sources_from_web_api_by_ids(conn: sqlite3.Connection, source_ids: Union[List[str], str]) -> "Source":
        """
        Query the OpenAlex web API for a particular source(s) to create the pyalex.Source dict. Insert the source(s) into the database.
        """
        if not isinstance(source_ids, list):
            source_ids = [source_ids]
        pyalexSources = pyalex.Sources().get([source_ids])
        sources = [Source(s) for s in pyalexSources]
        for source in sources:
            source.insert_or_replace_in_db(conn)
        return sources
    
    @staticmethod
    def read_sources_from_db_by_ids(conn: sqlite3.Connection, source_ids: Union[List[str], str]) -> "Source":
        """
        Query the database for a particular source to create its pyalex.Source dict. 
        """
        if not isinstance(source_ids, list):
            source_ids = [source_ids]
        source_dict = {}
        cursor = conn.cursor()
        # SOURCES
        cursor.execute("SELECT * FROM sources WHERE id=?", (remove_base_url(source_id),))
        source_id = cursor.fetchone()
        # SOURCES_COUNTS_BY_YEAR

        # SOURCES_IDS
        return Source(pyalex.Source(source_dict))
    
    def delete(self, conn: sqlite3.Connection):
        """
        Delete the source from the database.
        """
        source_id = self.source_id
        conn.execute("DELETE FROM sources WHERE id=?", (source_id,))
        conn.execute("DELETE FROM sources_counts_by_year WHERE source_id=?", (source_id,))
        conn.execute("DELETE FROM sources_ids WHERE source_id=?", (source_id,))

    def insert_or_replace_in_db(self, conn: sqlite3.Connection):
        """
        Insert the source into the database.
        """
        source = self.source
        # SOURCES
        insert_tuple = (remove_base_url(source['id']), source['issn_l'], source['issn'], source['display_name'], source['publisher'], source['works_count'], source['cited_by_count'], source['is_oa'], source['is_in_doaj'], source ['homepage_url'], source['works_api_url'], source['updated_date'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO sources (id, issn_l, issn, display_name, publisher, works_count, cited_by_count, is_oa, is_in_doaj, homepage_url, works_api_url, updated_date) VALUES ({question_marks})", insert_tuple
        )

        # SOURCES_COUNTS_BY_YEAR
        for year, count in source['counts_by_year'].items():
            insert_tuple = (remove_base_url(source['id']), year, count, works_count, cited_by_count, oa_works_count)
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO sources_counts_by_year (source_id, year, works_count, cited_by_count, oa_works_count) VALUES ({question_marks})", insert_tuple
            )

        # SOURCES_IDS
        for ids in source['ids']:
            insert_tuple = (remove_base_url(source['id']), ids['openalex'], ids['issn_l'], ids['issn'], ids['mag'], ids['wikidata'], ids['fatcat'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO sources_ids (source_id, openalex, issn_l, issn, mag, wikidata, fatcat) VALUES ({question_marks})", insert_tuple
            )

        conn.commit()