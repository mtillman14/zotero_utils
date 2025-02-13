import sqlite3
import json

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Author:

    def __init__(self, author: pyalex.Author):
        self.author = author

    def insert(self, conn: sqlite3.Connection):
        """
        Insert the author into the database.
        """
        author = self.author
        # AUTHORS
        insert_tuple = (remove_base_url(author['id']), author['orcid'], author['display_name'], author['display_name_alternatives'], author['works_count'], author['cited_by_count'], author['last_known_institution'], author['works_api_url'], author['updated_date'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"INSERT INTO authors (id, orcid, display_name, display_name_alternatives, works_count, cited_by_count, last_known_institution, works_api_url, updated_date) VALUES ({question_marks})", insert_tuple
        )

        # AUTHORS_COUNTS_BY_YEAR
        for count in author['counts_by_year']:
            insert_tuple = (remove_base_url(author['id']), count['year'], count['works_count'], count['cited_by_count'], count['oa_works_count'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"INSERT INTO authors_counts_by_year (author_id, year, works_count, cited_by_count, oa_works_count) VALUES ({question_marks})", insert_tuple
            )

        # AUTHORS_IDS
        author_ids = author['ids']
        openalex_id = author_ids['openalex']
        orcid_id = author_ids.get('orcid')
        scopus_id = author_ids.get('scopus')
        twitter_id = author_ids.get('twitter')
        wikipedia_id = author_ids.get('wikipedia')
        mag_id = author_ids.get('mag')
        insert_tuple = (remove_base_url(author['id']), openalex_id, orcid_id, scopus_id, twitter_id, wikipedia_id, mag_id)
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"INSERT INTO authors_ids (author_id, openalex_id, orcid_id, scopus_id, twitter_id, wikipedia_id, mag_id) VALUES ({question_marks})", insert_tuple
        )

        