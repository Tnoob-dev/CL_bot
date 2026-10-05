import logging
from pathlib import Path

# Logger
logger = logging.getLogger(__name__)

# bot/{path}/{user_id}
def create_user_path(path: str, user_id: int) -> bool:
    logger.info("Creando carpeta para el usuario %s", user_id)
    user_path = path / Path(str(user_id))

    if not user_path.exists():
        user_path.mkdir()

    logger.info("Carpeta para el usuario %s creada", user_id)
    return True


# bot/subts/{user_id}
def create_subtitles_dl_path(user_id: int):
    logger.info("Creando carpeta de busqueda de subtitulos para el usuario %s", user_id)
    output_path = Path.cwd() / Path("bot") / Path("subts")

    if not output_path.exists():
        output_path.mkdir()

    create_user_path(output_path, user_id)

    logger.info("Carpeta de busqueda de subtitulos para el usuario %s creada", user_id)
    return True


# custpom path
def create_custom_path(path: str):
    custom_path = Path(path)
    if not custom_path.exists():
        custom_path.mkdir()

    logger.info("Carpeta custom %s creada", path)
