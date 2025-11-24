from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import gemini_srt_translator as gst
from translate.translate import Translator
from utils.process_srt_files import process_srt
import os
import random
import json


# Translate object
class Translate():
    def __init__(self):
        
        # Gemini api keys, this will be a list of str, cuz in the environment we will have a lot of api keys, separated by commas
        api_keys = os.getenv("GEMINI_API_KEY").split(",")
        
        api_key1 = random.choice(api_keys)
        
        api_key2 = random.choice(api_keys)
        
        self.gemini_api_key: str = api_key1
        self.gemini_api_key2: str = api_key2
    
    # show language queries
    def language_keyboard():
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🇪🇸 Español", callback_data="tr_es"),
                    InlineKeyboardButton("🇺🇸 English", callback_data="tr_en")
                ]
            ]
        )
        return keyboard
    
    # translate srt via ai
    async def ai_srt_translate(self, target_lang: str, input_file: str, output_file: str):
        gst.gemini_api_key = self.gemini_api_key
        gst.gemini_api_key2 = self.gemini_api_key2
        gst.target_language = target_lang
        gst.input_file = input_file
        gst.output_file = output_file
        
        gst.translate()
        
    # translate srt via google translate
    async def google_srt_translate(self, target_lang: str, input_file: str, user_id: int, output_file: str):
        google_translator = Translator(to_lang=target_lang)
        
        await process_srt(input_file, user_id)