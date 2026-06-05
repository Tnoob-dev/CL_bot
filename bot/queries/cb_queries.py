from entry.entry import bot
from utils.db_reqs import get_user, delete_post
from pyrogram.client import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import WebpageMediaEmpty
from utils.functions import check_administration, get_clicked_button_text, download_image, translate_synopsis, translate_title, translate_words
from utils.search_subts import download_subs
from utils.create_paths import create_subtitles_dl_path
from utils.movie_search import get_info_by_id
# from pathlib import Path
import os
import logging

# Logger 
logger = logging.getLogger(__name__)

# callback query for query actions
@bot.on_callback_query()
async def query_manager(client: Client, query: CallbackQuery):

    user_id = query.from_user.id
    user_founded = get_user(user_id)
    clibrary = os.getenv("CINEMA_ID")
    group_chat = os.getenv("GROUP_ID")
    
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
                await client.send_message(chat_id=group_chat, 
                                        text="Su pedido ha sido completado",
                                        reply_to_message_id=int(splitted_query_data[-1]))
            await query.message.delete()
        else:
            await query.answer(text="🤨", show_alert=True)
            
    # query for subtitle search
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
                
                await m.edit(f"**🔼Subtitulo enviado, asegurese de que sea el correcto✅.\nGracias por usar nuestro bot.🦾🤖\nSiga disfrutando de @{clibrary}🎟**")
                
                os.remove(srt_file_renamed)
        except Exception as error:
            logger.error(f"Error al descargar el subtitulo -> {error}")
            await query.message.reply(error)
                
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
                    f"**Link**: https://t.me/{group_chat}/{message_replied_id}"
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
            
    elif query.data.startswith("remove_"):
        data = query.data.split("_")
        try:
            delete_post(data[-1])
            await query.message.edit("Post eliminado del canal y BD")
            await client.delete_messages(chat_id=clibrary,
                                         message_ids=int(data[-1]))
        except Exception as e:
            await query.message.reply(e)
            
    elif query.data.startswith("close_"):

        data = query.data.split("_")

        if int(data[1]) == query.from_user.id:
            await query.message.delete()

        else:
            await query.answer("Esta no es tu busqueda :|", show_alert=True)
    elif query.data.startswith("info_"):
        
        data = query.data.split("_")
        template = ""

        movie = await get_info_by_id(data[1])

        kind = "movie" if movie["type"].lower() == "movie" or movie["type"].lower() == "tvmovie" else "serie"

        title = movie.get("primaryTitle")
        title_translated = await translate_title(title)
        year = movie.get("startYear")
        rating = movie.get("rating")
        time_in_seconds = movie.get("runtimeSeconds")
        duration = int(time_in_seconds / 60) if time_in_seconds is not None else "-"
        genres = ', '.join(translate_words(words=movie.get("genres"))) if movie.get("genres") is not None else movie.get("genres")
        plot = movie.get("plot")
        synopsis = await translate_synopsis(plot) if plot is not None else ""
        image = movie.get("primaryImage")

        if kind == "movie":
            template += f"🎬 {title} | {title_translated if title_translated is not None else title} 🎬\n"
            template += f"🗓 Año: {year}\n"
            template += f"⭐️Rating: {rating['aggregateRating'] if rating is not None else '-'}\n"
            template += f"⏱️ Duración: {duration} minutos\n"
            template += f"📚 Género: {genres}\n"
            template += f"📌 Sinopsis: {synopsis if synopsis is not None else plot}\n"
        else:
            template += f"🎭 {title} | {title_translated if title_translated is not None else title} 🎭\n"
            template += f"🗓 Año: {year}\n"
            template += f"⭐️Rating: {rating["aggregateRating"]}\n"
            template += f"⏱️ Duración: {duration} minutos por episodio\n"
            template += f"🎨 Géneros: {genres}\n"
            template += f"📖 Sinopsis: {synopsis if synopsis is not None else plot}\n"

        if image:
            try:
                await query.message.reply_photo(image["url"], caption=template)
            except WebpageMediaEmpty:
                await query.answer("No se puede subir como imagen, subiendo como archivo")
                path = await download_image(image["url"])
                await query.message.reply_document(path, caption=template)
                os.remove(path)
        else:
            await query.message.reply(template)

        template = ""