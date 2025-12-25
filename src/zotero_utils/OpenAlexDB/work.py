import sqlite3
import json
from typing import Union, List

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Work:

    def __init__(self, work: pyalex.Work):
        if not isinstance(work, pyalex.Work):
            raise TypeError("work must be a pyalex.Work object")
        self.work = work
        self.work_id = remove_base_url(work['id'])

    @staticmethod
    def create_works_from_web_api_by_ids(conn: sqlite3.Connection, work_ids: Union[List[str], str]) -> "Work":
        """
        Query the OpenAlex web API for a particular work(s) to create the pyalex.Work dict. Insert the work(s) into the database.
        """
        if not isinstance(work_ids, list):
            work_ids = [work_ids]
        pyalexWorks = pyalex.Works().get([work_ids]) # I think this may be the syntax for just one work. How to do this for a list of works at once?
        works = [Work(w) for w in pyalexWorks]
        for work in works:
            work.insert_or_replace_in_db(conn)
        return works

    @staticmethod
    def read_works_from_db_by_ids(conn: sqlite3.Connection, work_ids: Union[List[str], str]) ->  "Work":
        """
        Query the database for a particular work to create its pyalex.Work dict. 
        """
        if not isinstance(work_ids, list):
            work_ids = [work_ids]
        work_dict = {}
        cursor = conn.cursor()

        # WORKS
        cursor.execute("SELECT * FROM works WHERE id=?", (remove_base_url(work_id),))
        work_id = cursor.fetchone()

        # WORKS_PRIMARY_LOCATIONS

        # WORKS_LOCATIONS

        # WORKS_BEST_OA_LOCATIONS

        # WORKS_AUTHORSHIPS

        # WORKS_BIBLIO

        # WORKS_TOPICS

        # WORKS_CONCEPTS

        # WORKS_IDS

        # WORKS_MESH

        # WORKS_OPEN_ACCESS

        # WORKS_REFERENCED_WORKS

        # WORKS_RELATED_WORKS
        return Work(pyalex.Work(work_dict))
    
    def delete(self, conn: sqlite3.Connection):
        """
        Delete the work from the database.
        """
        work_id = self.work_id
        conn.execute("DELETE FROM works WHERE id=?", (work_id,))
        conn.execute("DELETE FROM works_primary_locations WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_locations WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_best_oa_locations WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_authorships WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_biblio WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_topics WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_concepts WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_ids WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_mesh WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_open_access WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_referenced_works WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM works_related_works WHERE work_id=?", (work_id,))
        conn.commit()

    def insert_or_replace_in_db(self, conn: sqlite3.Connection):
        """
        Insert the work into the database.
        """
        work = self.work
        work_id = self.work_id
        # WORKS
        insert_tuple = (work_id, str(work['doi']), work['title'], work['display_name'], work['publication_year'], work['publication_date'], work['type'], work['cited_by_count'], int(work['is_retracted']), int(work['is_paratext']), work['cited_by_api_url'], json.dumps(work['abstract_inverted_index']), work['language'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO works (id, doi, title, display_name, publication_year, publication_date, type, cited_by_count, is_retracted, is_paratext, cited_by_api_url, abstract_inverted_index, language) VALUES ({question_marks})", insert_tuple
        )

        # WORKS_PRIMARY_LOCATIONS
        insert_tuple = (work_id, remove_base_url(work['primary_location']['source']['id']), work['primary_location']['landing_page_url'], 
                       work['primary_location']['pdf_url'], int(work['primary_location']['is_oa']), work['primary_location']['version'], 
                       work['primary_location']['license'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO works_primary_locations (work_id, source_id, landing_page_url, pdf_url, is_oa, version, license) VALUES ({question_marks})", insert_tuple
        )

        # WORKS_LOCATIONS
        for location in work['locations']:
            insert_tuple = (work_id, remove_base_url(location['source']['id']), location['landing_page_url'], location['pdf_url'], 
                          int(location['is_oa']), location['version'], location['license'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO works_locations (work_id, source_id, landing_page_url, pdf_url, is_oa, version, license) VALUES ({question_marks})", insert_tuple
            )

        # WORKS_BEST_OA_LOCATIONS
        insert_tuple = (work_id, remove_base_url(work['best_oa_location']['source']['id']), work['best_oa_location']['landing_page_url'],
                       work['best_oa_location']['pdf_url'], int(work['best_oa_location']['is_oa']), work['best_oa_location']['version'],
                       work['best_oa_location']['license'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO works_best_oa_locations (work_id, source_id, landing_page_url, pdf_url, is_oa, version, license) VALUES ({question_marks})", insert_tuple
        )

        # WORKS_AUTHORSHIPS
        for authorship in work['authorships']:
            for institution in authorship['institutions']:
                insert_tuple = (work_id, authorship['author_position'], remove_base_url(authorship['author']['id']), 
                              remove_base_url(institution['id']))
                question_marks = ', '.join(['?'] * len(insert_tuple))
                conn.execute(
                    f"REPLACE INTO works_authorships (work_id, author_position, author_id, institution_id) VALUES ({question_marks})", insert_tuple
                )

        # WORKS_BIBLIO
        insert_tuple = (work_id, work['biblio']['volume'], work['biblio']['issue'], work['biblio']['first_page'], work['biblio']['last_page'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO works_biblio (work_id, volume, issue, first_page, last_page) VALUES ({question_marks})", insert_tuple
        )

        # WORKS_TOPICS
        for topic in work['topics']:
            insert_tuple = (work_id, remove_base_url(topic['id']), topic['score'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO works_topics (work_id, topic_id, score) VALUES ({question_marks})", insert_tuple
            )

        # WORKS_CONCEPTS
        for concept in work['concepts']:
            insert_tuple = (work_id, remove_base_url(concept['id']), concept['score'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO works_concepts (work_id, concept_id, score) VALUES ({question_marks})", insert_tuple
            )

        # WORKS_IDS
        work_ids = work['ids']
        openalex_id = work_ids.get('openalex')
        doi = work_ids.get('doi')
        mag = work_ids.get('mag')
        pmid = work_ids.get('pmid')
        pmcid = work_ids.get('pmcid')
        insert_tuple = (work_id, openalex_id, doi, mag, pmid, pmcid)
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO works_ids (work_id, openalex, doi, mag, pmid, pmcid) VALUES ({question_marks})", insert_tuple
        )

        # WORKS_MESH
        for mesh in work['mesh']:
            insert_tuple = (work_id, mesh['descriptor_ui'], mesh['descriptor_name'], 
                          mesh['qualifier_ui'], mesh['qualifier_name'], mesh['is_major_topic'])
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO works_mesh (work_id, descriptor_ui, descriptor_name, qualifier_ui, qualifier_name, is_major_topic) VALUES ({question_marks})", insert_tuple
            )

        # WORKS_OPEN_ACCESS
        insert_tuple = (work_id, int(work['open_access']['is_oa']), work['open_access']['oa_status'], 
                       work['open_access']['oa_url'], int(work['open_access']['any_repository_has_fulltext']))
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO works_open_access (work_id, is_oa, oa_status, oa_url, any_repository_has_fulltext) VALUES ({question_marks})", insert_tuple
        )

        # WORKS_REFERENCED_WORKS
        for referenced_work_id in work['referenced_works']:
            insert_tuple = (work_id, remove_base_url(referenced_work_id))
            question_marks = ', '.join(['?'] * len(insert_tuple))            
            conn.execute(
                f"REPLACE INTO works_referenced_works (work_id, referenced_work_id) VALUES ({question_marks})", insert_tuple
            )

        # WORKS_RELATED_WORKS
        for related_work_id in work['related_works']:
            insert_tuple = (work['id'], remove_base_url(related_work_id))
            question_marks = ', '.join(['?'] * len(insert_tuple))
            conn.execute(
                f"REPLACE INTO works_related_works (work_id, related_work_id) VALUES ({question_marks})", insert_tuple
            )

        conn.commit()