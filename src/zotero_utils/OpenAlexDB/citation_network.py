"""
Citation Network Module

Builds citation network graphs from Zotero library items using OpenAlex data.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from ..Classes.item import get_items, get_openalex_work_id
from ..OpenAlexAPI.works import (
    get_work_by_doi,
    get_works_by_dois,
    get_works_by_ids,
    get_citing_works,
    normalize_doi,
)
from .work import Work
from .clean import remove_base_url


def get_zotero_items_with_dois() -> Tuple[List[dict], List[dict]]:
    """
    Fetch all Zotero items and filter to those with DOIs.

    Returns:
        Tuple of (items_with_dois, items_without_dois)
        Each item dict contains: zotero_key, doi, title, authors, itemType
    """
    items = get_items(source='user', incl_attachments=False)

    if not items:
        return [], []

    items_with_dois = []
    items_without_dois = []

    for item in items:
        data = item.get('data', {})
        doi = data.get('DOI', '').strip()
        title = data.get('title', 'Untitled')
        item_type = data.get('itemType', 'unknown')

        # Format authors
        creators = data.get('creators', [])
        authors = format_authors(creators)

        item_info = {
            'zotero_key': item.get('key'),
            'title': title,
            'authors': authors,
            'itemType': item_type,
            'year': extract_year(data.get('date', '')),
        }

        if doi:
            item_info['doi'] = normalize_doi(doi)
            items_with_dois.append(item_info)
        else:
            items_without_dois.append(item_info)

    return items_with_dois, items_without_dois


def format_authors(creators: List[dict]) -> str:
    """Format creator list into author string."""
    if not creators:
        return "No authors"

    author_names = []
    for c in creators[:2]:
        name = c.get('lastName') or c.get('name', '')
        if name:
            author_names.append(name)

    if not author_names:
        return "No authors"

    result = ", ".join(author_names)
    if len(creators) > 2:
        result += " et al."
    return result


def extract_year(date_str: str) -> Optional[int]:
    """Extract year from a date string."""
    if not date_str:
        return None
    # Try to find a 4-digit year
    import re
    match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if match:
        return int(match.group())
    return None


def fetch_and_cache_works(
    conn: sqlite3.Connection,
    zotero_items: List[dict]
) -> Dict[str, dict]:
    """
    Fetch OpenAlex works for Zotero items and cache in SQLite.

    Args:
        conn: SQLite database connection
        zotero_items: List of item dicts with 'doi' and 'zotero_key'

    Returns:
        Dict mapping zotero_key -> work_info dict with openalex_work_id
    """
    cursor = conn.cursor()
    result = {}

    # Check which items are already cached
    dois_to_fetch = []
    work_ids_needing_refs = []  # Work IDs that need referenced_works fetched
    cached_count = 0

    for item in zotero_items:
        zotero_key = item['zotero_key']
        doi = item.get('doi')

        if not doi:
            continue

        # Check cache first
        cursor.execute(
            "SELECT openalex_work_id FROM zotero_openalex_mapping WHERE zotero_key = ?",
            (zotero_key,)
        )
        row = cursor.fetchone()

        if row and row[0]:
            openalex_id = row[0]

            # Check if the work exists in the works table (fully cached)
            cursor.execute(
                "SELECT COUNT(*) FROM works WHERE id = ?",
                (openalex_id,)
            )
            work_exists = cursor.fetchone()[0] > 0

            if work_exists:
                # Fully cached - use cached data
                cached_count += 1
                result[zotero_key] = {
                    'openalex_work_id': openalex_id,
                    'doi': doi,
                    'title': item['title'],
                    'authors': item['authors'],
                    'year': item.get('year'),
                    'in_library': True,
                }
            else:
                # Mapping exists but work data missing - need to fetch
                work_ids_needing_refs.append((zotero_key, doi, item, openalex_id))
        else:
            dois_to_fetch.append((zotero_key, doi, item))

    # Report cache status
    total_with_dois = len([i for i in zotero_items if i.get('doi')])
    print(f"Cache status: {cached_count}/{total_with_dois} items fully cached")

    if work_ids_needing_refs:
        print(f"  {len(work_ids_needing_refs)} items have mapping but need work data")
    if dois_to_fetch:
        print(f"  {len(dois_to_fetch)} items need to be fetched from OpenAlex")

    # Batch fetch missing works from OpenAlex
    if dois_to_fetch:
        dois_only = [d[1] for d in dois_to_fetch]
        print(f"Fetching {len(dois_only)} works from OpenAlex by DOI...")
        works = get_works_by_dois(dois_only)

        # Create lookup by normalized DOI
        works_by_doi = {}
        for work in works:
            work_doi = work.get('doi', '')
            if work_doi:
                normalized = normalize_doi(work_doi)
                works_by_doi[normalized] = work

        # Match and cache
        now = datetime.now().isoformat()
        for zotero_key, doi, item in dois_to_fetch:
            work = works_by_doi.get(doi)
            if work:
                openalex_id = remove_base_url(work.get('id', ''))

                # Cache the mapping
                cursor.execute("""
                    INSERT OR REPLACE INTO zotero_openalex_mapping
                    (zotero_key, openalex_work_id, doi, title, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (zotero_key, openalex_id, doi, item['title'], now))

                # Cache the work data (including referenced_works)
                try:
                    work_obj = Work(work)
                    work_obj.insert_or_replace_in_db(conn)
                    print(f"  Fetched & cached: {openalex_id} ({len(work.get('referenced_works', []))} refs)")
                except Exception as e:
                    print(f"  Error caching work {openalex_id}: {e}")

                result[zotero_key] = {
                    'openalex_work_id': openalex_id,
                    'doi': doi,
                    'title': work.get('title', item['title']),
                    'authors': item['authors'],
                    'year': work.get('publication_year') or item.get('year'),
                    'in_library': True,
                }

        conn.commit()

    # Fetch referenced works for cached items that don't have them
    if work_ids_needing_refs:
        print(f"Fetching work data for {len(work_ids_needing_refs)} items with incomplete cache...")
        ids_to_fetch = [item[3] for item in work_ids_needing_refs]
        works = get_works_by_ids(ids_to_fetch)

        # Create lookup by work ID
        works_by_id = {remove_base_url(w.get('id', '')): w for w in works}

        for zotero_key, doi, item, openalex_id in work_ids_needing_refs:
            work = works_by_id.get(openalex_id)
            if work:
                try:
                    work_obj = Work(work)
                    work_obj.insert_or_replace_in_db(conn)
                except Exception as e:
                    print(f"Error caching work {openalex_id}: {e}")

                # Add to result
                result[zotero_key] = {
                    'openalex_work_id': openalex_id,
                    'doi': doi,
                    'title': work.get('title', item['title']),
                    'authors': item['authors'],
                    'year': work.get('publication_year') or item.get('year'),
                    'in_library': True,
                }

        conn.commit()
        print(f"  Fetched and cached {len(works)} works")

    return result


def get_referenced_works_from_cache(
    conn: sqlite3.Connection,
    work_id: str
) -> List[str]:
    """Get works referenced by this work from cache."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT referenced_work_id FROM works_referenced_works WHERE work_id = ?",
        (work_id,)
    )
    return [row[0] for row in cursor.fetchall()]


def get_citing_works_from_cache(
    conn: sqlite3.Connection,
    work_id: str
) -> List[str]:
    """Get works that cite this work from cache."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT citing_work_id FROM works_cited_by WHERE work_id = ?",
        (work_id,)
    )
    return [row[0] for row in cursor.fetchall()]


def cache_citing_works(
    conn: sqlite3.Connection,
    work_id: str,
    citing_work_ids: List[str]
) -> None:
    """Cache citing works in the database."""
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    for citing_id in citing_work_ids:
        cursor.execute("""
            INSERT OR REPLACE INTO works_cited_by
            (work_id, citing_work_id, fetched_date)
            VALUES (?, ?, ?)
        """, (work_id, citing_id, now))
    conn.commit()


def build_library_graph(
    conn: sqlite3.Connection,
    zotero_items_map: Dict[str, dict]
) -> dict:
    """
    Build the initial graph with library items and edges between them.

    Args:
        conn: SQLite database connection
        zotero_items_map: Dict from zotero_key -> work_info

    Returns:
        Dict with 'nodes', 'edges', and 'library_ids'
    """
    nodes = []
    edges = []
    library_work_ids = set()

    # Build nodes from library items
    work_id_to_zotero = {}
    for zotero_key, info in zotero_items_map.items():
        work_id = info.get('openalex_work_id')
        if work_id:
            library_work_ids.add(work_id)
            work_id_to_zotero[work_id] = zotero_key

            nodes.append({
                'id': work_id,
                'zotero_key': zotero_key,
                'title': info.get('title', 'Untitled'),
                'authors': info.get('authors', ''),
                'year': info.get('year'),
                'doi': info.get('doi'),
                'nodeType': 'library',
            })

    # Find edges between library items
    # Check which library items reference other library items
    total_refs = 0
    for work_id in library_work_ids:
        referenced = get_referenced_works_from_cache(conn, work_id)
        total_refs += len(referenced)
        for ref_id in referenced:
            if ref_id in library_work_ids:
                edges.append({
                    'source': work_id,
                    'target': ref_id,
                    'type': 'cites',
                })

    print(f"Found {total_refs} total references across {len(library_work_ids)} library items")
    print(f"Found {len(edges)} edges between library items")

    return {
        'nodes': nodes,
        'edges': edges,
        'library_ids': list(library_work_ids),
    }


def get_external_connections(
    conn: sqlite3.Connection,
    work_id: str,
    library_work_ids: Set[str],
    max_refs: int = 20,
    max_citing: int = 20
) -> dict:
    """
    Get external references and citations for a work.

    Args:
        conn: SQLite database connection
        work_id: OpenAlex work ID to expand
        library_work_ids: Set of work IDs already in library
        max_refs: Maximum referenced works to return
        max_citing: Maximum citing works to return

    Returns:
        Dict with 'nodes' and 'edges' for external connections
    """
    nodes = []
    edges = []
    seen_ids = set()

    # Get referenced works (what this paper cites)
    referenced = get_referenced_works_from_cache(conn, work_id)

    # Filter to external only and limit
    external_refs = [r for r in referenced if r not in library_work_ids][:max_refs]

    # Get citing works from cache or API
    citing_cached = get_citing_works_from_cache(conn, work_id)

    if not citing_cached:
        # Fetch from API
        citing_works = get_citing_works(work_id, limit=max_citing)
        citing_ids = [remove_base_url(w.get('id', '')) for w in citing_works]

        # Cache for future use
        cache_citing_works(conn, work_id, citing_ids)

        # Also cache minimal work info for these
        for work in citing_works:
            try:
                work_obj = Work(work)
                work_obj.insert_or_replace_in_db(conn)
            except Exception:
                pass
        conn.commit()

        citing_cached = citing_ids

    # Filter to external only and limit
    external_citing = [c for c in citing_cached if c not in library_work_ids][:max_citing]

    # Fetch details for external works we need to display
    all_external_ids = list(set(external_refs + external_citing))

    # Try to get details from cache first
    work_details = {}
    cursor = conn.cursor()
    for ext_id in all_external_ids:
        cursor.execute(
            "SELECT title, publication_year FROM works WHERE id = ?",
            (ext_id,)
        )
        row = cursor.fetchone()
        if row:
            work_details[ext_id] = {
                'title': row[0] or 'Unknown Title',
                'year': row[1],
            }

    # Fetch missing details from API
    missing_ids = [i for i in all_external_ids if i not in work_details]
    if missing_ids:
        fetched_works = get_works_by_ids(missing_ids)
        for work in fetched_works:
            ext_id = remove_base_url(work.get('id', ''))
            work_details[ext_id] = {
                'title': work.get('title', 'Unknown Title'),
                'year': work.get('publication_year'),
            }
            # Cache it
            try:
                work_obj = Work(work)
                work_obj.insert_or_replace_in_db(conn)
            except Exception:
                pass

    # Build external nodes
    for ext_id in all_external_ids:
        if ext_id not in seen_ids:
            details = work_details.get(ext_id, {})
            nodes.append({
                'id': ext_id,
                'title': details.get('title', 'Unknown Title'),
                'year': details.get('year'),
                'authors': '',
                'nodeType': 'external',
            })
            seen_ids.add(ext_id)

    # Build edges for referenced works (this paper -> ref)
    for ref_id in external_refs:
        edges.append({
            'source': work_id,
            'target': ref_id,
            'type': 'cites',
        })

    # Build edges for citing works (citing paper -> this paper)
    for citing_id in external_citing:
        edges.append({
            'source': citing_id,
            'target': work_id,
            'type': 'cites',
        })

    return {
        'nodes': nodes,
        'edges': edges,
    }


def get_work_details(conn: sqlite3.Connection, work_id: str) -> Optional[dict]:
    """Get details for a single work from cache or API."""
    cursor = conn.cursor()

    # Try cache first
    cursor.execute("""
        SELECT title, publication_year, doi FROM works WHERE id = ?
    """, (work_id,))
    row = cursor.fetchone()

    if row:
        return {
            'id': work_id,
            'title': row[0],
            'year': row[1],
            'doi': row[2],
        }

    # Fetch from API
    from ..OpenAlexAPI.works import get_work_by_id
    work = get_work_by_id(work_id)
    if work:
        return {
            'id': work_id,
            'title': work.get('title', 'Unknown'),
            'year': work.get('publication_year'),
            'doi': work.get('doi'),
        }

    return None


def get_authors_for_work(conn: sqlite3.Connection, work_id: str) -> str:
    """Get formatted author string for a work from the database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.display_name
        FROM works_authorships wa
        JOIN authors a ON wa.author_id = a.id
        WHERE wa.work_id = ?
        ORDER BY wa.author_position
        LIMIT 2
    """, (work_id,))
    rows = cursor.fetchall()

    if not rows:
        return ""

    names = [row[0] for row in rows if row[0]]
    if not names:
        return ""

    result = ", ".join(names)

    # Check if there are more authors
    cursor.execute(
        "SELECT COUNT(*) FROM works_authorships WHERE work_id = ?",
        (work_id,)
    )
    total = cursor.fetchone()[0]
    if total > 2:
        result += " et al."

    return result


def extract_authors_from_work(work: dict) -> str:
    """Extract formatted author string from OpenAlex work dict."""
    authorships = work.get('authorships', [])
    if not authorships:
        return ""

    names = []
    for authorship in authorships[:2]:
        author = authorship.get('author', {})
        name = author.get('display_name', '')
        if name:
            names.append(name)

    if not names:
        return ""

    result = ", ".join(names)
    if len(authorships) > 2:
        result += " et al."

    return result


def get_item_citations(
    conn: sqlite3.Connection,
    work_id: str,
    library_work_ids: Set[str]
) -> dict:
    """
    Get all works cited by a specific item.

    Args:
        conn: SQLite database connection
        work_id: OpenAlex work ID of the item
        library_work_ids: Set of work IDs in the user's library

    Returns:
        Dict with 'nodes' and 'edges' for the citation graph
    """
    nodes = []
    edges = []

    # Get referenced works from cache
    referenced = get_referenced_works_from_cache(conn, work_id)

    if not referenced:
        return {'nodes': [], 'edges': []}

    # Get details for all referenced works from cache first
    cursor = conn.cursor()
    work_details = {}
    missing_ids = []
    missing_authors_ids = []  # Works in cache but missing author data

    for ref_id in referenced:
        cursor.execute(
            "SELECT title, publication_year FROM works WHERE id = ?",
            (ref_id,)
        )
        row = cursor.fetchone()
        if row and row[0]:
            # Get authors from database
            authors = get_authors_for_work(conn, ref_id)
            work_details[ref_id] = {
                'title': row[0],
                'year': row[1],
                'authors': authors,
            }
            # If no authors found, we need to re-fetch to get author data
            if not authors:
                missing_authors_ids.append(ref_id)
        else:
            missing_ids.append(ref_id)

    # Fetch works that are missing entirely
    if missing_ids:
        print(f"  Fetching details for {len(missing_ids)} external works...")
        fetched_works = get_works_by_ids(missing_ids)

        for work in fetched_works:
            ext_id = remove_base_url(work.get('id', ''))
            authors = extract_authors_from_work(work)
            work_details[ext_id] = {
                'title': work.get('title', 'Unknown Title'),
                'year': work.get('publication_year'),
                'authors': authors,
            }
            # Cache the work for future use
            try:
                work_obj = Work(work)
                work_obj.insert_or_replace_in_db(conn)
            except Exception:
                pass

        conn.commit()

        # Fill in any still-missing works
        for ref_id in missing_ids:
            if ref_id not in work_details:
                work_details[ref_id] = {
                    'title': 'Unknown Title',
                    'year': None,
                    'authors': '',
                }

    # Fetch works that are cached but missing author data
    if missing_authors_ids:
        print(f"  Fetching author data for {len(missing_authors_ids)} cached works...")
        fetched_works = get_works_by_ids(missing_authors_ids)

        for work in fetched_works:
            ext_id = remove_base_url(work.get('id', ''))
            authors = extract_authors_from_work(work)

            # Update work_details with the fetched authors
            if ext_id in work_details:
                work_details[ext_id]['authors'] = authors

            # Update the cache with author data
            try:
                work_obj = Work(work)
                work_obj.insert_or_replace_in_db(conn)
            except Exception:
                pass

        conn.commit()

    # Build nodes for referenced works
    for ref_id in referenced:
        details = work_details.get(ref_id, {'title': 'Unknown Title', 'year': None, 'authors': ''})
        is_in_library = ref_id in library_work_ids

        nodes.append({
            'id': ref_id,
            'title': details.get('title', 'Unknown Title'),
            'year': details.get('year'),
            'authors': details.get('authors', ''),
            'nodeType': 'library' if is_in_library else 'external',
        })

        # Edge from central item to this reference
        edges.append({
            'source': work_id,
            'target': ref_id,
            'type': 'cites',
        })

    return {
        'nodes': nodes,
        'edges': edges,
    }
