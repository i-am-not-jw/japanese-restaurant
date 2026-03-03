import os
import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Manual .env loading since we want to avoid dependencies
def load_simple_env(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    os.environ[k] = v

env_path = "/tmp/japanese_restaurant_data/.env"
load_simple_env(env_path)

WEBHOOK_TOKEN = os.getenv("NOTION_WEBHOOK_SECRET", "antigravity_secret_trigger_2026")

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        
        # 1. Validate Secret Token (Authorization Header)
        auth_header = self.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {WEBHOOK_TOKEN}":
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Unauthorized"}).encode())
            return

        if path == '/trigger-pipeline':
            self.trigger_script("daily_orchestrator.py")
        elif path == '/finalize-sync':
            self.trigger_script("finalize_sync.py")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        query = parse_qs(url.query)
        
        # Validate Token from Query (for browser clicks)
        token = query.get("token", [None])[0]
        if not token or token != WEBHOOK_TOKEN:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Invalid Token")
            return

        if path == '/finalize-sync':
            self.trigger_script("finalize_sync.py", is_get=True)
        elif path == '/trigger-via-browser':
            self.trigger_script("daily_orchestrator.py", is_get=True)
        else:
            self.send_response(404)
            self.end_headers()

    def trigger_script(self, script_name, is_get=False):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(base_dir, "execution", script_name)
            
            print(f"🚀 [Webhook] Triggering: {script_path}")
            subprocess.Popen(["python3", script_path], cwd=base_dir)
            
            if is_get:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                <html>
                    <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                        <h1 style="color: #4CAF50;">✅ Request Received!</h1>
                        <p>{script_name} has been triggered. You can close this tab now.</p>
                        <script>setTimeout(function(){{ window.close(); }}, 1500);</script>
                    </body>
                </html>
                """.encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": f"{script_name} triggered"}).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

def run(port=5001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print("--------------------------------------------------")
    print(f"🛰️  Standard Library Webhook Receiver is running on port {port}!")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("--------------------------------------------------")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
