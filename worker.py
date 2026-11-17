from workers import WorkerEntrypoint, Response
from pathlib import Path
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

        # API রুট (আগের মতোই)
        if path == "/api/update" and request.method == "POST":
            # ... (আপনার আগের API লজিক)
            pass

        if path == "/api/clients" and request.method == "GET":
            # ... (আপনার আগের API লজিক)
            pass

        if path == "/api/command" and request.method == "POST":
            # ... (আপনার আগের API লজিক)
            pass

        if request.method == "OPTIONS":
            return Response("", headers=cors_headers)

        # HTML এবং PWA ফাইল সার্ভ করা (Path ভিত্তিক)
        if path in ("", "/"):
            admin_file = Path(__file__).parent / "templates" / "admin.html"
            return Response(admin_file.read_text(encoding="utf-8"), headers={"Content-Type": "text/html; charset=utf-8"})
        
        if path == "/target":
            target_file = Path(__file__).parent / "templates" / "target.html"
            return Response(target_file.read_text(encoding="utf-8"), headers={"Content-Type": "text/html; charset=utf-8"})
        
        if path == "/manifest.json":
            manifest_file = Path(__file__).parent / "templates" / "manifest.json"
            return Response(manifest_file.read_text(encoding="utf-8"), headers={"Content-Type": "application/json"})
        
        if path == "/service-worker.js":
            sw_file = Path(__file__).parent / "templates" / "service-worker.js"
            return Response(sw_file.read_text(encoding="utf-8"), headers={"Content-Type": "application/javascript"})

        return Response("Not Found", status=404)
