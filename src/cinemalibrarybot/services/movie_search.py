from aiohttp.client_exceptions import ClientError, ClientConnectionError, ConnectionTimeoutError
from aiohttp.http_exceptions import HttpBadRequest
import aiohttp, json, logging

from cinemalibrarybot.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Offline mock
#
# The external movie-info boundary is these two functions. When MOCK_MOVIE_DATA
# is enabled (or no IMDB_API_URL is configured) they serve data from a local
# JSON fixture instead of calling the API, so /info works fully offline. The
# fixture is FIXTURES_DIR/titles.json: an object mapping title id -> title dict
# in the same shape the real API returns.
# ---------------------------------------------------------------------------
def _use_mock() -> bool:
    return settings.MOCK_MOVIE_DATA or not settings.IMDB_API_URL


def _load_fixture_titles() -> dict:
    path = settings.FIXTURES_DIR / "titles.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Mock movie fixture not found at %s", path)
        return {}
    except json.JSONDecodeError as error:
        logger.error("Invalid mock movie fixture %s -> %s", path, error)
        return {}


async def _mock_get_results(query: str):
    titles = list(_load_fixture_titles().values())
    q = (query or "").strip().lower()
    if q:
        filtered = [t for t in titles if q in str(t.get("primaryTitle", "")).lower()]
        titles = filtered or titles
    return titles[:5]


async def _mock_get_info_by_id(movieId: str):
    return _load_fixture_titles().get(movieId)


async def get_results(query: str):
    if _use_mock():
        return await _mock_get_results(query)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.IMDB_API_URL}/search/titles?query={query}&limit=5") as response:
                titles = await response.json()

                if not titles.get("titles"):
                    return []

                results = []

                for title in titles.get("titles"):
                    title_id = title.get("id")

                    async with session.get(f"{settings.IMDB_API_URL}/titles/{title_id}") as response:
                        results.append(
                            await response.json()
                        )

        return results
    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest) as error:
        logger.error(error)


async def get_info_by_id(movieId: str):
    if _use_mock():
        return await _mock_get_info_by_id(movieId)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.IMDB_API_URL}/titles/{movieId}") as response:
                movie = await response.json()

                if not movie.get("id"):
                    return None

                return movie

    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest) as error:
        logger.error(error)
