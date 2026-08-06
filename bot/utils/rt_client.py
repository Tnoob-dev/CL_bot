import aiohttp
import asyncio
import logging

from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"

URL = "https://www.rottentomatoes.com"
SEARCH_PATH = "/search"
TIMEOUT = aiohttp.ClientTimeout(total=10)

headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": USER_AGENT,
    }

async def find_first_movie_link(soup: BeautifulSoup) -> Optional[str]:
    
    movie_link = soup.select_one(
        "a[data-qa='info-name']"
    )
    
    if not movie_link:
        movie_link = soup.find("a", attrs={"class": "unset", "slot": "title", "data-qa": "info-name"})
        
    if not movie_link:
        logger.error("No se encontro movie_link")
        return 
    
    href = movie_link.get("href")
    
    if not href or not isinstance(href, str):
        logger.error("Error: href no es un str")
        return
    
    return href

async def search_movie(session: aiohttp.ClientSession, query: str) -> Optional[str]:
    
    url = f"{URL}{SEARCH_PATH}"
    params = {"search": query}
    
    try:
        async with session.get(url=url, params=params, headers=headers, timeout=TIMEOUT) as response:
            response.raise_for_status()
            html = await response.text(encoding="utf-8")
    except (aiohttp.ClientError, asyncio.TimeoutError):
        logger.error("error al buscar la pelicula")
        return
    
    soup = BeautifulSoup(html, "html.parser")
    
    return await find_first_movie_link(soup=soup)

async def find_scorecard(soup: BeautifulSoup) -> Optional[dict[str, dict]]:
    
    score_info = {}
    
    media_scorecard = soup.select_one(
        "div[class='media-scorecard']"
    )
    
    if not media_scorecard:
        media_scorecard = soup.find("div", attrs= {"class": "media-scorecard"})
        
    if not media_scorecard:
        logger.error("Error no se encontro scorecard")
        return {}
    
    rt_critics_percentage = media_scorecard.select_one(
        "rt-text[slot='critics-score']"
    )
    
    if not rt_critics_percentage:
        rt_critics_percentage.find_next("rt-text", {"slot": "critics-score"})
    
    
    rt_critics_reviews = media_scorecard.select_one(
        "rt-link[slot='critics-reviews']"
    )
    
    if not rt_critics_reviews:
        rt_critics_reviews = media_scorecard.find_next("rt-link", attrs={"slot": "critics-reviews"})
    
    rt_critics_reviews_count = rt_critics_reviews.text.replace("Reviews", "").strip().replace(",", "")
    rt_critics_reviews_link = f"{URL}{rt_critics_reviews.get('href')}"
    
    score_info["tomatoes"] = {"percentage": rt_critics_percentage.text.strip(), "reviews": rt_critics_reviews_count, "reviews_link": rt_critics_reviews_link}
    
    rt_auience_percentage = media_scorecard.select_one(
        "rt-text[slot='audience-score']"
    )
    
    if not rt_auience_percentage:
        rt_auience_percentage = media_scorecard.find_next("rt-text", {"slot": "audience-score"})
        
    rt_audience_reviews = media_scorecard.select_one(
        "rt-link[slot='audience-reviews']"
    )
    
    if not rt_audience_reviews:
        rt_audience_reviews = media_scorecard.find_next("rt-link", {"slot": "audience-reviews"})
    
    rt_audience_reviews_count = rt_audience_reviews.text.replace("+ Verified Ratings", "").replace("+ Ratings", "").strip().replace(",", "")
    rt_audience_reviews_links = f"{URL}{rt_audience_reviews.get("href")}"
    
    score_info["audience"] = {"percentage": rt_auience_percentage.text.strip(), "reviews": rt_audience_reviews_count, "reviews_links": rt_audience_reviews_links}
        
    return score_info
    
async def init_scorecard_search(session: aiohttp.ClientSession, link: str) -> Optional[dict[str, dict]]:
    
    try:
        async with session.get(url=link, headers=headers, timeout=TIMEOUT) as response:
            response.raise_for_status()
            html = await response.text(encoding="utf-8")
    except (aiohttp.ClientError, asyncio.TimeoutError):
        logger.error("Error al obtener la pagina de la pelicula/serie")
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    return await find_scorecard(soup=soup)





##############################
############ MAIN ############
##############################
async def info(search: str):
    
    async with aiohttp.ClientSession() as session:
        link = await search_movie(session=session, query=search)
        if link:
            score_info = await init_scorecard_search(session=session, link=link)
            return score_info
        else:
            logger.error("No se encontro la pelicula/serie")
            return None