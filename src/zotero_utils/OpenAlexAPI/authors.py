

def get_author(author_info: dict) -> dict:
    """Get an author based on their info"""
    if 'orcid' in author_info:
        return get_author_by_orcid(author_info['orcid'])
    if 'name' in author_info:
        return get_author_by_name(author_info['name'])
    
def get_author_by_orcid(orcid: str) -> dict:
    """Get an author from their ORCID ID"""
    raise NotImplementedError

def get_author_by_name(author_name: str) -> dict:
    """Attempt to get an author from their name"""
    raise NotImplementedError