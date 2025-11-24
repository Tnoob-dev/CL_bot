from pathlib import Path
from utils.functions import save_to_json

async def process_srt(file_path: str, user_id: int) -> None:
    
    with open(file_path, mode="r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        blocks = content.strip().split("\n\n")
        subtitles = []
        
        for block in blocks:
            lines = block.split("\n")
            if len(lines) >= 3:
                subtitle = {
                    'sequence': int(lines[0]),
                    'timestamp': lines[1],
                    'text': '\n'.join(lines[2:]),
                    'translated_text': ''
                }
                
                subtitles.append(subtitle)
                
        save_to_json(subtitles, user_id, file_path.split("/")[-1])
    except Exception as error:
        print(f"Ha ocurrido el siguiente error mientras se procesaba el subtitulo: -> {error}")            

