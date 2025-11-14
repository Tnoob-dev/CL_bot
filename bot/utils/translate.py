from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import gemini_srt_translator as gst
import os

class Translate():
    def __init__(self):
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY")
        self.gemini_api_key2: str = os.getenv("GEMINI_API_KEY2")
        
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
        
    async def srt_translate(self, target_lang: str, input_file: str, output_file: str):
        gst.gemini_api_key = self.gemini_api_key
        gst.gemini_api_key2 = self.gemini_api_key2
        gst.target_language = target_lang
        gst.input_file = input_file
        gst.output_file = output_file
        
        gst.translate()