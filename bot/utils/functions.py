from pyrogram.client import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant, FloodWait
from typing import List, Dict
from pathlib import Path
from yarl import URL
from .create_paths import create_custom_path
from google import genai
import os
import asyncio
import json
import logging
import requests
import random


# Logger 
logger = logging.getLogger(__name__)

# check if a path or file exists
def check_existence(path: Path):
    return False if not path.exists() else True

# check if a user is admin
def check_administration(message: Message) -> bool:
    admins: List[str] = os.getenv("ADMINS").split(",")
    
    if str(message.from_user.id) not in admins:
        return False
    
    return True

# check if a user is in the channel
async def check_user_in_channel(client: Client, message: Message) -> bool:
    
    if not message.from_user:
        return False
    
    try:
        await client.get_chat_member(chat_id=os.getenv("CINEMA_ID"), user_id=message.from_user.id)
        # await client.get_chat_member(chat_id=os.getenv("ANIME_ID"), user_id=message.from_user.id)
        # await client.get_chat_member(chat_id=os.getenv("GAME_LIBRARY_ID"), user_id=message.from_user.id)
        # await client.get_chat_member(chat_id=os.getenv("EQUINOX_ID"), user_id=message.from_user.id)
        
        return True
    except UserNotParticipant:
        await message.reply_sticker(Path.cwd() / Path("assets") / Path("tongue_out.tgs"))
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
    # for loop into messaages to send all the file to backup channel
    for message_id in messages:
        success = False # Flag: if True, means file sent to backup channel succesfully
        
        # while loop...
        while not success:
            try:
                
                # forwarding
                await client.copy_message(chat_id=int(os.getenv("CHANNEL_ID")), from_chat_id=os.getenv("SENDER_BOT"), message_id=message_id)
                success = True # change flag to True and go for the next file
                
            except FloodWait as f: # if exists flood sleep bot the time estimated
                
                await asyncio.sleep(f.value)
                
def save_to_json(subtitles: List[Dict[str, int | str]], user_id: int, output_file: str):
    try:
        
        with open(f"./bot/translations/downloads/{user_id}/{output_file}", 'w', encoding='utf-8') as f:
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
        
def download_image(url: URL | str):
    create_custom_path("./images_downloaded")
    response = requests.get(url, stream=True)
    
    full_path = f"./images_downloaded/imagen.{url.split(".")[-1]}"
    
    with open(full_path, "wb") as file:
        for chunk in response.iter_content():
            file.write(chunk)
            
    return full_path

async def translate_synopsis(input_text: str):
    
    api_keys = os.getenv("GEMINI_API_KEY").split(",")
        
    single_api_key = random.choice(api_keys)
    
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
        async with genai.Client(api_key=single_api_key).aio as client:
            response = await client.models.generate_content(
                model="gemini-2.5-flash-preview-09-2025",
                contents={"text": prompt}
            )
            
            return response.text
    except Exception as e:
        logger.error(f"Error: {e}")

async def translate_title(title: str):
    
    api_keys = os.getenv("GEMINI_API_KEY").split(",")
        
    single_api_key = random.choice(api_keys)
    
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
        async with genai.Client(api_key=single_api_key).aio as client:
            response = await client.models.generate_content(
                model="gemini-2.5-flash-preview-09-2025",
                contents={"text": prompt}
            )
            
            return response.text
    except Exception as e:
        logger.error(f"Error: {e}")

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