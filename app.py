import http.server
import socketserver
import urllib.request
import urllib.parse
import sys
import webbrowser
import threading
import os
import time

PORT = int(os.environ.get("PORT", 8000))
BASE_URL = "https://index-api.tpso.go.th"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

class LocalProxyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path.startswith("/api/tpso/"):
            tpso_path = parsed_url.path.replace("/api/tpso/", "/OpenApi/")
            url = f"{BASE_URL}{tpso_path}"
            if parsed_url.query:
                url += f"?{parsed_url.query}"
            
            print(f"[Proxy GET] -> {url}")
            req = urllib.request.Request(url, headers=HEADERS, method='GET')
            try:
                with urllib.request.urlopen(req) as r:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(r.read())
            except Exception as e:
                print(f"Error proxying GET: {e}", file=sys.stderr)
                self.send_error(502, f"Bad Gateway: {e}")
            return
        
        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path.startswith("/api/tpso/"):
            tpso_path = parsed_url.path.replace("/api/tpso/", "/OpenApi/")
            url = f"{BASE_URL}{tpso_path}"
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            print(f"[Proxy POST] -> {url}")
            req = urllib.request.Request(
                url,
                data=post_data,
                headers={'Content-Type': 'application/json', 'User-Agent': HEADERS['User-Agent']},
                method='POST'
            )
            try:
                with urllib.request.urlopen(req) as r:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(r.read())
            except Exception as e:
                print(f"Error proxying POST: {e}", file=sys.stderr)
                self.send_error(502, f"Bad Gateway: {e}")
            return
        
        self.send_error(404, "Endpoint not found")

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LocalProxyHandler) as httpd:
        print(f"Local Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        httpd.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    
    print("Opening browser...")
    webbrowser.open(f"http://localhost:{PORT}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        sys.exit(0)
