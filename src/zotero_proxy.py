from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import json
import traceback
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zotero_utils.OpenAlexDB.citation_network import (
    get_zotero_items_with_dois,
    fetch_and_cache_works,
    build_library_graph,
    get_external_connections,
    get_work_details,
    get_item_citations,
)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'openalex.db')
DB_PATH = os.path.abspath(DB_PATH)

# Global state
db_conn = None
library_work_ids = set()


def get_db_connection():
    """Get or create database connection."""
    global db_conn
    if db_conn is None:
        # Ensure database exists with schema
        init_db_if_needed()
        db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return db_conn


def init_db_if_needed():
    """Initialize database with schema if it doesn't exist or is empty."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if the new tables exist, add them if not
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='zotero_openalex_mapping'"
    )
    if not cursor.fetchone():
        print("Adding zotero_openalex_mapping table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zotero_openalex_mapping (
                zotero_key TEXT PRIMARY KEY,
                openalex_work_id TEXT,
                doi TEXT,
                title TEXT,
                last_updated TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS zotero_openalex_mapping_work_id_idx
            ON zotero_openalex_mapping(openalex_work_id)
        """)

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='works_cited_by'"
    )
    if not cursor.fetchone():
        print("Adding works_cited_by table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS works_cited_by (
                work_id TEXT,
                citing_work_id TEXT,
                fetched_date TEXT,
                PRIMARY KEY (work_id, citing_work_id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS works_cited_by_work_id_idx
            ON works_cited_by(work_id)
        """)

    # Add indexes for works_referenced_works if they don't exist
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS works_referenced_works_work_id_idx
        ON works_referenced_works(work_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS works_referenced_works_ref_id_idx
        ON works_referenced_works(referenced_work_id)
    """)

    conn.commit()
    conn.close()


class ZoteroProxyHandler(SimpleHTTPRequestHandler):

    def send_json_response(self, data, status=200):
        """Helper to send JSON response with CORS headers."""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_response(self, message, status=500):
        """Helper to send error response."""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())

    def get_json_body(self):
        """Parse JSON body from POST request."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        post_data = self.rfile.read(content_length)
        return json.loads(post_data.decode('utf-8'))

    def do_GET(self):
        # Reset cache endpoint - clears stale data to force refresh
        if self.path == '/api/reset-cache':
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM zotero_openalex_mapping")
                cursor.execute("DELETE FROM works_referenced_works")
                cursor.execute("DELETE FROM works_cited_by")
                conn.commit()
                print("Cache cleared!")
                self.send_json_response({'status': 'ok', 'message': 'Cache cleared'})
            except Exception as e:
                print(f'Error clearing cache: {e}')
                self.send_error_response(str(e))
            return

        # Get work details by ID
        if self.path.startswith('/api/work-details/'):
            try:
                work_id = self.path.replace('/api/work-details/', '')
                conn = get_db_connection()
                details = get_work_details(conn, work_id)

                if details:
                    self.send_json_response(details)
                else:
                    self.send_error_response('Work not found', 404)

            except Exception as e:
                print(f'Error getting work details: {e}')
                traceback.print_exc()
                self.send_error_response(str(e))

        # Proxy Zotero API requests
        elif self.path.startswith('/zotero-api/'):
            try:
                zotero_path = self.path.replace('/zotero-api/', '')
                zotero_url = f'http://localhost:23119/api/{zotero_path}'

                print(f'\n=== Proxying request ===')
                print(f'Original path: {self.path}')
                print(f'Zotero URL: {zotero_url}')

                with urllib.request.urlopen(zotero_url) as response:
                    data = response.read()
                    print(f'Success! Got {len(data)} bytes')

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)

            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else 'No error body'
                print(f'\n!!! HTTPError !!!')
                print(f'Status: {e.code}')
                print(f'Reason: {e.reason}')
                print(f'Body: {error_body}')

                self.send_error_response(
                    f'Zotero API error {e.code}: {e.reason}',
                    e.code
                )

            except Exception as e:
                print(f'\n!!! General Exception !!!')
                print(f'Error type: {type(e).__name__}')
                print(f'Error: {str(e)}')
                traceback.print_exc()
                self.send_error_response(f'Proxy error: {str(e)}')

        else:
            # Serve static files normally
            super().do_GET()

    def do_POST(self):
        global library_work_ids

        # Initialize citation network
        if self.path == '/api/init-network':
            try:
                print('\n=== Initializing Citation Network ===')

                # Get Zotero items with DOIs
                items_with_dois, items_without_dois = get_zotero_items_with_dois()

                print(f'Found {len(items_with_dois)} items with DOIs')
                print(f'Skipping {len(items_without_dois)} items without DOIs')

                if not items_with_dois:
                    self.send_json_response({
                        'nodes': [],
                        'edges': [],
                        'library_ids': [],
                        'stats': {
                            'items_with_dois': 0,
                            'items_without_dois': len(items_without_dois),
                        }
                    })
                    return

                # Fetch and cache OpenAlex data
                conn = get_db_connection()
                print('Fetching OpenAlex data...')
                zotero_items_map = fetch_and_cache_works(conn, items_with_dois)

                print(f'Mapped {len(zotero_items_map)} items to OpenAlex')

                # Build the graph
                print('Building citation graph...')
                graph = build_library_graph(conn, zotero_items_map)

                # Store library IDs for expand-node
                library_work_ids = set(graph['library_ids'])

                print(f'Graph: {len(graph["nodes"])} nodes, {len(graph["edges"])} edges')

                # Add stats
                graph['stats'] = {
                    'items_with_dois': len(items_with_dois),
                    'items_without_dois': len(items_without_dois),
                    'mapped_to_openalex': len(zotero_items_map),
                }

                self.send_json_response(graph)

            except Exception as e:
                print(f'Error initializing network: {e}')
                traceback.print_exc()
                self.send_error_response(str(e))

        # Expand a node to show external connections
        elif self.path == '/api/expand-node':
            try:
                data = self.get_json_body()
                work_id = data.get('work_id')

                if not work_id:
                    self.send_error_response('work_id required', 400)
                    return

                print(f'\n=== Expanding node: {work_id} ===')

                conn = get_db_connection()
                expansion = get_external_connections(
                    conn,
                    work_id,
                    library_work_ids,
                    max_refs=20,
                    max_citing=20
                )

                print(f'Found {len(expansion["nodes"])} external nodes, '
                      f'{len(expansion["edges"])} edges')

                self.send_json_response(expansion)

            except Exception as e:
                print(f'Error expanding node: {e}')
                traceback.print_exc()
                self.send_error_response(str(e))

        # Get citations for a single item (for focused graph view)
        elif self.path == '/api/get-item-citations':
            try:
                data = self.get_json_body()
                work_id = data.get('work_id')

                if not work_id:
                    self.send_error_response('work_id required', 400)
                    return

                print(f'\n=== Getting citations for: {work_id} ===')

                conn = get_db_connection()
                citations = get_item_citations(conn, work_id, library_work_ids)

                print(f'Found {len(citations["nodes"])} cited works')

                self.send_json_response(citations)

            except Exception as e:
                print(f'Error getting citations: {e}')
                traceback.print_exc()
                self.send_error_response(str(e))

        else:
            self.send_error_response('Not found', 404)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


if __name__ == '__main__':
    PORT = 8000
    httpd = HTTPServer(('localhost', PORT), ZoteroProxyHandler)
    print(f'Server running at http://localhost:{PORT}/')
    print(f'Database: {DB_PATH}')
    print('Press Ctrl+C to stop')
    httpd.serve_forever()
