import os
from dotenv import load_dotenv

load_dotenv()

class StreamConfig:
    """Configuración del servidor de streaming."""

    PORT: int = int(os.getenv("STREAM_PORT", 8080))
    BIND_ADDRESS: str = os.getenv("STREAM_BIND", "0.0.0.0")
    BIN_CHANNEL: int = int(os.getenv("STREAM_BIN_CHANNEL"))
    HASH_LENGTH: int = int(os.getenv("STREAM_HASH_LENGTH", 6))
    CHUNK_SIZE: int = 1024 * 1024
    CACHE_SIZE: int = 128
    REQUEST_LIMIT: int = 5
    
    
    MAX_CACHE_BYTES: int = int(os.getenv("STREAM_MAX_CACHE_BYTES", 200 * 1024 * 1024))
    PREFETCH_COUNT: int = int(os.getenv("STREAM_PREFETCH_COUNT", 15))
    SLEEP_THRESHOLD: int = int(os.getenv("STREAM_SLEEP_THRESHOLD", 30))

    _url = os.getenv("STREAM_URL", "")
    URL = _url.rstrip("/") + "/" if _url else f"http://{BIND_ADDRESS}:{PORT}/"

    @classmethod
    def update_url(cls, new_url: str):
        """Actualiza la URL pública (usado por el túnel)."""
        cls.URL = new_url.rstrip("/") + "/"
