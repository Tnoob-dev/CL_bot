import logging
import os
from contextlib import suppress
from pathlib import Path

from entry.entry import bot
from pyrogram import Client
from pyrogram.errors import WebpageMediaEmpty
from pyrogram.filters import photo, private
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from utils.create_paths import create_subtitles_dl_path
from utils.db_reqs import delete_post, get_user, update_user_premium
from utils.functions import (
    check_administration,
    get_clicked_button_text,
    translate_synopsis,
    translate_title,
    translate_words,
)
from utils.movie_search import (
    get_info_by_id,
    get_movie_info_by_id_tmdb,
    get_tv_info_by_id_tmdb,
)
from utils.rt_client import info
from utils.search_subts import download_subs

# Logging config
logger = logging.getLogger(__name__)

last_user_photo = {}


@bot.on_message(private & photo, group=0)
async def save_user_photo(client: Client, message: Message):
    """Guarda el file_id de la última foto enviada por el usuario en privado."""
    user_id = message.from_user.id
    last_user_photo[user_id] = message.photo.file_id



# helpers
def _get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

async def _format_imdb_info(movie: dict) -> str:
    """Formatea la información obtenida de IMDb."""
    kind = "movie" if movie.get("type", "").lower() in ["movie", "tvmovie"] else "serie"
    title = movie.get("primaryTitle")
    title_translated = await translate_title(title)
    year = movie.get("startYear")
    rating = movie.get("rating")
    time_in_seconds = movie.get("runtimeSeconds")
    duration = int(time_in_seconds / 60) if time_in_seconds else "-"
    
    genres_raw = movie.get("genres")
    genres = ", ".join(await translate_words(words=genres_raw)) if genres_raw else "-"
    
    plot = movie.get("plot")
    synopsis = await translate_synopsis(plot) if plot else ""
    
    emoji = "🎬" if kind == "movie" else "🎭"
    duration_text = "minutos" if kind == "movie" else "minutos por episodio"
    
    template = (
        f"{emoji} **{title}** | **{title_translated or title}** {emoji}\n"
        f"🗓 Año: **{year}**\n"
        f"⭐️ Rating: **{rating['aggregateRating'] if rating else '-'}/10**\n"
    )
    
    if kind == "movie":
        rt_info = await info(title)
        if rt_info:
            tomato = rt_info.get("tomatoes")
            audience = rt_info.get("audience")
            if tomato:
                template += f"🍅 Rotten Tomatoes: **{tomato.get('percentage')} ({tomato.get('reviews')})**\n"
            if audience:
                template += f"👤 Audiencia: **{audience.get('percentage')} ({audience.get('reviews')})**\n"

    template += (
        f"⏱️ Duración: **{duration} {duration_text}**\n"
        f"📚 Género: **{genres}**\n\n"
        f"<blockquote expandable><strong>{synopsis or plot}</strong></blockquote>\n"
    )
    return template, movie.get("primaryImage", {}).get("url")

async def _format_tmdb_movie_info(movie: dict) -> tuple[str, str]:
    """Formatea la información de películas de TMDB."""
    title = movie.get('original_title')
    year = movie.get('release_date', '').split("-")[0]
    title_translated = await translate_title(title)
    rating = round(movie.get('vote_average', 0), 1)
    duration = movie.get("runtime") or "-"
    
    genres = ", ".join([g.get('name') for g in movie.get("genres", [])])
    genres = await translate_words(words=genres.split(", ")) if genres else "-"
    
    plot = movie.get('overview')
    synopsis = await translate_synopsis(plot) or plot
    image_url = f"{_get_env('TMDB_IMAGE_BASE_URL')}{movie.get('poster_path')}"
    
    template = (
        f"🎬 **{title}** | **{title_translated or title}** 🎬\n"
        f"🗓 Año: **{year}**\n"
        f"⭐️ Rating: **{rating}/10**\n"
        f"⏱️ Duración: **{duration} minutos**\n"
        f"📚 Géneros: **{genres}**\n\n"
        f"<blockquote expandable><strong>{synopsis}</strong></blockquote>\n"
    )
    return template, image_url

async def _format_tmdb_series_info(serie: dict) -> tuple[str, str]:
    """Formatea la información de series de TMDB."""
    title = serie.get('original_name')
    year = serie.get('first_air_date', '').split("-")[0]
    title_translated = await translate_title(title)
    rating = round(serie.get('vote_average', 0), 1)
    
    run_times = serie.get('episode_run_time', [])
    duration = int(sum(run_times) / len(run_times)) if run_times else "-"
    
    genres = ", ".join([g.get('name') for g in serie.get("genres", [])])
    genres = await translate_words(words=genres.split(", ")) if genres else "-"
    
    plot = serie.get('overview')
    synopsis = await translate_synopsis(plot) or plot
    image_url = f"{_get_env('TMDB_IMAGE_BASE_URL')}{serie.get('poster_path')}"
    
    template = (
        f"🎬 **{title}** | **{title_translated or title}** 🎬\n"
        f"🗓 Año: **{year}**\n"
        f"⭐️ Rating: **{rating}/10**\n"
        f"⏱️ Duración: **{duration} minutos por episodio**\n"
        f"📚 Géneros: **{genres}**\n\n"
        f"<blockquote expandable><strong>{synopsis}</strong></blockquote>\n"
    )
    return template, image_url

async def _send_media_message(query: CallbackQuery, template: str, image_url: str):
    """Envía la información como foto o documento si la foto falla."""
    if image_url:
        try:
            await query.message.reply_photo(image_url, caption=template)
        except WebpageMediaEmpty:
            await query.answer("No se puede subir como imagen, subiendo como archivo", show_alert=True)
            await query.message.reply_document(document=image_url, caption=template)
    else:
        await query.message.reply(template)


# subhandlers
async def _handle_orders(client: Client, query: CallbackQuery):
    data = query.data
    group_chat = _get_env("GROUP_ID")
    
    if data.startswith("order_ready"):
        if check_administration(query):
            msg_id = int(data.split("_")[-1])
            await client.send_message(group_chat, "Su pedido ha sido completado", reply_to_message_id=msg_id)
            await query.message.delete()
        else:
            await query.answer("🤨", show_alert=True)
            
    elif data.startswith("order_not_found_"):
        try:
            parts = data.split("_")
            user_id_cb, msg_id = int(parts[-2]), int(parts[-1])
            
            # do not delete the message before answeer, it cause pyrogram errors
            await query.message.edit_text("✅ Orden Reenviada a los administradores ✅")
            
            await client.send_message(
                chat_id=_get_env("ORDERS_ID"),
                text=(
                    f"🎟 Nueva solicitud:\n\n"
                    f"📩 **Pedido**: <code>{parts[-1]}</code>\n"
                    f"👤 **Usuario**: {query.from_user.mention} (__{user_id_cb}__)\n"
                    f"🔗 **Link**: https://t.me/{group_chat}/{msg_id}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🫡 Orden Lista 🫡", callback_data=f"order_ready_{msg_id}"),
                        InlineKeyboardButton("❌ No encontrado ❌", callback_data=f"order_404_{msg_id}"),
                    ]
                ])
            )
            await query.answer("Tu orden fue enviada a los administradores ✅")
        except Exception:
            logger.exception("Error en order_not_found")
            await query.answer("Ocurrió un error al reenviar tu orden.", show_alert=True)
            
    elif data.startswith("order_404_") and check_administration(query):
        msg_id = int(data.split("_")[-1])
        await client.send_message(group_chat, "Lo sentimos, no encontramos su pedido.", reply_to_message_id=msg_id)
        await query.message.delete()


async def _handle_subtitles(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    user_founded = get_user(user_id)
    clibrary = _get_env("CINEMA_ID")
    
    if user_founded[0]:
        await query.message.delete()
        create_subtitles_dl_path(user_id)
        file_name = get_clicked_button_text(query).replace('🔡', '')
        
        m = await query.message.reply(f"🔽 Descargando __{file_name}__.srt 😏🔽")
        try:
            srt_file_original = download_subs(query.data.split("sub_")[1])
            srt_file_renamed = f"./bot/subts/{user_id}/{file_name}.srt"
            os.rename(srt_file_original, srt_file_renamed)
            
            await query.message.reply_document(srt_file_renamed)
            await m.edit(
                f"**🔼 Subtítulo enviado, asegúrese de que sea el correcto ✅.\n"
                f"Gracias por usar nuestro bot. 🦾🤖\nSiga disfrutando de @{clibrary} 🎟**"
            )
            os.remove(srt_file_renamed)
        except Exception:
            logger.exception("Error al descargar el subtítulo")
            await m.edit("❌ Ocurrió un error al descargar el subtítulo. Inténtalo de nuevo más tarde.")
    else:
        await query.answer("No tienes permisos para descargar subtítulos.", show_alert=True)


async def _handle_media_info(client: Client, query: CallbackQuery):
    data = query.data.split("_")
    source, media_id = data[1], data[-1]
    
    if source == "imdb":
        movie = await get_info_by_id(media_id)
        template, image_url = await _format_imdb_info(movie)
    elif source == "movie":
        movie = await get_movie_info_by_id_tmdb(media_id)
        template, image_url = await _format_tmdb_movie_info(movie)
    elif source == "serie":
        serie = await get_tv_info_by_id_tmdb(media_id)
        template, image_url = await _format_tmdb_series_info(serie)
    else:
        await query.answer("Fuente de información no válida.", show_alert=True)
        return

    await _send_media_message(query, template, image_url)


async def _handle_remove_post(client: Client, query: CallbackQuery):
    if not check_administration(query):
        await query.answer("🤨", show_alert=True)
        return
        
    post_id = query.data.split("_")[-1]
    clibrary = _get_env("CINEMA_ID")
    try:
        delete_post(post_id)
        await query.message.edit("Post eliminado del canal y BD")
        await client.delete_messages(chat_id=clibrary, message_ids=int(post_id))
    except Exception:
        logger.exception("Error al eliminar el post")
        await query.message.reply("❌ Ocurrió un error al eliminar el post.")


async def _handle_close_search(client: Client, query: CallbackQuery):
    target_user = int(query.data.split("_")[1])
    if target_user == query.from_user.id:
        await query.message.delete()
    else:
        await query.answer("Esta no es tu búsqueda :|", show_alert=True)


async def _handle_payments(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    pay_methods = {
        "metro": {"card": _get_env("CUP_CARD"), "extra": f"💳 Tarjeta: <code>{_get_env('CUP_CARD')}</code>\n📱 Confirmar: <code>{_get_env('MOBILE')}</code>"},
        "bpa_cup": {"card": _get_env("CUP_CARD2"), "extra": f"💳 Tarjeta: <code>{_get_env('CUP_CARD2')}</code>\n📱 Confirmar: <code>{_get_env('MOBILE')}</code>"},
        "bpa_mlc": {"card": _get_env("MLC_CARD"), "extra": f"💳 Tarjeta: <code>{_get_env('MLC_CARD')}</code>\n📱 Confirmar: <code>{_get_env('MOBILE')}</code>"},
        "sm": {"card": None, "extra": f"📱 Móvil: <code>{_get_env('MOBILE')}</code>"},
    }
    
    confirm_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar ✅", callback_data="confirm_pay")]])
    base_text = "No debe recortar la foto, envíe con fecha y hora presentes.\n\nSolo toque los números para copiar:\n\n"

    if data == "become_vip":
        text = (
            f"Coste del plan VIP 💎:\n"
            f"- 💳 Tarjeta ➡️ {_get_env('VIP_PRICE_CUP')} CUP\n"
            f"- 💳 Tarjeta ➡️ {_get_env('VIP_PRICE_MLC')} MLC\n"
            f"- 💵 USD (PayPal/QvaPay/Crypto) ➡️ {_get_env('VIP_PRICE_USD')} USD\n"
            f"- 📱 Saldo Móvil ➡️ {_get_env('VIP_PRICE_CUP')} CUP\n\n"
            f"Ventajas que ofrece el plan 📈:\n"
            f"- Stream de archivos y videos 📺\n"
            f"- Se quita la eliminación de archivos de 3 minutos 🔥\n\n"
            f"⏳ El plan tiene una duración de 30 días a partir de su compra\n\n"
            f"Seleccione uno de los métodos de pago de abajo ⬇️"
        )
        buttons = [
            [InlineKeyboardButton("💳 CUP Metropolitano", callback_data="pay_edit_metro")],
            [InlineKeyboardButton("💳 CUP BPA", callback_data="pay_edit_bpa_cup")],
            [InlineKeyboardButton("💳 MLC BPA", callback_data="pay_edit_bpa_mlc")],
            [InlineKeyboardButton("💙 ENZONA", callback_data="pay_edit_enzona")],
            [InlineKeyboardButton("📱 Saldo Móvil", callback_data="pay_edit_sm")],
            [InlineKeyboardButton("💵 PayPal/QvaPay", callback_data="pay_edit_paypal")],
        ]
        await query.message.delete()
        await query.message.reply(text=text, reply_markup=InlineKeyboardMarkup(buttons))
        
    elif data.startswith("pay_edit_"):
        method = data.replace("pay_edit_", "")
        
        if method in pay_methods:
            await query.message.edit(text=base_text + pay_methods[method]["extra"], reply_markup=confirm_markup)
        elif method == "enzona":
            await query.message.delete()
            await query.message.reply_photo(
                photo=Path.cwd() / "assets" / "enzona_pic.jpg",
                caption="No debe recortar la foto, envíe con fecha y hora presentes.\n\nPresione en Confirmar ✅ para enviar su evidencia.",
                reply_markup=confirm_markup
            )
        elif method == "paypal":
            await query.message.delete()
            await query.message.reply_photo(
                photo=Path.cwd() / "assets" / "qvapay_pic.png",
                caption="No debe recortar la foto, envíe con fecha y hora presentes.\n\nPresione en Confirmar ✅ para enviar su evidencia.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💜 QvaPay PayMe Link", url=_get_env("QVAPAY_LINK"))],
                    [InlineKeyboardButton("Confirmar ✅", callback_data="confirm_pay")]
                ])
            )
            
    elif data == "confirm_pay":
        await query.message.delete()
        await query.message.reply(
            text="📸 *Envíe su captura de pago ahora.*\n\nUna vez enviada la imagen, presione el botón de abajo para finalizar:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar ✅", callback_data="send_pay_admin")]])
        )
        
    elif data == "send_pay_admin":
        photo_id = last_user_photo.get(user_id)
        if photo_id:
            await query.answer("✅ Procesando comprobante...")
            user_info = query.from_user
            caption = f"🔔 Nuevo comprobante\n👤 @{user_info.username or 'Sin username'}\n🆔 `{user_id}`"
            buttons = [
                [
                    InlineKeyboardButton("Aceptar Pago ✅", callback_data=f"premium_accept_{user_info.username or 'Sin username'}_{user_id}"),
                    InlineKeyboardButton("Declinar Pago ❌", callback_data=f"premium_decline_{user_info.username or 'Sin username'}_{user_id}"),
                ]
            ]
            await client.send_photo(
                chat_id=int(_get_env("PAY_GROUP")),
                photo=photo_id,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            del last_user_photo[user_id]
            await query.message.edit_text("✅ *¡Comprobante enviado a los administradores!*")
        else:
            await query.answer("⚠️ Primero envía la captura de pago.", show_alert=True)
            
    elif data.startswith("premium_"):
        parts = data.split("_")
        action, username, target_user_id = parts[1], parts[2], int(parts[-1])
        
        if action == "accept":
            success, dead_date = update_user_premium(target_user_id, days=32)
            if success:
                await client.send_message(
                    chat_id=target_user_id,
                    text=(
                        "✅ *¡Pago Aceptado!*\n\n"
                        "🎉 *Felicidades*, su plan *VIP* ha sido activado correctamente.\n\n"
                        f"📅 *Válido hasta:* `{dead_date}`\n\n"
                        "Disfrute de todos los beneficios exclusivos. Si tiene alguna duda, no dude en contactarnos."
                    )
                )
                await query.message.edit(f"Pago aceptado ✅\n\nUsuario: @{username}\n\n🆔 {target_user_id}")
        else:
            await client.send_message(
                chat_id=target_user_id,
                text=(
                    "⚠️ *Problema con su Pago*\n\n"
                    "Lamentamos informarle que hemos detectado un inconveniente con su comprobante de pago.\n\n"
                    "📋 *Posibles causas:*\n"
                    "• Monto incorrecto\n• Captura no legible\n• Pago no verificado\n\n"
                    "🆘 *¿Qué hacer?*\n"
                    f"Contacte a la administración a través del grupo oficial: @{_get_env('GROUP_ID')}\n\n"
                    "Estamos aquí para ayudarle."
                )
            )
            await query.message.edit(f"Pago denegado ❌\n\nUsuario: @{username}\n\n🆔 {target_user_id}")

@bot.on_callback_query()
async def query_manager(client: Client, query: CallbackQuery):
    """Router principal para todas las CallbackQueries."""
    data = query.data
    
    try:
        if data.startswith("order_"):
            await _handle_orders(client, query)
        elif data.startswith("sub_"):
            await _handle_subtitles(client, query)
        elif data.startswith("info_"):
            await _handle_media_info(client, query)
        elif data.startswith("remove_"):
            await _handle_remove_post(client, query)
        elif data.startswith("close_"):
            await _handle_close_search(client, query)
        elif data in ("become_vip", "confirm_pay", "send_pay_admin") or data.startswith(("pay_edit_", "premium_")):
            await _handle_payments(client, query)
        else:
            await query.answer("Acción no reconocida.", show_alert=True)
            
    except Exception:
        logger.exception("Error crítico en query_manager (data: %s)", data)
        try:
            await query.answer("Ocurrió un error inesperado. Inténtalo de nuevo.", show_alert=True)
        except Exception:
            logger.exception()
            suppress(Exception)