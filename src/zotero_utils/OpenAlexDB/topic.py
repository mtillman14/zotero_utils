import sqlite3
import json
from typing import Union, List

import pyalex

from zotero_utils.OpenAlexDB.clean import remove_base_url

class Topic:

    def __init__(self, topic: pyalex.Topic):
        if not isinstance(topic, pyalex.Topic):
            raise TypeError("topic must be a pyalex.Topic object")        
        self.topic = topic
        self.topic_id = remove_base_url(topic['id'])

    @staticmethod
    def create_topics_from_web_api_by_ids(conn: sqlite3.Connection, topic_ids: Union[List[str], str]) -> "Topic":
        """
        Query the OpenAlex web API for a particular topic(s) to create the pyalex.Topic dict. Insert the topic(s) into the database.
        """
        if not isinstance(topic_ids, list):
            topic_ids = [topic_ids]
        pyalexTopics = pyalex.Topics().get([topic_ids])
        topics = [Topic(t) for t in pyalexTopics]
        for topic in topics:
            topic.insert_or_replace_in_db(conn)
        return topics

    @staticmethod
    def read_topics_from_db_by_ids(conn: sqlite3.Connection, topic_ids: Union[List[str], str]) -> "Topic":
        """
        Query the database for a particular topic to create its pyalex.Topic dict. 
        """
        if not isinstance(topic_ids, list):
            topic_ids = [topic_ids]
        topic_dict = {}
        cursor = conn.cursor()
        # TOPICS
        cursor.execute("SELECT * FROM topics WHERE id=?", (remove_base_url(topic_id),))
        topic_id = cursor.fetchone()
        return Topic(pyalex.Topic(topic_dict))
    
    def delete(self, conn: sqlite3.Connection):
        """
        Delete the topic from the database.
        """
        topic_id = self.topic_id
        conn.execute("DELETE FROM topics WHERE id=?", (topic_id,))

    def insert_or_replace_in_db(self, conn: sqlite3.Connection):
        """
        Insert the topic into the database.
        """
        topic = self.topic
        # TOPICS
        insert_tuple = (remove_base_url(topic['id']),topic['display_name'], remove_base_url(topic['subfield_id']), topic['subfield_display_name'], remove_base_url(topic['field_id']),topic['field_display_name'], remove_base_url(topic['domain_id']), topic['domain_display_name'], topic['description'], topic['keywords'], topic['works_api_url'], topic['wikipedia_id'], topic['works_count'], topic['cited_by_count'], topic['updated_date'])
        question_marks = ', '.join(['?'] * len(insert_tuple))
        conn.execute(
            f"REPLACE INTO topics (id, display_name, subfield_id, subfield_display_name, field_id, field_display_name, domain_id, domain_display_name, description, keywords, works_api_url, wikipedia_id, works_count, cited_by_count, updated_date) VALUES ({question_marks})", insert_tuple
        )

        conn.commit()