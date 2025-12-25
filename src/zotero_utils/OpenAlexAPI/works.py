

def get_work(work_info: dict) -> dict:
    """Given a dict of info on the work, try to find it in OpenAlex"""
    if "doi" in work_info:
        return get_work_by_doi(work_info['doi'])
    if "issn" in work_info:
        return get_work_by_issn(work_info['issn'])
    if "url" in work_info:
        return get_work_by_url(work_info['url'])
    if "author_year" in work_info:
        return get_work_by_author_year(work_info['author_year'])

def get_work_by_doi(doi: str) -> dict:
    """Get a work by its DOI"""
    raise NotImplementedError

def get_work_by_issn(issn: str) -> dict:
    """Get a work by its ISSN"""
    raise NotImplementedError

def get_work_by_url(url: str) -> dict:
    """Get a work by its URL"""
    raise NotImplementedError

def get_work_by_author_year(author_year: str) -> dict:
    """Get a work by its author(s) and publication year."""
    raise NotImplementedError

