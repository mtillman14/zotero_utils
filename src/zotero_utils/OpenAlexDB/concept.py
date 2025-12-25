import sqlite3
import json
from typing import Union, List

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Concept:

    def __init__(self, concept: pyalex.Concept):
        if not isinstance(concept, pyalex.Concept):
            raise TypeError("concept must be a pyalex.Concept object")        
        self.concept = concept
        self.concept_id = remove_base_url(concept['id'])

    @staticmethod
    def create_concepts_from_web_api_by_ids(conn: sqlite3.Connection, concept_ids: Union[List[str], str]) -> "Concept":
        """
        Query the OpenAlex web API for a particular concept(s) to create the pyalex.Concept dict. Insert the concept(s) into the database.
        """
        if not isinstance(concept_ids, list):
            concept_ids = [concept_ids]
        pyalexConcepts = pyalex.Concepts().get([concept_ids])
        concepts = [Concept(c) for c in pyalexConcepts]
        for concept in concepts:
            concept.insert_or_replace_in_db(conn)
        return concepts

    @staticmethod
    def read_concepts_from_db_by_ids(conn: sqlite3.Connection, concept_ids: Union[List[str], str]) -> "Concept":
        """
        Query the database for a particular concept to create its pyalex.Concept dict. 
        """
        if not isinstance(concept_ids, list):
            concept_ids = [concept_ids]
        concept_dict = {}
        cursor = conn.cursor()
        # CONCEPTS
        cursor.execute("SELECT * FROM concepts WHERE id=?", (remove_base_url(concept_id),))
        concept_id = cursor.fetchone()

        # CONCEPTS_ANCESTORS

        # CONCEPTS_COUNTS_BY_YEAR

        # CONCEPTS_IDS

        # CONCEPTS_RELATED_CONCEPTS
        return Concept(pyalex.Concept(concept_dict))
    
    def delete(self, conn: sqlite3.Connection):
        """
        Delete the concept from the database.
        """
        concept_id = self.concept_id
        conn.execute("DELETE FROM concepts WHERE id=?", (concept_id,))
        conn.execute("DELETE FROM concepts_ancestors WHERE concept_id=?", (concept_id,))
        conn.execute("DELETE FROM concepts_counts_by_year WHERE concept_id=?", (concept_id,))
        conn.execute("DELETE FROM concepts_ids WHERE concept_id=?", (concept_id,))      
        conn.execute("DELETE FROM concepts_related_concepts WHERE concept_id=?", (concept_id,))   

    def insert_or_replace_in_db(self, conn: sqlite3.Connection):
        """
        REPLACE the concept in the database.
        """
        concept = self.concept
        # CONCEPTS
        insert_tuple = (remove_base_url(concept['id']), concept['wikidata'], concept['display_name'], concept['level'], concept['description'], concept['works_count'], concept['cited_by_count'], concept['image_url'], concept['image_thumbnail_url'], concept['works_api_url'], concept['updated_date'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO concepts (id, wikidata, display_name, level, description, works_count, cited_by_count, image_url, image_thumbnail_url, works_api_url, updated_date) VALUES ({question_marks})", insert_tuple
        )

        # CONCEPTS_ANCESTORS
        for ancestor in concept['ancestors']:
            insert_tuple = (remove_base_url(ancestor['id']), remove_base_url(concept['id']))
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO concepts_ancestors (ancestor_id, concept_id) VALUES ({question_marks})", insert_tuple
            )
        
        # CONCEPTS_COUNTS_BY_YEAR
        for year in concept['counts_by_year']:
            insert_tuple = (remove_base_url(concept['id']), year['year'], year['works_count'], year['cited_by_count'], year['oa_works_count'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO concepts_counts_by_year (concept_id, year, works_count, cited_by_count, oa_works_count) VALUES ({question_marks})", insert_tuple
            )

        # CONCEPTS_IDS
        for id in concept['ids']:
            insert_tuple = (remove_base_url(concept['id']), concept['openalex'], concept['wikidata'], concept['wikipedia'], concept['umls_aui'], concept['umls_cui'], concept['mag'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO concepts_ids (concept_id, openalex, wikidata, wikipedia, umls_aui, umls_cui, mag) VALUES ({question_marks})", insert_tuple
            )

        # CONCEPTS_RELATED_CONCEPTS
        for related_concept in concept['related_concepts']:
            insert_tuple = (remove_base_url(related_concept['id']), remove_base_url(concept['id']))
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO concepts_related_concepts (related_concept_id, concept_id) VALUES ({question_marks})", insert_tuple
            )

        conn.commit()