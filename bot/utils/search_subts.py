import logging
import os
import random

from opensubtitlescom import OpenSubtitles, OpenSubtitlesException

# Logger
logger = logging.getLogger(__name__)


def subs(query: str, lang: str) -> list | None:

    global op

    api_keys = os.getenv("OPENSUBTITLES_KEYS").split(",")
    username = os.getenv("OPENSUBTITLE_USERNAME")
    password = os.getenv("OPENSUBTITLE_PASSWORD")

    try:
        op = OpenSubtitles("TitiLM10 XDDD v0.0.1", api_key=random.choice(api_keys))

        op.login(username, password)

        response = op.search(query=query, languages=lang)

        if len(response.data) > 0:
            response.data.pop(0)
    except OpenSubtitlesException:
        logger.exception("Error en la busqueda de subtitulos")
    else:
        return response.data

    return None


def download_subs(file_id: str) -> str:

    try:
        file = op.download_and_save(file_id)
    except OpenSubtitlesException:
        logger.exception("Error en la busqueda de subtitulos")
    else:
        return file