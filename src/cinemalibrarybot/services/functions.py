from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, User
from pyrogram.errors import UserNotParticipant, FloodWait
from typing import List, Dict
from pathlib import Path
from cinemalibrarybot.repositories.db_reqs import get_user, insert
from groq import AsyncGroq
from deep_translator import GoogleTranslator
from cinemalibrarybot.stream.config import StreamConfig
from cinemalibrarybot.stream.file_properties import get_file_info, pack_file, get_short_hash
from cinemalibrarybot.repositories.create_cine_db import Game
from cinemalibrarybot.config import settings
import os
import asyncio
import json
import logging
import aiohttp
import time

# Logger 
logger = logging.getLogger(__name__)

# check if a path or file exists
def check_existence(path: Path):
    return False if not path.exists() else True

# check if a user is admin
def check_administration(message: Message) -> bool:
    
    user_id = message.from_user.id
    
    _, user = get_user(user_id, all_the_users=False)
    
    if not user.is_admin:
        return False

    return True

# check if a user is in the channel
async def check_user_in_channel(client: Client, message: Message) -> bool:
    
    if not message.from_user:
        return False
    
    try:
        await client.get_chat_member(chat_id=os.getenv("CINEMA_ID"), user_id=message.from_user.id)

        return True
    except UserNotParticipant:
        await message.reply_sticker(settings.ASSETS_DIR / "tongue_out.tgs")
        await message.reply("Para usar este bot, primero debes unirte a nuestros canales.", 
                            reply_markup=InlineKeyboardMarkup(
                                [
                                    [InlineKeyboardButton("🎬Cinema Library🎬", url=f"https://t.me/{os.getenv("CINEMA_ID")}")]
                                ]
                            ))
        return False
    except Exception as e:
        logger.error(f"Error inesperado en check_user_in_channel: {e}")
        return False

async def forward_messages(client: Client, messages: List[int]):
    new_ids = []  

    for message_id in messages:
        success = False  # Flag: if True, means file sent to backup channel succesfully
        # while loop...
        while not success:
            try:
                # forwarding
                copied = await client.copy_message(
                    chat_id=int(os.getenv("CHANNEL_ID")),
                    from_chat_id=os.getenv("SENDER_BOT"),
                    message_id=message_id
                )
                new_ids.append(copied.id)  
                success = True  # change flag to True and go for the next file
            except FloodWait as f:  # if exists flood sleep bot the time estimated
                await asyncio.sleep(f.value)
    
    return new_ids


import random
random_num = random.randint(0, 89)

def build_season_link(last_message_id: int) -> str:
    name = f"chn_{last_message_id}_{random_num}"
    return f"https://t.me/{os.getenv('SENDER_BOT')}?start={name}"

def register_movie(messages: List[int]) -> str:
    
    last_id = messages[-1]
    
    name = f"chn_{last_id}_{random_num}"
    insert(Game(name=name, file_ids=messages))
    return build_season_link(last_id)

def save_to_json(subtitles: List[Dict[str, int | str]], user_id: int, output_file: str):
    try:
        out_dir = settings.translations_dir / "downloads" / str(user_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / output_file, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=2)
            
    except Exception as error:
        logger.error(f"Error guardando el json -> {error}")
        
def clear_path(path: str) -> None:
    
    if os.path.exists(path):
        files = os.listdir(path)
        
        if len(files) > 0:
            for file in files:
                os.remove(path + file)

def get_clicked_button_text(query: CallbackQuery):
    key = query.data
    
    for markup in query.message.reply_markup.inline_keyboard:
        if markup[0].callback_data == key:
            return markup[0].text
        
async def download_image(url: str):
    os.makedirs("./images_downloaded", exist_ok=True)
    ext = str(url).split(".")[-1].split("?")[0]
    full_path = f"./images_downloaded/imagen.{ext}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            with open(full_path, "wb") as file:
                async for chunk in response.content:
                    file.write(chunk)
    return full_path

async def download_tg_files(client: Client, file_id: str, username: str):
    os.makedirs("./images_downloaded", exist_ok=True)
    full_path = await client.download_media(file_id, file_name=f"./images_downloaded/{username}.jpg")
    
    return full_path

async def translate_synopsis(input_text: str):
    client = AsyncGroq(api_key=os.getenv("GROQ_KEY"))
    
    prompt = f"""
Por favor, traduce la siguiente sinopsis de película o serie del inglés al español. Sigue estas instrucciones al pie de la letra:

1.  **Traducción Fiel:** Traduce el texto de manera precisa, conservando el significado original, el tono (dramático, cómico, suspense) y todos los detalles de la trama.
2.  **Sin Adiciones:** No añadas información que no esté en el texto original (como nombres de actores, director, año de estreno, críticas o tu opinión).
3.  **Sin Omisiones:** No omitas frases, personajes o elementos clave de la trama.
4.  **Estilo Natural:** El español debe sonar natural y fluido, como el texto de una sinopsis profesional. Usa términos comunes para el género (ej: "thriller de suspense", "comedia dramática").
5.  **Nombres Propios:** No traduzcas títulos de películas/series o nombres de personajes, a menos que ya exista una traducción oficial ampliamente conocida (ej: "Frozen" -> "Frozen: Una aventura congelada"). Los nombres de lugares o instituciones sí se traducen.
6.  **Formato:** Devuelve **solo** la traducción limpia, sin prefacios como "Aquí tienes la traducción:" ni comentarios finales.

**Texto a traducir:**
{input_text}
"""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error: {e}")

async def translate_title(title: str):
    client = AsyncGroq(api_key=os.getenv("GROQ_KEY"))
    
    prompt = f"""
Actúa como un traductor especializado en localización cinematográfica. Tu tarea es traducir o adaptar al español **SOLO** el título principal que te proporcione, aplicando esta jerarquía de reglas de manera estricta:

1.  **Prioridad Máxima: Título Oficial en Español.**
    *   Si existe un título oficial de distribución en español ampliamente conocido y verificado (ej: "The Shawshank Redemption" -> "Cadena Perpetua", "Frozen" -> "Frozen: Una aventura congelada"), **DEBES usarlo**. No propongas alternativas.

2.  **Traducción Literal o Adaptada (Solo si no aplica la regla 1).**
    *   Si NO hay un título oficial conocido, decide:
        *   **Traducir literalmente** si es claro y funciona en español (ej: "The Social Network" -> "La red social").
        *   **Adaptar** si una traducción literal suena mal o no tiene sentido. Busca un equivalente natural que capture la esencia (ej: "The Hangover" -> "¿Qué pasó ayer?").

3.  **Conservar el Original (Casos excepcionales).**
    *   **NO traduzcas** y conserva el título original en inglés (o en su idioma) si:
        *   Es un nombre propio (de personaje, lugar, marca: "Saw", "Shrek", "Gotham").
        *   Es una palabra inventada o sin traducción directa ("Inception", "Se7en").
        *   El título ya es una palabra internacionalmente reconocida o un lema ("Avatar", "Matrix", "The Avengers").
        *   El título **YA está en español** (ej: "Coco", "Roma", "El laberinto del fauno"). Déjalo exactamente igual.

**Formato de Respuesta:**
*   Devuelve **únicamente** el título resultante (ya sea traducido, adaptado o el original), sin comillas, sin explicaciones, sin listas de opciones.
*   No añadas "La película" o "La serie".
*   Si el título original contiene un artículo en inglés ("The", "A"), omítelo en la traducción a menos que sea gramaticalmente esencial en español (ej: "The Godfather" -> "El Padrino").

**Título a procesar:**
{title}
"""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error: {e}")

def translate_words(words: List[str], target_lang: str = "es") -> List[str]:
    translator = GoogleTranslator(source="auto", target=target_lang)

    results = [translator.translate(word) for word in words]

    return results

def clean_name(text: str):
    
    splitted_text = text.split("\n")
    title = splitted_text[0]
    special_chars = ["🎬", "🎭"]
    
    
    if special_chars[0] in title:
        title = title.replace(special_chars[0], "")
        return title.strip()
    
    elif special_chars[1] in title:
        title = title.replace(special_chars[1], "")
        return title.strip()
    
    return title

async def get_message_info(client: Client, message_id: int | List[int]) -> Message | List[Message]:
    
    message_info = await client.get_messages(
                    chat_id=os.getenv("CINEMA_ID"),
                    message_ids=int(message_id)
                )
    
    return message_info

async def get_profile_info(client: Client, user_id: int) -> User:
    
    profile_info = await client.get_users(user_id)
    
    return profile_info

async def delete_after_delay(client: Client, chat_id: int, message_id: int, delay: int = 180):

    try:
        await asyncio.sleep(delay)
        await client.delete_messages(chat_id, message_id)
        logger.info(f"Mensaje {message_id} eliminado del chat {chat_id} tras {delay}s")
    except Exception as e:
        logger.error(f"No se pudo eliminar el mensaje {message_id} en el chat {chat_id}: {e}")


async def generate_stream_link(target_message: Message) -> List[List[InlineKeyboardButton]]:
    file_info = get_file_info(target_message)
    
    full_hash = pack_file(
        file_info.file_name,
        file_info.file_size,
        file_info.mime_type,
        file_info.message_id
    )
    
    file_hash = get_short_hash(full_hash)
    stream_link = f"{StreamConfig.URL}stream/{target_message.id}?hash={file_hash}"

    
    # link 
    watch_link = f"{StreamConfig.URL}watch/{target_message.id}?hash={file_hash}"
    
    buttons = [
        [InlineKeyboardButton("Ver en navegador", url=watch_link)],
        [InlineKeyboardButton("Ver en Reproductor", url=stream_link)]
    ]
    
    return buttons

def gen_ids(id1: int, id2: int = None) -> List[int]:
    
    if id2 is None:
        return [id1]
    
    start, end = min(id1, id2), max(id1, id2)
    return list(range(start, end + 1))