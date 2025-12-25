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
        Insert the work into the database. Uses defensive .get() access for all fields.
        """
        work = self.work
        work_id = self.work_id

        # WORKS - main table
        insert_tuple = (
            work_id,
            str(work.get('doi') or ''),
            work.get('title') or '',
            work.get('display_name') or '',
            work.get('publication_year'),
            work.get('publication_date'),
            work.get('type') or '',
            work.get('cited_by_count') or 0,
            int(work.get('is_retracted') or False),
            int(work.get('is_paratext') or False),
            work.get('cited_by_api_url') or '',
            json.dumps(work.get('abstract_inverted_index') or {}),
            work.get('language') or ''
        )
        conn.execute(
            "REPLACE INTO works (id, doi, title, display_name, publication_year, publication_date, type, cited_by_count, is_retracted, is_paratext, cited_by_api_url, abstract_inverted_index, language) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            insert_tuple
        )

        # WORKS_PRIMARY_LOCATIONS
        primary_loc = work.get('primary_location')
        if primary_loc:
            source = primary_loc.get('source') or {}
            source_id = source.get('id') or ''
            insert_tuple = (
                work_id,
                remove_base_url(source_id) if source_id else None,
                primary_loc.get('landing_page_url'),
                primary_loc.get('pdf_url'),
                int(primary_loc.get('is_oa') or False),
                primary_loc.get('version'),
                primary_loc.get('license')
            )
            conn.execute(
                "REPLACE INTO works_primary_locations (work_id, source_id, landing_page_url, pdf_url, is_oa, version, license) VALUES (?, ?, ?, ?, ?, ?, ?)",
                insert_tuple
            )

        # WORKS_LOCATIONS
        for location in work.get('locations') or []:
            source = location.get('source') or {}
            source_id = source.get('id') or ''
            insert_tuple = (
                work_id,
                remove_base_url(source_id) if source_id else None,
                location.get('landing_page_url'),
                location.get('pdf_url'),
                int(location.get('is_oa') or False),
                location.get('version'),
                location.get('license')
            )
            conn.execute(
                "REPLACE INTO works_locations (work_id, source_id, landing_page_url, pdf_url, is_oa, version, license) VALUES (?, ?, ?, ?, ?, ?, ?)",
                insert_tuple
            )

        # WORKS_BEST_OA_LOCATIONS
        best_oa_loc = work.get('best_oa_location')
        if best_oa_loc:
            source = best_oa_loc.get('source') or {}
            source_id = source.get('id') or ''
            insert_tuple = (
                work_id,
                remove_base_url(source_id) if source_id else None,
                best_oa_loc.get('landing_page_url'),
                best_oa_loc.get('pdf_url'),
                int(best_oa_loc.get('is_oa') or False),
                best_oa_loc.get('version'),
                best_oa_loc.get('license')
            )
            conn.execute(
                "REPLACE INTO works_best_oa_locations (work_id, source_id, landing_page_url, pdf_url, is_oa, version, license) VALUES (?, ?, ?, ?, ?, ?, ?)",
                insert_tuple
            )

        # WORKS_AUTHORSHIPS
        for authorship in work.get('authorships') or []:
            author = authorship.get('author') or {}
            author_id = author.get('id')
            if author_id:
                institutions = authorship.get('institutions') or []
                if institutions:
                    for institution in institutions:
                        inst_id = institution.get('id')
                        insert_tuple = (
                            work_id,
                            authorship.get('author_position'),
                            remove_base_url(author_id),
                            remove_base_url(inst_id) if inst_id else None
                        )
                        conn.execute(
                            "REPLACE INTO works_authorships (work_id, author_position, author_id, institution_id) VALUES (?, ?, ?, ?)",
                            insert_tuple
                        )
                else:
                    # Author with no institution
                    insert_tuple = (
                        work_id,
                        authorship.get('author_position'),
                        remove_base_url(author_id),
                        None
                    )
                    conn.execute(
                        "REPLACE INTO works_authorships (work_id, author_position, author_id, institution_id) VALUES (?, ?, ?, ?)",
                        insert_tuple
                    )

        # WORKS_BIBLIO
        biblio = work.get('biblio') or {}
        insert_tuple = (
            work_id,
            biblio.get('volume'),
            biblio.get('issue'),
            biblio.get('first_page'),
            biblio.get('last_page')
        )
        conn.execute(
            "REPLACE INTO works_biblio (work_id, volume, issue, first_page, last_page) VALUES (?, ?, ?, ?, ?)",
            insert_tuple
        )

        # WORKS_TOPICS
        for topic in work.get('topics') or []:
            topic_id = topic.get('id')
            if topic_id:
                insert_tuple = (work_id, remove_base_url(topic_id), topic.get('score'))
                conn.execute(
                    "REPLACE INTO works_topics (work_id, topic_id, score) VALUES (?, ?, ?)",
                    insert_tuple
                )

        # WORKS_CONCEPTS
        for concept in work.get('concepts') or []:
            concept_id = concept.get('id')
            if concept_id:
                insert_tuple = (work_id, remove_base_url(concept_id), concept.get('score'))
                conn.execute(
                    "REPLACE INTO works_concepts (work_id, concept_id, score) VALUES (?, ?, ?)",
                    insert_tuple
                )

        # WORKS_IDS
        work_ids = work.get('ids') or {}
        insert_tuple = (
            work_id,
            work_ids.get('openalex'),
            work_ids.get('doi'),
            work_ids.get('mag'),
            work_ids.get('pmid'),
            work_ids.get('pmcid')
        )
        conn.execute(
            "REPLACE INTO works_ids (work_id, openalex, doi, mag, pmid, pmcid) VALUES (?, ?, ?, ?, ?, ?)",
            insert_tuple
        )

        # WORKS_MESH
        for mesh in work.get('mesh') or []:
            insert_tuple = (
                work_id,
                mesh.get('descriptor_ui'),
                mesh.get('descriptor_name'),
                mesh.get('qualifier_ui'),
                mesh.get('qualifier_name'),
                mesh.get('is_major_topic')
            )
            conn.execute(
                "REPLACE INTO works_mesh (work_id, descriptor_ui, descriptor_name, qualifier_ui, qualifier_name, is_major_topic) VALUES (?, ?, ?, ?, ?, ?)",
                insert_tuple
            )

        # WORKS_OPEN_ACCESS
        open_access = work.get('open_access') or {}
        insert_tuple = (
            work_id,
            int(open_access.get('is_oa') or False),
            open_access.get('oa_status'),
            open_access.get('oa_url'),
            int(open_access.get('any_repository_has_fulltext') or False)
        )
        conn.execute(
            "REPLACE INTO works_open_access (work_id, is_oa, oa_status, oa_url, any_repository_has_fulltext) VALUES (?, ?, ?, ?, ?)",
            insert_tuple
        )

        # WORKS_REFERENCED_WORKS - This is the key table for citation network!
        for referenced_work_id in work.get('referenced_works') or []:
            if referenced_work_id:
                insert_tuple = (work_id, remove_base_url(referenced_work_id))
                conn.execute(
                    "REPLACE INTO works_referenced_works (work_id, referenced_work_id) VALUES (?, ?)",
                    insert_tuple
                )

        # WORKS_RELATED_WORKS
        for related_work_id in work.get('related_works') or []:
            if related_work_id:
                insert_tuple = (work_id, remove_base_url(related_work_id))
                conn.execute(
                    "REPLACE INTO works_related_works (work_id, related_work_id) VALUES (?, ?)",
                    insert_tuple
                )

        conn.commit()