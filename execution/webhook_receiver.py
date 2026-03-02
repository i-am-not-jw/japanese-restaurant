import os
import subprocess
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from accessible /tmp path
env_path = "/tmp/japanese_restaurant_data/.env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

# Security Token (Should be set in .env)
# Notion Button settings -> Custom headers -> "Authorization": "Bearer YOUR_TOKEN"
WEBHOOK_TOKEN = os.getenv("NOTION_WEBHOOK_SECRET", "default_secret_change_me")

@app.route('/trigger-via-browser', methods=['GET'])
def trigger_via_browser():
    # 1. Validate Token from URL query
    token = request.args.get("token")
    if not token or token != WEBHOOK_TOKEN:
        return "Invalid Token", 401

    # 2. Trigger Orchestrator (Non-blocking)
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        orchestrator_path = os.path.join(base_dir, "execution", "daily_orchestrator.py")
        
        print(f"🚀 [Webhook] Triggering pipeline: {orchestrator_path}")
        
        subprocess.Popen(["python3", orchestrator_path], cwd=base_dir)
        
        # 3. Return a simple auto-closing success page
        return """
        <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                <h1 style="color: #2eaadc;">🚀 Pipeline Started!</h1>
                <p>You can close this tab now.</p>
                <script>setTimeout(function(){ window.close(); }, 1500);</script>
            </body>
        </html>
        """
    except Exception as e:
        return str(e), 500

@app.route('/trigger-pipeline', methods=['POST'])
def trigger_pipeline():
    # 1. Validate Secret Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {WEBHOOK_TOKEN}":
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 2. Trigger Orchestrator (Non-blocking)
    # We use subprocess.Popen so the Flask response isn't delayed by the long-running pipeline
    try:
        # Get absolute path to the orchestrator
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        orchestrator_path = os.path.join(base_dir, "execution", "daily_orchestrator.py")
        
        print(f"🚀 [Webhook] Triggering pipeline: {orchestrator_path}")
        
        # Trigger Orchestrator (Non-blocking)
        subprocess.Popen(["python3", orchestrator_path], cwd=base_dir)
        
        return jsonify({
            "status": "success", 
            "message": "Pipeline triggered successfully",
            "active_script": "daily_orchestrator.py"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/finalize-sync', methods=['POST'])
def finalize_sync():
    # 1. Validate Secret Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {WEBHOOK_TOKEN}":
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # 2. Trigger Finalize Script (Non-blocking)
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        finalize_path = os.path.join(base_dir, "execution", "finalize_sync.py")
        
        print(f"🚀 [Webhook] Finalizing Sync: {finalize_path}")
        
        subprocess.Popen(["python3", finalize_path], cwd=base_dir)
        
        return jsonify({
            "status": "success", 
            "message": "Finalize sync triggered successfully",
            "active_script": "finalize_sync.py"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run on port 5000 by default
    print("--------------------------------------------------")
    print("🛰️  Japanese Restaurant Webhook Receiver is running!")
    print("Endpoint: POST http://localhost:5001/trigger-pipeline")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("--------------------------------------------------")
    app.run(host='0.0.0.0', port=5001)
