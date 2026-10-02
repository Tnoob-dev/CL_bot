import logging
import os
import shutil
from pathlib import Path

from entry.entry import bot
from pyrogram.client import Client
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
from utils.movie_search import get_info_by_id, get_movie_info_by_id_tmdb, get_tv_info_by_id_tmdb
from utils.rt_client import info
from utils.search_subts import download_subs

# Logger
logger = logging.getLogger(__name__)

last_user_photo = {}

# ---------------------------------------------------------------------------
# Constantes / assets compartidos
# ---------------------------------------------------------------------------
SEARCH_ERROR_TEXT = "❌ Ocurrió un error al descargar el subtítulo. Inténtalo de nuevo más tarde."
PAY_INSTRUCTIONS = "No debe recortar la foto, envie con fecha y hora presentes.\n\n"
CONFIRM_BUTTON = InlineKeyboardButton("Confirmar✅", callback_data="confirm_pay")
FOLDER_ZIP_STICKER = Path.cwd() / "assets" / "folderToZip.tgs"
ENZONA_PIC = Path.cwd() / "assets" / "enzona_pic.jpg"
QVAPAY_PIC = Path.cwd() / "assets" / "qvapay_pic.png"


def _env(name: str) -> str:
    """Devuelve una variable de entorno obligatoria (falla rapido si falta)."""
    value = os.getenv(name)
    if value is None:
        logger.warning(f"Variable de entorno {name} no configurada")
    return value


# ---------------------------------------------------------------------------
# Handler de fotos de usuario
# ---------------------------------------------------------------------------
@bot.on_message(private & photo, group=0)
async def save_user_photo(client: Client, message: Message):
    last_user_photo[message.from_user.id] = message.photo.file_id


# ---------------------------------------------------------------------------
# Helpers de negocio
# ---------------------------------------------------------------------------
async def _download_subtitle(query: CallbackQuery, file_id: str, send_document: bool):
    """Descarga un subtitulo; en modo bulk solo edita el mensaje de progreso."""
    user_founded = get_user(query.from_user.id)
    if not user_founded[0]:
        return

    user = user_founded[1]
    create_subtitles_dl_path(user.id)
    file_name = get_clicked_button_text(query=query).replace("🔡", "")

    m = await query.message.reply(f"🔽Descargando __{file_name}__.srt😏🔽")
    srt_original = download_subs(file_id)
    srt_renamed = f"./bot/subts/{user.id}/{file_name}.srt"
    os.rename(srt_original, srt_renamed)

    if send_document:
        await query.message.delete()
        await query.message.reply_document(srt_renamed)
        await m.edit(
            f"**🔼Subtitulo enviado, asegurese de que sea el correcto✅.\n"
            f"Gracias por usar nuestro bot.🦾🤖\n"
            f"Siga disfrutando de @{_env('CINEMA_ID')}🎟**"
        )
        os.remove(srt_renamed)
    else:
        await m.edit(f"Descargado {file_name}")


async def _send_media_with_fallback(query: CallbackQuery, image, template: str):
    """Envia la imagen de la ficha; si Telegram no puede capturarla, manda documento."""
    try:
        await query.message.reply_photo(image, caption=template)
    except WebpageMediaEmpty:
        await query.answer("No se puede subir como imagen, subiendo como archivo")
        await query.message.reply_document(document=image, caption=template)


def _base_template(
    title, title_translated, year, rating_str, extra_lines, duration_line,
    genre_label, genres, synopsis, plot, emoji,
):
    """Plantilla comun para las fichas IMDB/TMDB (pelicula y serie).

    `extra_lines` se inserta tras el rating (ej. Rotten Tomatoes) y
    `duration_line` justo despues; ambos pueden venir vacios.
    """
    display_title = title_translated if title_translated is not None else title
    synopsis_or_plot = synopsis if synopsis is not None else plot
    return (
        f"{emoji} **{title}** | **{display_title}** {emoji}\n"
        f"🗓 Año: **{year}**\n"
        f"⭐️Rating: **{rating_str}/10**\n"
        f"{extra_lines}"
        f"{duration_line}\n"
        f"📚 {genre_label}: **{genres}**\n"
        f"\n<blockquote expandable><strong>{synopsis_or_plot}</strong></blockquote>\n"
    )


# ---------------------------------------------------------------------------
# Handlers de callbacks (uno por responsabilidad)
# ---------------------------------------------------------------------------
async def handle_order_ready(client: Client, query: CallbackQuery):
    """Admin marca un pedido como completado."""
    if not check_administration(query):
        await query.answer(text="🤨", show_alert=True)
        return
    msg_id = int(query.data.split("_")[-1])
    await client.send_message(
        chat_id=_env("GROUP_ID"),
        text="Su pedido ha sido completado",
        reply_to_message_id=msg_id,
    )
    await query.message.delete()


async def handle_subtitle(client: Client, query: CallbackQuery):
    """Descarga individual de subtitulo (/srt)."""
    try:
        await _download_subtitle(query, query.data.split("sub_", 1)[1], send_document=True)
    except Exception as error:
        logger.error(f"Error al descargar el subtitulo -> {error}")
        await query.message.reply(SEARCH_ERROR_TEXT)


async def handle_bulk_subtitle(client: Client, query: CallbackQuery):
    """Descarga acumulada de subtitulos (/bsrt); agrega el archivo al zip final."""
    try:
        # split maxsplit=1 preserva el file_id real tras 'bulk_sub_'
        await _download_subtitle(query, query.data.split("bulk_sub_", 1)[1], send_document=False)
    except Exception as error:
        logger.error(f"Error al descargar el subtitulo -> {error}")
        await query.message.reply(SEARCH_ERROR_TEXT)


async def handle_bulk_end(client: Client, query: CallbackQuery):
    """Finaliza el modo bulk: empaqueta los subtitulos en un zip."""
    user_id = get_user(query.from_user.id)[1].id
    sub_dir = f"./bot/subts/{user_id}"

    await query.message.delete()
    await query.message.reply("Subtitulos seleccionados✅, creando zip🗂...")
    await query.message.reply_sticker(FOLDER_ZIP_STICKER)

    zip_dir = shutil.make_archive(f"subs_{user_id}", "zip", sub_dir)
    await query.message.reply_document(zip_dir)

    shutil.rmtree(sub_dir)
    os.remove(zip_dir)


async def handle_order_not_found(client: Client, query: CallbackQuery):
    """Usuario reenvia su pedido a los administradores."""
    try:
        parts = query.data.split("_")
        user_message = parts[-1]
        user_id_cb = int(parts[-2])
        replied_msg_id = query.message.reply_to_message_id

        await query.message.reply(
            "✅Orden Reenviada a los administradores✅",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎬Canal de pedidos🎬", url=f"https://t.me/{_env('ORDERS_ID')}")]]
            ),
        )
        await query.message.delete()

        await client.send_message(
            chat_id=_env("ORDERS_ID"),
            text=(
                f"🎟Nueva solicitud:\n\n"
                f"📩**Pedido**: <code>{user_message}</code>\n"
                f"👤**Usuario**: {query.from_user.mention} (__{user_id_cb}__)\n"
                f"🔗**Link**: https://t.me/{_env('GROUP_ID')}/{replied_msg_id}"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🫡Orden Lista🫡", callback_data=f"order_ready_{replied_msg_id}"),
                        InlineKeyboardButton("❌No encontrado❌", callback_data=f"order_404_{replied_msg_id}"),
                    ]
                ]
            ),
        )
        await query.answer("Tu orden fue enviada a los administradores ✅", show_alert=False)
    except Exception as e:
        logger.error(f"Error en order_not_found -> {e}")
        await query.answer("Ocurrió un error al reenviar tu orden.", show_alert=True)


async def handle_order_404(client: Client, query: CallbackQuery):
    """Admin notifica al usuario que su pedido no fue encontrado."""
    if not check_administration(query):
        return
    msg_id = int(query.data.split("_")[-1])
    await client.send_message(
        chat_id=_env("GROUP_ID"),
        reply_to_message_id=msg_id,
        text="Lo sentimos, no encontramos su pedido.",
    )
    await query.message.delete()


async def handle_remove_post(client: Client, query: CallbackQuery):
    """Elimina un post del canal y de la BD."""
    post_id = query.data.split("_")[-1]
    try:
        delete_post(post_id)
        await query.message.edit("Post eliminado del canal y BD")
        await client.delete_messages(chat_id=_env("CINEMA_ID"), message_ids=int(post_id))
    except Exception as e:
        logger.error(f"Error al eliminar el post -> {e}")
        await query.message.reply("❌ Ocurrió un error al eliminar el post. Inténtalo de nuevo más tarde.")


async def handle_close_search(client: Client, query: CallbackQuery):
    """Cierra la busqueda, solo para el usuario que la inicio."""
    owner_id = int(query.data.split("_")[1])
    if owner_id == query.from_user.id:
        await query.message.delete()
    else:
        await query.answer("Esta no es tu busqueda :|", show_alert=True)


async def handle_imdb_info(client: Client, query: CallbackQuery):
    """Ficha de pelicula/serie desde IMDB."""
    movie = await get_info_by_id(query.data.split("_")[-1])
    kind = "movie" if movie.get("type").lower() in ("movie", "tvmovie") else "serie"

    title = movie.get("primaryTitle")
    title_translated = await translate_title(title)
    rating = movie.get("rating")
    runtime = movie.get("runtimeSeconds")
    duration = int(runtime / 60) if runtime is not None else "-"
    genres = (
        ", ".join(await translate_words(words=movie.get("genres")))
        if movie.get("genres") is not None
        else movie.get("genres")
    )
    plot = movie.get("plot")
    synopsis = await translate_synopsis(plot) if plot is not None else ""
    rating_str = f"{rating['aggregateRating'] if rating is not None else '-'}"

    tomato = audience = None
    extra_lines = ""
    if kind == "movie":
        rt_info = await info(title)
        if rt_info is not None:
            tomato = rt_info.get("tomatoes")
            audience = rt_info.get("audience")
        if tomato is not None:
            extra_lines += f"🍅Rotten Tomatoes: **{tomato.get('percentage')} ({tomato.get('reviews')})**\n"
        if audience is not None:
            extra_lines += f"👤Audiencia: **{audience.get('percentage')} ({audience.get('reviews')})**\n"

    is_movie = kind == "movie"
    template = _base_template(
        title=title,
        title_translated=title_translated,
        year=movie.get("startYear"),
        rating_str=rating_str,
        extra_lines=extra_lines,
        duration_line=(
            f"⏱️ Duración: **{duration} minutos**" if is_movie
            else f"⏱️ Duración: **{duration} minutos por episodio**"
        ),
        genre_label="Género" if is_movie else "Géneros",
        genres=genres,
        synopsis=synopsis,
        plot=plot,
        emoji="🎬" if is_movie else "🎭",
    )

    image = movie.get("primaryImage")
    if image:
        await _send_media_with_fallback(query, image.get("url"), template)
    else:
        await query.message.reply(template)


async def handle_tmdb_movie(client: Client, query: CallbackQuery):
    """Ficha de pelicula desde TMDB."""
    movie = await get_movie_info_by_id_tmdb(query.data.split("_")[-1])
    title = movie.get("original_title")
    genres = ", ".join(await translate_words(words=[g["name"] for g in movie.get("genres")]))
    plot = movie.get("overview")
    synopsis = await translate_synopsis(plot) or plot
    rating = round(movie.get("vote_average"), 1)
    duration = movie.get("runtime") if movie.get("runtime") is not None else "-"
    image = f"{_env('TMDB_IMAGE_BASE_URL')}{movie.get('poster_path')}"

    template = _base_template(
        title=title,
        title_translated=await translate_title(title),
        year=movie.get("release_date").split("-")[0],
        rating_str=str(rating),
        extra_lines="",
        duration_line=f"⏱️ Duración: **{duration} minutos**",
        genre_label="Géneros",
        genres=genres,
        synopsis=synopsis,
        plot=plot,
        emoji="🎬",
    )
    await _send_media_with_fallback(query, image, template)


async def handle_tmdb_serie(client: Client, query: CallbackQuery):
    """Ficha de serie desde TMDB."""
    serie = await get_tv_info_by_id_tmdb(query.data.split("_")[-1])
    title = serie.get("original_name")
    genres = ", ".join(await translate_words(words=[g["name"] for g in serie.get("genres")]))
    plot = serie.get("overview")
    synopsis = await translate_synopsis(plot) or plot
    rating = round(serie.get("vote_average"), 1)

    runtimes = list(serie.get("episode_run_time"))
    duration = int(sum(runtimes) / len(runtimes)) if runtimes else "-"
    image = f"{_env('TMDB_IMAGE_BASE_URL')}{serie.get('poster_path')}"

    template = _base_template(
        title=title,
        title_translated=await translate_title(title),
        year=serie.get("first_air_date").split("-")[0],
        rating_str=str(rating),
        extra_lines="",
        duration_line=f"⏱️ Duración: **{duration} minutos por episodio**",
        genre_label="Géneros",
        genres=genres,
        synopsis=synopsis,
        plot=plot,
        emoji="🎬",
    )
    await _send_media_with_fallback(query, image, template)


async def handle_info(client: Client, query: CallbackQuery):
    """Router de fichas: imdb / movie / serie."""
    source = query.data.split("_")[1]
    if source == "imdb":
        await handle_imdb_info(client, query)
    elif source == "movie":
        await handle_tmdb_movie(client, query)
    else:
        await handle_tmdb_serie(client, query)


async def handle_become_vip(client: Client, query: CallbackQuery):
    """Muestra el plan VIP y sus metodos de pago."""
    text = f"""
Coste del plan VIP 💎:
    - 💳 Tarjeta ➡️ {_env('VIP_PRICE_CUP')} CUP
    - 💳 Tarjeta ➡️ {_env('VIP_PRICE_MLC')} MLC
    - 💵 USD (PayPal/QvaPay/Crypto) ➡️ {_env('VIP_PRICE_USD')} USD
    - 📱 Saldo Movil ➡️ {_env('VIP_PRICE_CUP')} CUP

Ventajas que ofrece el plan 📈:
    - Stream de archivos y videos 📺
    - Se quita la eliminacion de archivos de 3 minutos 🔥

⏳ El plan tiene una duracion de 30 dias a partir de su compra

Seleccione uno de los metodos de pago de abajo ⬇️
"""
    buttons = [
        [InlineKeyboardButton("💳 CUP Metropolitano", callback_data="pay_edit_metro")],
        [InlineKeyboardButton("💳 CUP BPA", callback_data="pay_edit_bpa_cup")],
        [InlineKeyboardButton("💳 MLC BPA", callback_data="pay_edit_bpa_mlc")],
        [InlineKeyboardButton("💙 ENZONA", callback_data="pay_edit_enzona")],
        [InlineKeyboardButton("📱 Saldo Movil", callback_data="pay_edit_sm")],
        [InlineKeyboardButton("💵 PayPal/QvaPay", callback_data="pay_edit_paypal")],
    ]
    await query.message.delete()
    await query.message.reply(text=text, reply_markup=InlineKeyboardMarkup(buttons))


# Metodos de pago tipo tarjeta/saldo: sufijo callback -> (variable env, etiqueta)
CARD_PAYMENTS = {
    "metro": ("CUP_CARD", "💳Tarjeta"),
    "bpa_cup": ("CUP_CARD2", "💳Tarjeta"),
    "bpa_mlc": ("MLC_CARD", "💳Tarjeta"),
    "sm": ("MOBILE", "📱Movil"),
}


async def handle_pay_edit(client: Client, query: CallbackQuery):
    """Instrucciones segun metodo de pago seleccionado."""
    method = query.data.removeprefix("pay_edit_")
    confirm_markup = InlineKeyboardMarkup([[CONFIRM_BUTTON]])

    if method in CARD_PAYMENTS:
        env_key, label = CARD_PAYMENTS[method]
        lines = f"{label}: <code>{_env(env_key)}</code>"
        if method != "sm":
            lines += f"\n📱Confirmar: <code>{_env('MOBILE')}</code>"
        await query.message.edit(
            text=f"{PAY_INSTRUCTIONS}Solo toque los numeros para copiar:\n\n{lines}\n\nPresione en Confirmar✅ para enviar su evidencia de pago a los admins",
            reply_markup=confirm_markup,
        )
    elif method == "enzona":
        await query.message.delete()
        await query.message.reply_photo(
            photo=ENZONA_PIC,
            caption=f"{PAY_INSTRUCTIONS}Presione en Confirmar✅ para enviar su evidencia de pago a los admins",
            reply_markup=confirm_markup,
        )
    elif method == "paypal":
        await query.message.delete()
        await query.message.reply_photo(
            photo=QVAPAY_PIC,
            caption=f"{PAY_INSTRUCTIONS}Presione en Confirmar✅ para enviar su evidencia de pago a los admins",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("💜QvaPay PayMe Link", url=_env("QVAPAY_LINK"))],
                    [CONFIRM_BUTTON],
                ]
            ),
        )


async def handle_confirm_pay(client: Client, query: CallbackQuery):
    """Pide la captura de pantalla del pago."""
    await query.message.delete()
    await query.message.reply(
        text="📸 *Envíe su captura de pago ahora.*\n\nUna vez enviada la imagen, presione el botón de abajo para finalizar:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Confirmar✅", callback_data="send_pay_admin")]]
        ),
    )


async def handle_send_pay_admin(client: Client, query: CallbackQuery):
    """Envia el comprobante al grupo de administradores."""
    user_id = query.from_user.id
    photo_id = last_user_photo.get(user_id)

    if not photo_id:
        await query.answer("⚠️ Primero envía la captura de pago.", show_alert=True)
        return

    await query.answer("✅ Procesando comprobante...")
    username = query.from_user.username or "Sin username"
    caption = f"🔔 Nuevo comprobante\n👤 @{username}\n🆔 `{user_id}`"
    buttons = [
        [
            InlineKeyboardButton("Aceptar Pago✅", callback_data=f"premium_accept_{username}_{user_id}"),
            InlineKeyboardButton("Declinar Pago❌", callback_data=f"premium_decline_{username}_{user_id}"),
        ]
    ]

    await client.send_photo(
        chat_id=int(_env("PAY_GROUP")),
        photo=photo_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    del last_user_photo[user_id]
    await query.message.edit_text("✅ *¡Comprobante enviado a los administradores!*")


async def handle_premium(client: Client, query: CallbackQuery):
    """Admin acepta o declina un pago VIP."""
    parts = query.data.split("_")
    action, username, target_user_id = parts[1], parts[2], int(parts[-1])

    if action == "accept":
        ok, dead_date = update_user_premium(target_user_id, days=32)
        if ok:
            await client.send_message(
                chat_id=target_user_id,
                text=(
                    "✅ *¡Pago Aceptado!*\n\n"
                    "🎉 *Felicidades*, su plan *VIP* ha sido activado correctamente.\n\n"
                    f"📅 *Válido hasta:* `{dead_date}`\n\n"
                    "Disfrute de todos los beneficios exclusivos. Si tiene alguna duda, no dude en contactarnos."
                ),
            )
            await query.message.edit(
                f"Pago aceptado ✅\n\nUsuario: @{username}\n\n🆔 {target_user_id}"
            )
        return

    await client.send_message(
        chat_id=target_user_id,
        text=(
            "⚠️ *Problema con su Pago*\n\n"
            "Lamentamos informarle que hemos detectado un inconveniente con su comprobante de pago.\n\n"
            "📋 *Posibles causas:*\n"
            "• Monto incorrecto\n• Captura no legible\n• Pago no verificado\n\n"
            "🆘 *¿Qué hacer?*\n"
            "Contacte a la administración a través del grupo oficial para resolver este problema:\n"
            f"👉 @{_env('GROUP_ID')}\n\nEstamos aquí para ayudarle."
        ),
    )
    await query.message.edit(f"Pago denegado ❌\n\nUsuario: @{username}\n\n🆔 {target_user_id}")


# ---------------------------------------------------------------------------
# Router principal de callbacks
# Orden: prefijos mas especificos primero (bulk_sub_ antes que sub_, etc.)
# ---------------------------------------------------------------------------
_CALLBACK_ROUTES = [
    ("bulk_sub_", handle_bulk_subtitle),
    ("bulk_end", handle_bulk_end),
    ("sub_", handle_subtitle),
    ("order_ready", handle_order_ready),
    ("order_not_found_", handle_order_not_found),
    ("order_404_", handle_order_404),
    ("remove_", handle_remove_post),
    ("close_", handle_close_search),
    ("info_", handle_info),
    ("become_vip", handle_become_vip),
    ("pay_edit_", handle_pay_edit),
    ("confirm_pay", handle_confirm_pay),
    ("send_pay_admin", handle_send_pay_admin),
    ("premium_", handle_premium),
]


@bot.on_callback_query()
async def query_manager(client: Client, query: CallbackQuery):
    """Despacha cada callback_data hacia su handler especifco."""
    for prefix, handler in _CALLBACK_ROUTES:
        if query.data == prefix or query.data.startswith(prefix):
            await handler(client, query)
            return
    logger.debug(f"Callback sin ruta conocida: {query.data}")
