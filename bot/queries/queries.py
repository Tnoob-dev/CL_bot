from entry.entry import bot
from commands.Order import return_mesID
from commands.Translations import return_filename
from utils.db_reqs import get_user, update_user_value
from pyrogram.client import Client
from pyrogram.types import CallbackQuery
from utils.functions import check_administration, get_clicked_button_text
from utils.users_translate import Translate
from utils.search_subts import download_subs
from utils.create_paths import create_subtitles_dl_path
from pathlib import Path
import os
import logging

# Logger 
logger = logging.getLogger(__name__)

# callback query for query actions

@bot.on_callback_query()
async def query_manager(client: Client, query: CallbackQuery):

    # get user id, username, and check if user is in db
    user_id = query.from_user.id
    user_founded = get_user(user_id)
    
    # query for orders
    if query.data == 'order_ready':
        if check_administration(query):
                await client.send_message(chat_id="chat1080p", 
                                        text="Su pedido ha sido completado",
                                        reply_to_message_id=return_mesID())
                await query.message.delete()
        else:
            await query.answer(text="🤨", show_alert=True)
    elif query.data.startswith("sub_"):
        try:
            if user_founded[0]:
                await query.message.delete()
                
                create_subtitles_dl_path(query.from_user.id)
                
                file_name = get_clicked_button_text(query=query)
                
                m = await query.message.reply(f"🔽Descargando __{file_name.replace("🔡", "")}__.srt😏🔽")
                
                srt_file_original = download_subs(query.data.split("sub_")[1])
                srt_file_renamed = f"./bot/subts/{user_id}/{file_name.replace("🔡", "")}.srt"
                
                os.rename(srt_file_original, srt_file_renamed)
                
                await query.message.reply_document(srt_file_renamed)
                
                await m.edit(f"**🔼Subtitulo enviado, asegurese de que sea el correcto✅.\nGracias por usar nuestro bot.🦾🤖\nSiga disfrutando de @{os.getenv("CINEMA_ID")}🎟**")
                
                os.remove(srt_file_renamed)
        except Exception as error:
            logger.error(f"Error al descargar el subtitulo -> {error}")
            await query.message.reply(error)
    elif query.data.startswith("tr_"):
        # query for translations
        if user_founded[0]:
            # logger.info(user_founded)
            try:
                # each user has 5 translations available, except the admins, so we check that user trnaslations is >= 1
                if user_founded[1].rest_tries >= 1:
                    # translations path
                    main_path = Path.cwd() / Path("bot") / Path("translations")
                    # get target language
                    target_lang = query.data.split("_")[1]
                    
                    # input srt file: return_filename() -> name of the .srt file
                    # output srt file: will be ES_ || EN_ + return_filename()
                    input_srt =  main_path / Path("downloads") / Path(str(user_id)) / Path(return_filename())
                    output_srt = main_path / Path("output") / Path(str(user_id)) / Path(f"{target_lang.upper()}_{return_filename()}")
                    
                    # initialize Translate object
                    translator = Translate()
                    
                    # delete actual callback query message, and start processing
                    await query.message.delete()
                    
                    m = await query.message.reply(f"👨‍🔧Traduciendo ||__{return_filename().split("/")[-1]}__||, espere por favor, en cuanto termine tendra su subtitulo subido, mientras tanto, disfrute d {os.getenv("CINEMA_ID")}😉")
                    
                    # Translation...
                    try:
                        await translator.ai_srt_translate(target_lang, str(input_srt), str(output_srt))
                    
                        await m.delete()
                        update_user_value(user_id)
                    except Exception as e:
                        await query.message.reply(e)
                    
                    # final message
                    await query.message.reply_document(str(output_srt), caption=f"✅Archivo traducido✅\nPara el usuario {query.from_user.mention} ({query.from_user.id})")
                    
                    # all the files in download and output paths
                    download_files = os.listdir(main_path / Path("downloads") / Path(str(user_id)))
                    output_files = os.listdir(main_path / Path("output") / Path(str(user_id)))
                    
                    # remove them
                    for dl,ot in zip(download_files, output_files):
                        os.remove(main_path / Path("downloads") / Path(str(user_id)) / dl)
                        os.remove(main_path / Path("output") / Path(str(user_id)) / ot)
                    
                    # and finally remove the user dirs
                    os.rmdir(main_path / Path("downloads") / Path(str(user_id)))
                    os.rmdir(main_path / Path("output") / Path(str(user_id)))
                    await query.message.reply(f"Le quedan disponibles {user_founded[1].rest_tries - 1} traducciones")
                else:
                    # this is in case user doesn't have more than 1 translation available
                    await query.message.reply("Ya se termino sus traducciones, vuelva mañana por favor")
            except Exception as error:
                logger.error(f"Error durante las traducciones -> {error}")