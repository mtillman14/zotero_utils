"""Communicate with the OpenAlex API"""

from .works import get_work
from .authors import get_author

class OpenAlexAPIContactor:

    BASE_URL = '' # Base URL for the OpenAlex web API
    
    def get_work(work_info: dict) -> dict:
        """Get the specified work from the OpenAlex web API"""
        return get_work(work_info)
    
    def get_author(author_info: dict) -> dict:
        """Get the specified author from the OpenAlex web API"""
        return get_author(author_info)

    def get_institution(institution_info: dict) -> dict:
        """Get the specified institution from the OpenAlex web API"""
        pass

    def get_source(source_info: dict) -> dict:
        """Get the specified source from the OpenAlex web API"""
        pass    