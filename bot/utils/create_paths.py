from pathlib import Path

def create_translations_path() -> bool:
    path = Path.cwd() / Path("bot") / Path("translations")
    
    if not path.exists():
        path.mkdir()
    
    return True

def create_download_path() -> bool:    
    path = Path.cwd() / Path("bot") / Path("translations") / Path("downloads")
    
    if not path.exists():
        path.mkdir()
        
    return True

def create_user_path(path: str, user_id: int) -> bool:
    
    user_path = path / Path(str(user_id))
    
    if not user_path.exists():
        user_path.mkdir()
    
    return True

def create_output_path(user_id) -> bool:
    output_path = Path.cwd() / Path("bot") / Path("translations") / Path("output")
    
    if not output_path.exists():
        output_path.mkdir()
    
    create_user_path(output_path, user_id)
    
    return True