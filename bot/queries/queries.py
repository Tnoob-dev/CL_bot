from entry.entry import bot
from commands.Order import return_mesID
from commands.Translations import return_filename
from pyrogram.client import Client
from pyrogram.types import Message, CallbackQuery
from utils.functions import check_administration
from utils.translate import Translate
from pathlib import Path
import os



@bot.on_callback_query()
async def query_manager(client: Client, query: CallbackQuery):

    if query.data == 'order_ready':
        if check_administration(query):
                await client.send_message(chat_id="chat1080p", 
                                        text="Su pedido ha sido completado",
                                        reply_to_message_id=return_mesID())
                await query.message.delete()
        else:
            await query.answer(text="🤨", show_alert=True)
    else:
        target_lang = query.data.split("_")[1]
        input_file = Path.cwd() / Path("bot") / Path("translations") / Path("downloads") / Path(str(query.from_user.id)) / Path(return_filename().split("/")[-1])
        
        output_file = Path.cwd() / Path("bot") / Path("translations") / Path("output") / Path(str(query.from_user.id)) / Path(f"{target_lang.upper()}_{return_filename().split("/")[-1]}")
        
        translator = Translate()
        await translator.srt_translate(target_lang, input_file, output_file)
        await query.message.delete()
        
        m = await query.message.reply(f"Traduciendo {return_filename().split("/")[-1]}, espere por favor, en cuanto termine tendra su subtitulo subido, mientras tanto, disfrute de nuestro canal 😉")
        
        await query.message.reply_document(output_file, caption=f"Archivo traducido para el usuario {query.from_user.mention} ({query.from_user.id})")
        
        await m.delete()
        
        os.remove(input_file)
        os.remove(output_file)