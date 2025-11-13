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

    user_id = query.from_user.id
    
    if query.data == 'order_ready':
        if check_administration(query):
                await client.send_message(chat_id="chat1080p", 
                                        text="Su pedido ha sido completado",
                                        reply_to_message_id=return_mesID())
                await query.message.delete()
        else:
            await query.answer(text="🤨", show_alert=True)
    else:
        main_path = Path.cwd() / Path("bot") / Path("translations")
        target_lang = query.data.split("_")[1]
        
        input_str =  main_path / Path("downloads") / Path(str(user_id)) / Path(return_filename().split("/")[-1])
        output_str = main_path / Path("output") / Path(str(user_id)) / Path(f"{target_lang.upper()}_{return_filename().split("/")[-1]}")
        
        translator = Translate()
        
        await query.message.delete()
        
        m = await query.message.reply(f"👨‍🔧Traduciendo ||__{return_filename().split("/")[-1]}__||, espere por favor, en cuanto termine tendra su subtitulo subido, mientras tanto, disfrute de nuestro canal 😉")
        
        await translator.srt_translate(target_lang, str(input_str), str(output_str))
        await query.message.reply_document(output_str, caption=f"✅Archivo traducido✅\nPara el usuario {query.from_user.mention} ({query.from_user.id})")
        
        await m.delete()
        
        download_files = os.listdir(main_path / Path("downloads") / Path(str(user_id)))
        output_files = os.listdir(main_path / Path("output") / Path(str(user_id)))
        
        for dl,ot in zip(download_files, output_files):
            os.remove(main_path / Path("downloads") / Path(str(user_id)) / dl)
            os.remove(main_path / Path("output") / Path(str(user_id)) / ot)
        
        os.rmdir(main_path / Path("downloads") / Path(str(user_id)))
        os.rmdir(main_path / Path("output") / Path(str(user_id)))