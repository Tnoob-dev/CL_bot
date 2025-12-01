from pathlib import Path

##################
# PATH CREATIONS #
##################

# bot/translations
def create_translations_path() -> bool:
    path = Path.cwd() / Path("bot") / Path("translations")
    
    if not path.exists():
        path.mkdir()
    
    return True

# bot/translations/downloads
def create_download_path() -> bool:    
    path = Path.cwd() / Path("bot") / Path("translations") / Path("downloads")
    
    if not path.exists():
        path.mkdir()
        
    return True

# bot/translations/downloads/{user_id}
def create_user_path(path: str, user_id: int) -> bool:
    
    user_path = path / Path(str(user_id))
    
    if not user_path.exists():
        user_path.mkdir()
    
    return True

# bot/translations/output/{user_id}
def create_output_path(user_id: int) -> bool:
    output_path = Path.cwd() / Path("bot") / Path("translations") / Path("output")
    
    if not output_path.exists():
        output_path.mkdir()
    
    create_user_path(output_path, user_id)
    
    return True

# bot/subts/{user_id}
def create_subtitles_dl_path(user_id: int):
    output_path = Path.cwd() / Path("bot") / Path("subts")
    
    if not output_path.exists():
        output_path.mkdir()
    
    create_user_path(output_path, user_id)
    
    return True