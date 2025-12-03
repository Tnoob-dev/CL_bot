from opensubtitlescom import OpenSubtitles, OpenSubtitlesException
import random
import os
import logging

# Logger 
logger = logging.getLogger(__name__)

def subs(query: str):
    
    global op
    
    api_keys = os.getenv("OPENSUBTITLES_KEYS").split(",")
    username = os.getenv("OPENSUBTITLE_USERNAME")
    password = os.getenv("OPENSUBTITLE_PASSWORD")

    op = OpenSubtitles("TitiLM10 XDDD v0.0.1", api_key=random.choice(api_keys))

    op.login(username, password)

    response = op.search(query=query, languages="es")

    if len(response.data) > 0:
        response.data.pop(0)
    
        return response.data
    
    return None

def download_subs(file_id: str):
    
    try:
        file = op.download_and_save(file_id)
        return file
    except OpenSubtitlesException as error:
        logger.error(f"Error -> {error}")