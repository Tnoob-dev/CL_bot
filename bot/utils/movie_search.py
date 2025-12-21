from aiohttp.client_exceptions import ClientError, ClientConnectionError, ConnectionTimeoutError
from aiohttp.http_exceptions import HttpBadRequest
import aiohttp, os, logging

logger = logging.getLogger(__name__)

async def get_results(query: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{os.getenv("IMDB_API_URL")}/search/titles?query={query}&limit=5") as response:
                titles = await response.json()
                
                if not titles.get("titles"):
                    return []
                
                results = []
                
                for title in titles.get("titles"):
                    title_id = title.get("id")
                
                    async with session.get(f"{os.getenv("IMDB_API_URL")}/titles/{title_id}") as response:
                        results.append(
                            await response.json()
                        )
        
        return results
    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest) as error:
        logger.error(error)