from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import gemini_srt_translator as gst
import os
import random
import logging

# Logger 
logger = logging.getLogger(__name__)

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