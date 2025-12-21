from pathlib import Path
import logging

# Logger 
logger = logging.getLogger(__name__)

##################
# PATH CREATIONS #
##################

# bot/translations
def create_translations_path() -> bool:
    logger.info("Creando carpeta de traducciones")
    path = Path.cwd() / Path("bot") / Path("translations")
    
    if not path.exists():
        path.mkdir()
    
    logger.info("Carpeta de traducciones creada")
    return True

# bot/translations/downloads
def create_download_path() -> bool:    
    logger.info("Creando carpeta de descargas")
    path = Path.cwd() / Path("bot") / Path("translations") / Path("downloads")
    
    if not path.exists():
        path.mkdir()
    
    logger.info("Carpeta de descargas creada")
    return True

# bot/translations/downloads/{user_id}
def create_user_path(path: str, user_id: int) -> bool:
    logger.info(f"Creando carpeta de traducciones (download) para el usuario {user_id}")
    user_path = path / Path(str(user_id))
    
    if not user_path.exists():
        user_path.mkdir()
    
    logger.info(f"Carpeta de traducciones (download) para el usuario {user_id} creada")
    return True

# bot/translations/output/{user_id}
def create_output_path(user_id: int) -> bool:
    logger.info(f"Creando carpeta de traducciones (output) para el usuario {user_id}")
    output_path = Path.cwd() / Path("bot") / Path("translations") / Path("output")
    
    if not output_path.exists():
        output_path.mkdir()
    
    create_user_path(output_path, user_id)
    
    logger.info(f"Carpeta de traducciones (output) para el usuario {user_id} creada")
    return True

# bot/subts/{user_id}
def create_subtitles_dl_path(user_id: int):
    logger.info(f"Creando carpeta de busqueda de subtitulos para el usuario {user_id}")
    output_path = Path.cwd() / Path("bot") / Path("subts")
    
    if not output_path.exists():
        output_path.mkdir()
    
    create_user_path(output_path, user_id)
    
    logger.info(f"Carpeta de busqueda de subtitulos para el usuario {user_id} creada")
    return True

# custpom path
def create_custom_path(path: str):
    custom_path = Path(path)
    if not custom_path.exists():
        custom_path.mkdir()
        
    logger.info(f"Carpeta custom {path} creada")