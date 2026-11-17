from workers import WorkerEntrypoint, Response
from pathlib import Path
from urllib.parse import urlparse

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)
        path = url.path.rstrip("/")

        # ১. Admin পেজ (/)
        if path in ("", "/"):
            admin_file = Path(__file__).parent / "templates" / "admin.html"
            return Response(
                admin_file.read_text(encoding="utf-8"),
                headers={"Content-Type": "text/html; charset=utf-8"}
            )

        # ২. Target পেজ (/target)
        if path == "/target":
            target_file = Path(__file__).parent / "templates" / "target.html"
            return Response(
                target_file.read_text(encoding="utf-8"),
                headers={"Content-Type": "text/html; charset=utf-8"}
            )

        # ৩. TTS API (/api/tts) - আপনার আগের worker.py থেকে
        if path == "/api/tts":
            # এখানে আপনার আগের TTS রিলে লজিক বসান
            return Response("TTS Endpoint", status=200)

        return Response("Not found", status=404)
