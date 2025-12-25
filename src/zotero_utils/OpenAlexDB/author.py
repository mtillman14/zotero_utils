import sqlite3
import json
from typing import Union, List

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Author:

    def __init__(self, author: pyalex.Author):
        if not isinstance(author, pyalex.Author):
            raise TypeError("author must be a pyalex.Author object")
        self.author = author
        self.author_id = remove_base_url(author['id'])

    @staticmethod
    def create_authors_from_web_api_by_ids(conn: sqlite3.Connection, author_ids: Union[List[str], str]) -> "Author":
        """
        Query the OpenAlex web API for a particular author(s) to create the pyalex.Author dict. Insert the author(s) into the database.
        """
        if not isinstance(author_ids, list):
            author_ids = [author_ids]
        pyalexAuthors = pyalex.Authors().get([author_ids]) # I think this may be the syntax for just one author. How to do this for a list of authors at once?
        authors = [Author(a) for a in pyalexAuthors]
        for author in authors:
            author.insert_or_replace_in_db(conn)
        return authors

    @staticmethod
    def read_authors_from_db_by_ids(conn: sqlite3.Connection, author_ids: Union[List[str], str]) -> "Author":
        """
        Query the database for a particular author to create its pyalex.Author dict. 
        """
        if not isinstance(author_ids, list):
            author_ids = [author_ids]
        author_dict = {}
        cursor = conn.cursor()
        # AUTHORS
        cursor.execute("SELECT * FROM authors WHERE id=?", (remove_base_url(author_id),))
        author_id = cursor.fetchone()

        # AUTHORS_COUNTS_BY_YEAR

        # AUTHORS_IDS        
        return Author(pyalex.Author(author_dict))
    
    def delete(self, conn: sqlite3.Connection):
        """
        Delete the author from the database.
        """
        author_id = self.author_id
        conn.execute("DELETE FROM authors WHERE id=?", (author_id,))
        conn.execute("DELETE FROM authors_counts_by_year WHERE author_id=?", (author_id,))
        conn.execute("DELETE FROM authors_ids WHERE author_id=?", (author_id,))

    def insert_or_replace_in_db(self, conn: sqlite3.Connection):
        """
        REPLACE the author in the database.
        """
        author = self.author
        # AUTHORS
        insert_tuple = (remove_base_url(author['id']), author['orcid'], author['display_name'], author['display_name_alternatives'], author['works_count'], author['cited_by_count'], author['last_known_institution'], author['works_api_url'], author['updated_date'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO authors (id, orcid, display_name, display_name_alternatives, works_count, cited_by_count, last_known_institution, works_api_url, updated_date) VALUES ({question_marks})", insert_tuple
        )

        # AUTHORS_COUNTS_BY_YEAR
        for count in author['counts_by_year']:
            insert_tuple = (remove_base_url(author['id']), count['year'], count['works_count'], count['cited_by_count'], count['oa_works_count'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO authors_counts_by_year (author_id, year, works_count, cited_by_count, oa_works_count) VALUES ({question_marks})", insert_tuple
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
            f"REPLACE INTO authors_ids (author_id, openalex_id, orcid_id, scopus_id, twitter_id, wikipedia_id, mag_id) VALUES ({question_marks})", insert_tuple
        )

        conn.commit()

        