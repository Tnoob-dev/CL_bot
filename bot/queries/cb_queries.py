from entry.entry import bot
from commands.Translations import return_filename
from utils.db_reqs import get_user, update_user_value
from pyrogram.client import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
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
    if query.data.startswith('order_ready'):
        splitted_query_data = query.data.split("_")
        if check_administration(query):
            if "pm" in splitted_query_data:
                await client.send_message(
                    chat_id=int(splitted_query_data[-1]),
                    text="Su pedido ha sido completado"
                )
            else:    
                await client.send_message(chat_id="chat1080p", 
                                        text="Su pedido ha sido completado",
                                        reply_to_message_id=int(splitted_query_data[-1]))
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
    elif query.data.startswith("order_not_found_"):
        try:
            message_replied_id = query.message.reply_to_message_id
            splitted_query_data = query.data.split("_")
            user_message = splitted_query_data[-1]
            user_id_cb = int(splitted_query_data[-2])
            
            await query.message.delete()
            
            await query.message.reply(
                "✅Orden Reenviada a los administradores✅",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🎬Canal de pedidos🎬", url="https://t.me/CinemaOrders")]
                    ]))
            
            await client.send_message(
                chat_id="CinemaOrders",
                text=(
                    f"🎟Nueva solicitud:\n\n"
                    f"**Pedido**: __{user_message}__\n"
                    f"**Usuario**: {query.from_user.mention} (__{user_id_cb}__)\n"
                    f"**Link**: https://t.me/{os.getenv("CINEMA_ID")}/{message_replied_id}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🫡Orden Lista🫡", callback_data=f"order_ready_{message_replied_id}")]
                    ]
                ))

            await query.answer("Tu orden fue enviada a los administradores ✅", show_alert=False)
        except Exception as e:
            logger.error(f"Error en order_not_found -> {e}")
            await query.answer("Ocurrió un error al reenviar tu orden.", show_alert=True)
    elif query.data.startswith("pm_order_not_found_"):
        try:
            splitted_query_data = query.data.split("_")
            user_message = splitted_query_data[-1]
            user_id_cb = int(splitted_query_data[-2])
            
            await query.message.delete()
            
            await query.message.reply(
                "✅Orden Reenviada a los administradores✅",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🎬Canal de pedidos🎬", url="https://t.me/CinemaOrders")]
                    ]))
            
            await client.send_message(
                chat_id="CinemaOrders",
                text=(
                    f"🎟Nueva solicitud:\n\n"
                    f"**Pedido**: __{user_message}__\n"
                    f"**Usuario**: {query.from_user.mention} (__{user_id_cb}__)\n"
                    "**Link**: DM"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🫡Orden Lista🫡", callback_data=f"order_ready_pm_{user_id_cb}")]
                    ]
                ))
            
        except Exception as e:
            logger.error(f"Error en pm_order_not_found -> {e}")
            await query.answer("Ocurrió un error al reenviar tu orden.", show_alert=True)
    elif query.data == "close":
        await query.message.delete()