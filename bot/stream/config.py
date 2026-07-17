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

    # --- Estabilidad ante mala conexión / errores de Telegram ---
    # Reintentos con backoff exponencial para cada chunk pedido a Telegram.
    MAX_TELEGRAM_RETRIES: int = int(os.getenv("STREAM_MAX_RETRIES", 4))
    RETRY_BASE_DELAY: float = float(os.getenv("STREAM_RETRY_DELAY", 1.0))
    # Máximo de descargas simultáneas contra los DC de Telegram (evita FLOOD_WAIT
    # cuando el stream principal + varios prefetch piden chunks a la vez).
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("STREAM_MAX_CONCURRENT_DOWNLOADS", 8))

    # --- Calidades (limitación de velocidad, NO transcodifica el video real) ---
    # Los valores son bytes/segundo objetivo. "auto"/"high" no aplican techo
    # adicional (usan el ritmo real del video). El resto limita el envío para
    # ahorrar datos / reducir cortes en conexiones malas.
    QUALITY_LABELS = {
        "auto": "Automática",
        "high": "Alta (original)",
        "medium": "Media (~1.5 Mbps)",
        "low": "Baja (~700 Kbps)",
        "data_saver": "Ahorro de datos (~350 Kbps)",
    }
    QUALITY_CAPS_BYTES_PER_SEC = {
        "auto": None,
        "high": None,
        "medium": int(1500 * 1024 / 8),
        "low": int(700 * 1024 / 8),
        "data_saver": int(350 * 1024 / 8),
    }
    DEFAULT_QUALITY: str = "auto"

    _url = os.getenv("STREAM_URL", "")
    URL = _url.rstrip("/") + "/" if _url else f"http://{BIND_ADDRESS}:{PORT}/"

    @classmethod
    def update_url(cls, new_url: str):
        """Actualiza la URL pública (usado por el túnel)."""
        cls.URL = new_url.rstrip("/") + "/"