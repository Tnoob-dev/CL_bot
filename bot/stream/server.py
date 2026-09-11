import logging
import mimetypes
import os
import time
from collections import defaultdict

from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine

from .config import StreamConfig
from .file_properties import get_short_hash, pack_file
from .streamer import PyrogramStreamer
from .web.html import create_html

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()

_streamer: PyrogramStreamer = None
_ongoing_requests: dict[str, int] = defaultdict(lambda: 0)
_SERVER_START_TIME = time.time()


def init_streamer(client):
    """Inicializa el streamer con el cliente de Pyrogram."""
    global _streamer
    _streamer = PyrogramStreamer(client)


def _get_requester_ip(request: web.Request) -> str:
    try:
        return request.headers["X-Forwarded-For"].split(", ")[0]
    except KeyError:
        peername = request.transport.get_extra_info("peername")
        if peername is not None:
            return peername[0]
        return "unknown"


def _allow_request(ip: str) -> bool:
    return _ongoing_requests[ip] < StreamConfig.REQUEST_LIMIT


def _get_readable_time(seconds: float) -> str:
    count = 0
    readable_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", " días"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        readable_time += time_list.pop() + ", "
    time_list.reverse()
    readable_time += ": ".join(time_list)
    return readable_time


def _parse_range_header(range_header, file_size: int):
    """Parsea el header Range de forma robusta, incluyendo rangos "sufijo"
    (bytes=-500) y valores malformados. Retorna (from_bytes, until_bytes) o
    lanza ValueError si el rango no se puede interpretar."""
    range_value = range_header.replace("bytes=", "").strip()

    if range_value.startswith("-"):
        # Rango sufijo: los últimos N bytes del archivo
        suffix_len = int(range_value[1:])
        from_bytes = max(file_size - suffix_len, 0)
        until_bytes = file_size - 1
        return from_bytes, until_bytes

    parts = range_value.split("-")
    from_bytes = int(parts[0])
    until_bytes = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
    return from_bytes, until_bytes


@routes.get("/status", allow_head=True)
async def status_handler(_: web.Request):
    return web.json_response(
        {
            "server_status": "running",
            "uptime": _get_readable_time(time.time() - _SERVER_START_TIME),
            "version": "1.0.0",
        }
    )


@routes.get(r"/watch/{messageID:\d+}", allow_head=True)
async def watch_handler(request: web.Request):
    """Muestra una página HTML con reproductor de video."""
    try:
        message_id = int(request.match_info["messageID"])
        secure_hash = request.rel_url.query.get("hash")

        file_info = await _streamer.get_file_properties(message_id)
        if not file_info:
            return web.Response(status=404, text="Archivo no encontrado")

        # Verificaciones antes del hash
        logger.info(
            "Nombre del archivo a stremear antes de crear hash: "
            + str(file_info.file_name)
        )
        logger.info(
            "Tamanho del archivo a stremear antes de crear hash: "
            + str(file_info.file_size)
        )
        logger.info(
            "MimeType del archivo a stremear antes de crear hash: "
            + str(file_info.mime_type)
        )
        logger.info(
            "Message ID del archivo a stremear antes de crear hash: "
            + str(file_info.message_id)
        )

        # Verificar hash
        full_hash = pack_file(
            file_info.file_name,
            file_info.file_size,
            file_info.mime_type,
            file_info.message_id,
        )

        logger.info("Full hash: " + full_hash)
        logger.info("Short Hash: " + get_short_hash(full_hash))
        logger.info("Secure hash: " + secure_hash)

        if get_short_hash(full_hash) != secure_hash:
            # patch por si todo explota
            # secure_hash = get_short_hash(full_hash)

            return web.HTTPForbidden(text="Hash inválido")

        stream_url = f"{StreamConfig.URL}stream/{message_id}?hash={secure_hash}"
        html = create_html(file_info, stream_url)

        return web.Response(text=html, content_type="text/html")

    except Exception as e:
        logger.error(f"Error en watch_handler: {e}")
        return web.Response(status=500, text="Error interno")


@routes.get(r"/stream/{messageID:\d+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        message_id = int(request.match_info["messageID"])
        secure_hash = request.rel_url.query.get("hash")
        logger.info(f"--- Recibida petición HTTP para /stream/{message_id} ---")

        return await media_streamer(request, message_id, secure_hash)

    except (
        AttributeError,
        BadStatusLine,
        ConnectionResetError,
        ConnectionAbortedError,
        ConnectionError,
    ):
        return web.Response(status=204)

    except Exception as e:
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text="Error interno del servidor")


async def media_streamer(request: web.Request, message_id: int, secure_hash: str):
    """Maneja el streaming de un archivo con soporte de Range requests."""
    head: bool = request.method == "HEAD"
    ip = _get_requester_ip(request)
    range_header = request.headers.get("Range", 0)

    if _streamer is None:
        return web.Response(status=503, text="Servidor de streaming no inicializado")

    logger.info(f"Petición de stream: ID={message_id} | IP={ip} | Range={range_header}")

    # Obtener propiedades del archivo
    file_info = await _streamer.get_file_properties(message_id)
    if not file_info:
        return web.Response(status=404, text="Archivo no encontrado")

    # Verificar hash
    full_hash = pack_file(
        file_info.file_name,
        file_info.file_size,
        file_info.mime_type,
        file_info.message_id,
    )
    if get_short_hash(full_hash) != secure_hash:
        logger.debug(f"Hash inválido para message_id {message_id}")
        return web.HTTPForbidden(text="Hash inválido")

    file_size = file_info.file_size

    if range_header:
        try:
            from_bytes, until_bytes = _parse_range_header(range_header, file_size)
        except (ValueError, IndexError):
            return web.Response(
                status=416,
                body="416: Range no válido",
                headers={"Content-Range": f"bytes */{file_size}"},
            )
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    until_bytes = min(until_bytes, file_size - 1)
    req_length = until_bytes - from_bytes + 1

    if not head:
        if not _allow_request(ip):
            return web.Response(status=429)
        _ongoing_requests[ip] += 1
        body = _streamer.download(file_info, file_size, from_bytes, until_bytes)
    else:
        body = None

    mime_type = file_info.mime_type
    file_name = file_info.file_name

    if not mime_type:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    disposition = "inline" if request.rel_url.query.get("s") else "attachment"

    ext = os.path.splitext(file_name.lower())[1]
    video_mimes = {
        ".mp4": "video/mp4",
        ".m4v": "video/x-m4v",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
    }

    if ext in video_mimes:
        mime_type = video_mimes[ext]
    elif mime_type and "video" in mime_type:
        mime_type = "video/mp4"

    headers = {
        "Content-Type": mime_type,
        "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
        "Content-Length": str(req_length),
        "Content-Disposition": f'{disposition}; filename="{file_name}"',
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Connection": "keep-alive",
        "Cache-Control": "public, max-age=3600",
    }

    response = web.StreamResponse(
        status=206 if range_header or request.http_range.start is not None else 200,
        reason="Partial Content" if range_header else "OK",
        headers=headers,
    )

    await response.prepare(request)

    try:
        if body:
            async for chunk in body:
                await response.write(chunk)
    except (ConnectionResetError, ConnectionAbortedError, ConnectionError):
        logger.info(f"Conexión cerrada por el cliente: {ip}")
    finally:
        _ongoing_requests[ip] -= 1

    return response


async def start_stream_server(client):
    """Inicia el servidor aiohttp de streaming."""
    init_streamer(client)

    app = web.Application(client_max_size=1024 * 8)
    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, StreamConfig.BIND_ADDRESS, StreamConfig.PORT).start()

    logger.info(f"Servidor de streaming iniciado en {StreamConfig.URL}")
    return runner
