from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import json
import traceback
import random

# Simulated edges storage - in the future this would come from your NetworkX digraph
# Format matches NetworkX DiGraph.edges() output: list of (source, target) tuples
# with optional edge attributes
cached_items = []

def generate_fake_edges(item_keys):
    """
    Generate fake citation edges between items.

    This simulates what your Python database library would return.
    In production, this would be replaced with:
        edges = list(your_networkx_digraph.edges(data=True))

    Returns edges in NetworkX-compatible format:
        [(source_id, target_id, {attr_dict}), ...]
    """
    edges = []
    if len(item_keys) < 2:
        return edges

    # Generate some random directed edges (simulating citations)
    # Each edge means: source "cites" or "references" target
    num_edges = min(len(item_keys), random.randint(3, 7))

    used_pairs = set()
    for _ in range(num_edges):
        source = random.choice(item_keys)
        target = random.choice(item_keys)

        # No self-loops, no duplicate edges
        if source != target and (source, target) not in used_pairs:
            used_pairs.add((source, target))
            edges.append((source, target, {"type": "cites"}))

    return edges

class ZoteroProxyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Endpoint to get edges for the current items
        if self.path == '/api/edges':
            try:
                edges = generate_fake_edges(cached_items)

                # Convert to JSON-serializable format
                # This format directly mirrors NetworkX DiGraph.edges(data=True)
                edges_json = [
                    {"source": s, "target": t, "data": d}
                    for s, t, d in edges
                ]

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(edges_json).encode())

            except Exception as e:
                print(f'Error generating edges: {e}')
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())

        # If requesting the Zotero API, proxy it
        elif self.path.startswith('/zotero-api/'):
            try:
                # Remove /zotero-api/ prefix and build Zotero URL
                zotero_path = self.path.replace('/zotero-api/', '')
                zotero_url = f'http://localhost:23119/api/{zotero_path}'
                
                print(f'\n=== Proxying request ===')
                print(f'Original path: {self.path}')
                print(f'Zotero URL: {zotero_url}')
                
                # Fetch from Zotero
                with urllib.request.urlopen(zotero_url) as response:
                    data = response.read()
                    print(f'Success! Got {len(data)} bytes')
                
                # Send response
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
                
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Zotero API error {e.code}: {e.reason}\n{error_body}'.encode())
                
            except Exception as e:
                print(f'\n!!! General Exception !!!')
                print(f'Error type: {type(e).__name__}')
                print(f'Error: {str(e)}')
                traceback.print_exc()
                
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Proxy error: {str(e)}'.encode())
        else:
            # Serve static files normally
            super().do_GET()

    def do_POST(self):
        global cached_items

        # Endpoint to register item keys and get edges back
        if self.path == '/api/edges':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                # Store item keys for edge generation
                cached_items = data.get('item_keys', [])
                print(f'\n=== Received {len(cached_items)} item keys ===')

                # Generate edges for these items
                edges = generate_fake_edges(cached_items)

                # Convert to JSON-serializable format
                # This format directly mirrors NetworkX DiGraph.edges(data=True)
                edges_json = [
                    {"source": s, "target": t, "data": d}
                    for s, t, d in edges
                ]

                print(f'Generated {len(edges_json)} edges')

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(edges_json).encode())

            except Exception as e:
                print(f'Error in POST /api/edges: {e}')
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

PORT = 8000
httpd = HTTPServer(('localhost', PORT), ZoteroProxyHandler)
print(f'Server running at http://localhost:{PORT}/')
print('Press Ctrl+C to stop')
httpd.serve_forever()