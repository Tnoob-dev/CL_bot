import logging
import os
from typing import Any

import aiohttp
from aiohttp.client_exceptions import (
    ClientConnectionError,
    ClientError,
    ConnectionTimeoutError,
)
from aiohttp.http_exceptions import HttpBadRequest

logger = logging.getLogger(__name__)

##### IMDB

async def get_results(query: str) -> list | None:
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(f"{os.getenv("IMDB_API_URL")}/search/titles?query={query}&limit=5") as response
        ):
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
    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest):
        logger.exception("Error del Cliente")
    else:
        return results
    
async def get_info_by_id(movieId: str) -> Any | None:
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(f"{os.getenv("IMDB_API_URL")}/titles/{movieId}") as response
        ):
                movie = await response.json()

                if not movie.get("id"):
                    return None

                return movie

    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest):
        logger.exception("Error del Cliente")


##### IMDB


async def search_tmdb(query: str):
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.getenv("TMDB_API_KEY")}"
        }
        
        async with (
            aiohttp.ClientSession() as session,
            session.get(f"{os.getenv("TMDB_API_URL")}/search/multi?query={query}&include_adult=false&language=en-US&page=1", headers=headers) as response
        ): 
            
            results = dict(await response.json()).get("results")
            
            return results
    
    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest):
        logger.exception("Error del Cliente")
        
async def get_movie_info_by_id_tmdb(movieId: str):
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.getenv("TMDB_API_KEY")}"
        }
        
        async with (
            aiohttp.ClientSession() as session,
            session.get(f"{os.getenv("TMDB_API_URL")}/movie/{movieId}?language=en-US", headers=headers) as response
        ):
            
            result = dict(await response.json())
            
            return result
            
    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest):
        logger.exception("Error del cliente")

async def get_tv_info_by_id_tmdb(seriesId: str):
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.getenv("TMDB_API_KEY")}"
        }
        
        async with (
            aiohttp.ClientSession() as session,
            session.get(f"{os.getenv("TMDB_API_URL")}/tv/{seriesId}?language=en-US", headers=headers) as response
        ):
            
            result = dict(await response.json())
            
            return result
            
    except (ClientError, ClientConnectionError, ConnectionTimeoutError, HttpBadRequest):
        logger.exception("Error del Cliente")