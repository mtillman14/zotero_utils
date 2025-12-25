import sqlite3
import json
from typing import Union, List

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Institution:

    def __init__(self, institution: pyalex.Institution):
        if not isinstance(institution, pyalex.Institution):
            raise TypeError("institution must be a pyalex.Institution object")        
        self.institution = institution
        self.institution_id = remove_base_url(institution['id'])

    @staticmethod
    def create_institutions_from_web_api_by_ids(conn: sqlite3.Connection, institution_ids: Union[List[str], str]) -> "Institution":
        """
        Query the OpenAlex web API for a particular institution(s) to create the pyalex.Institution dict. Insert the institution(s) into the database.
        """
        if not isinstance(institution_ids, list):
            institution_ids = [institution_ids]
        pyalexInstitutions = pyalex.Institutions().get([institution_ids])
        institutions = [Institution(i) for i in pyalexInstitutions]
        for institution in institutions:
            institution.insert_or_replace_in_db(conn)
        return institutions
    
    @staticmethod
    def read_institutions_from_db_by_ids(conn: sqlite3.Connection, institution_ids: Union[List[str], str]) -> "Institution":
        """
        Query the database for a particular institution to create its pyalex.Institution dict. 
        """
        if not isinstance(institution_ids, list):
            institution_ids = [institution_ids]
        institution_dict = {}
        cursor = conn.cursor()
        # INSTITUTIONS
        cursor.execute("SELECT * FROM institutions WHERE id=?", (remove_base_url(institution_id),))
        institution_id = cursor.fetchone()

        # INSTITUTIONS_ASSOCIATED_INSTITUTIONS

        # INSTITUTIONS_COUNTS_BY_YEAR

        # INSTITUTIONS_GEO

        # INSTITUTIONS_IDS
        return Institution(pyalex.Institution(institution_dict))
    
    def delete(self, conn: sqlite3.Connection):
        """
        Delete the institution from the database.
        """
        institution_id = self.institution_id
        conn.execute("DELETE FROM institutions WHERE id=?", (institution_id,))
        conn.execute("DELETE FROM institutions_associated_institutions WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM institutions_counts_by_year WHERE institution_id=?", (institution_id,))
        conn.execute("DELETE FROM institutions_geo WHERE institution_id=?", (institution_id,))        
        conn.execute("DELETE FROM institutions_ids WHERE institution_id=?", (institution_id,))              

    def insert_or_replace_in_db(self, conn: sqlite3.Connection):
        """
        Insert the institution into the database.
        """
        institution = self.institution
        # INSTITUTIONS
        insert_tuple = (
            remove_base_url(institution['id']), 
            institution['ror'], 
            institution['display_name'], 
            remove_base_url(institution['country_code']), 
            institution['type'], 
            institution['homepage_url'], 
            institution['image_url'], 
            institution['image_thumbnail_url'], 
            institution['display_name_acronyms'],
            institution['display_name_alternatives'],
            institution['works_count'],
            institution['cited_by_count'],
            institution['works_api_url'],
            institution['updated_date']
        )
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO institutions (id, ror, display_name, country_code, type, homepage_url, image_url, image_thumbnail_url, display_name_acronyms, display_name_alternatives, works_count, cited_by_count, works_api_url, updated_date) VALUES ({question_marks})", insert_tuple
        )

        # INSTITUTIONS_ASSOCIATED_INSTITUTIONS
        for associated_institution in institution['associated_institutions']:
            insert_tuple = (
                remove_base_url(institution['id']), 
                remove_base_url(associated_institution['id']),
                associated_institution['relationship']
            )
            conn.execute(
                "REPLACE INTO institutions_associated_institutions (institution_id, associated_institution_id, relationship) VALUES (?, ?, ?)", insert_tuple
            )

        # INSTITUTIONS_COUNTS_BY_YEAR
        for count_by_year in institution['counts_by_year']:
            insert_tuple = (
                remove_base_url(institution['id']), 
                count_by_year['year'],
                count_by_year['works_count'],
                count_by_year['cited_by_count'],
                count_by_year['oa_works_count']
            )
            conn.execute(
                "REPLACE INTO institutions_counts_by_year (institution_id, year, works_count, cited_by_count, oa_works_count) VALUES (?, ?, ?, ?, ?)", insert_tuple
            )

        # INSTITUTIONS_GEO
        for geo in institution['geo']:
            insert_tuple = (
                remove_base_url(institution['id']), 
                geo['city'],
                geo['geonames_city_id'],
                geo['region'],
                geo['country_code'],
                geo['country'],
                geo['latitude'],
                geo['longitude']
            )
            conn.execute(
                "REPLACE INTO institutions_geo (institution_id, city, geonames_city_id, region, country_code, country, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", insert_tuple
            )

        # INSTITUTIONS_IDS
        for id in institution['ids']:
            insert_tuple = (
                remove_base_url(institution['id']), 
                institution['openalex'],
                institution['ror'],
                institution['grid'],
                institution['wikipedia'],
                institution['wikidata'],
                institution['mag']
            )
            conn.execute(
                "REPLACE INTO institutions_ids (institution_id, openalex, ror, grid, wikipedia, wikidata, mag) VALUES (?, ?, ?, ?, ?, ?, ?)", insert_tuple
            )

        conn.commit()