# Cloudflare Workers Python entrypoint.
# Flask/eventlet/gunicorn cannot run in the Workers Python runtime (Pyodide),
# so this is a thin rewrite using only the Workers Web APIs.
#
# Original app.py was just: serve admin.html + target.html, relay Socket.IO
# client-data (lat/lng) to connected clients. This reproduces that.

from urllib.parse import urlparse, parse_qs
import json


def _read_template(name):
    """Bundled HTML modules live under /session/metadata in the runtime."""
    for path in (
        f"/session/metadata/templates/{name}",
        f"templates/{name}",
        name,
    ):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()
        except (FileNotFoundError, OSError):
            continue
    return f"<h1>Template not found</h1><p>{name}</p>"


# In-memory set of connected websockets (fine for light traffic;
# for production multi-region use, move this into a Durable Object).
_connected = set()


async def _handle_ws(request):
    ws = new_websocket_pair()
    server = ws[0]
    client = ws[1]
    _connected.add(client)

    try:
        await server.accept()
        async for msg in server:
            try:
                data = json.loads(msg)
            except Exception:
                continue
            # Relay to every connected client (mirrors original 'update-clients' broadcast)
            payload = json.dumps(data)
            for peer in list(_connected):
                try:
                    await peer.send(payload)
                except Exception:
                    _connected.discard(peer)
    except Exception:
        pass
    finally:
        _connected.discard(client)

    return client.response


async def fetch(request):
    url = urlparse(request.url)
    path = url.path.rstrip("/")

    # WebSocket upgrade for the Socket.IO client-data relay
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await _handle_ws(request)

    if path in ("", "/"):
        return Response(_read_template("admin.html"),
                        headers={"Content-Type": "text/html; charset=utf-8"})

    if path == "/target":
        return Response(_read_template("target.html"),
                        headers={"Content-Type": "text/html; charset=utf-8"})

    # Proxy endpoint: forward text to the Edge TTS service and stream audio back.
    # (The original app called edge-tts; this keeps the same contract.)
    if path == "/api/tts":
        text = ""
        if request.method == "POST":
            body = await request.text()
            text = parse_qs(body).get("text", [""])[0]
        else:
            text = parse_qs(url.query).get("text", [""])[0]
        if not text:
            return Response("Missing text", status=400)

        try:
            upstream = await fetch(
                "https://speech.platform.bing.com/tts/cognitiveservices/v1",
                {
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Mozilla/5.0 (compatible; bangla-tts)",
                    },
                    "body": f"text={text}",
                },
            )
        except Exception as exc:
            return Response(json.dumps({"error": str(exc)}), status=502,
                            headers={"Content-Type": "application/json"})

        if not upstream.ok:
            return Response(json.dumps({"error": f"upstream {upstream.status}"}),
                            status=upstream.status,
                            headers={"Content-Type": "application/json"})
        audio = await upstream.arrayBuffer()
        return Response(audio, {
            "status": 200,
            "headers": {
                "Content-Type": "audio/mpeg",
                "Content-Length": str(audio.byteLength),
                "Cache-Control": "public, max-age=86400",
            },
        })

    return Response("Not found", status=404)


export_default = {"fetch": fetch}
