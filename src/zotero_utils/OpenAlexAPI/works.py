from typing import Optional, List
import pyalex
from pyalex import Works


def normalize_doi(doi: str) -> str:
    """Normalize a DOI by removing URL prefixes."""
    if not doi:
        return doi
    doi = doi.strip()
    prefixes = ["https://doi.org/", "http://doi.org/", "doi.org/", "doi:"]
    for prefix in prefixes:
        if doi.lower().startswith(prefix.lower()):
            doi = doi[len(prefix):]
            break
    return doi


def get_work(work_info: dict) -> Optional[dict]:
    """Given a dict of info on the work, try to find it in OpenAlex"""
    if "doi" in work_info:
        return get_work_by_doi(work_info['doi'])
    if "issn" in work_info:
        return get_work_by_issn(work_info['issn'])
    if "url" in work_info:
        return get_work_by_url(work_info['url'])
    if "author_year" in work_info:
        return get_work_by_author_year(work_info['author_year'])
    return None


def get_work_by_doi(doi: str) -> Optional[dict]:
    """Get a work by its DOI using pyalex."""
    doi = normalize_doi(doi)
    if not doi:
        return None
    try:
        # Query using the DOI directly as an identifier
        work = Works()[f"https://doi.org/{doi}"]
        return work
    except Exception:
        # If direct lookup fails, try filter
        try:
            works = Works().filter(doi=doi).get()
            return works[0] if works else None
        except Exception:
            return None


def get_works_by_dois(dois: List[str]) -> List[dict]:
    """
    Batch fetch works by DOI (up to 50 at a time per OpenAlex limit).

    Args:
        dois: List of DOI strings

    Returns:
        List of work dictionaries
    """
    if not dois:
        return []

    # Normalize all DOIs
    normalized_dois = [normalize_doi(doi) for doi in dois if doi]
    normalized_dois = [d for d in normalized_dois if d]  # Remove empty

    all_works = []
    batch_size = 50

    for i in range(0, len(normalized_dois), batch_size):
        batch = normalized_dois[i:i + batch_size]
        try:
            # Use pipe-separated DOIs for OR query
            doi_filter = "|".join(batch)
            works = Works().filter(doi=doi_filter).get()
            all_works.extend(works)
        except Exception as e:
            print(f"Error fetching batch {i}-{i+batch_size}: {e}")
            # Try individual lookups as fallback
            for doi in batch:
                work = get_work_by_doi(doi)
                if work:
                    all_works.append(work)

    return all_works


def get_work_by_id(openalex_id: str) -> Optional[dict]:
    """Get a work by its OpenAlex ID."""
    if not openalex_id:
        return None
    try:
        # Ensure proper format
        if not openalex_id.startswith("W"):
            openalex_id = f"W{openalex_id}"
        work = Works()[openalex_id]
        return work
    except Exception:
        return None


def get_works_by_ids(openalex_ids: List[str]) -> List[dict]:
    """
    Batch fetch works by OpenAlex ID (up to 50 at a time).

    Args:
        openalex_ids: List of OpenAlex Work IDs (e.g., ["W123", "W456"])

    Returns:
        List of work dictionaries
    """
    if not openalex_ids:
        return []

    all_works = []
    batch_size = 50

    for i in range(0, len(openalex_ids), batch_size):
        batch = openalex_ids[i:i + batch_size]
        try:
            # Use pipe-separated IDs for OR query
            id_filter = "|".join(batch)
            works = Works().filter(openalex_id=id_filter).get()
            all_works.extend(works)
        except Exception as e:
            print(f"Error fetching batch {i}-{i+batch_size}: {e}")

    return all_works


def get_citing_works(work_id: str, limit: int = 50) -> List[dict]:
    """
    Get works that cite the given work.

    Args:
        work_id: OpenAlex Work ID (e.g., "W2741809807")
        limit: Maximum number of citing works to return

    Returns:
        List of work dictionaries that cite this work
    """
    if not work_id:
        return []

    # Ensure proper format (remove URL prefix if present)
    if work_id.startswith("https://openalex.org/"):
        work_id = work_id.replace("https://openalex.org/", "")

    try:
        # Use the cites filter to find works that cite this one
        citing_works = Works().filter(cites=work_id).get(per_page=limit)
        return list(citing_works) if citing_works else []
    except Exception as e:
        print(f"Error fetching citing works for {work_id}: {e}")
        return []


def get_work_by_issn(issn: str) -> Optional[dict]:
    """Get a work by its ISSN"""
    raise NotImplementedError


def get_work_by_url(url: str) -> Optional[dict]:
    """Get a work by its URL"""
    raise NotImplementedError


def get_work_by_author_year(author_year: str) -> Optional[dict]:
    """Get a work by its author(s) and publication year."""
    raise NotImplementedError

