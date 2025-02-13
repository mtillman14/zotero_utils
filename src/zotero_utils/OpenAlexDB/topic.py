import sqlite3
import json

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Topic:

    def __init__(self, topic: pyalex.Topic):
        self.topic = topic

    def insert(self, conn: sqlite3.Connection):
        """
        Insert the topic into the database.
        """
        topic = self.topic
        # TOPICS
        insert_tuple = (remove_base_url(topic['id']),topic['display_name'], remove_base_url(topic['subfield_id']), topic['subfield_display_name'], remove_base_url(topic['field_id']),topic['field_display_name'], remove_base_url(topic['domain_id']), topic['domain_display_name'], topic['description'], topic['keywords'], topic['works_api_url'], topic['wikipedia_id'], topic['works_count'], topic['cited_by_count'], topic['updated_date'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"INSERT INTO topics (id, display_name, subfield_id, subfield_display_name, field_id, field_display_name, domain_id, domain_display_name, description, keywords, works_api_url, wikipedia_id, works_count, cited_by_count, updated_date) VALUES ({question_marks})", insert_tuple
        )