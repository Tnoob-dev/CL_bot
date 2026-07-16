from entry.entry import bot
from utils.db_reqs import get_user, delete_post, update_user_premium
from pyrogram.client import Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import WebpageMediaEmpty
from pyrogram.filters import private, photo
from utils.functions import check_administration, get_clicked_button_text, download_image, translate_synopsis, translate_title, translate_words, get_message_info
from utils.search_subts import download_subs
from utils.create_paths import create_subtitles_dl_path
from utils.movie_search import get_info_by_id
from pathlib import Path
import os
import logging

# Logger 
logger = logging.getLogger(__name__)

last_user_photo = {}

# handler to listen when a user sends a pic
@bot.on_message(private & photo, group=0)
async def save_user_photo(client: Client, message: Message):
    user_id = message.from_user.id
    last_user_photo[user_id] = message.photo.file_id

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
    
    #  not confuse with order_404
    # order_not_found its for when an order its not founded after the user asked and the bot searched for it
    # order_404 its for when the admin can't find the order and the user needs to be notified
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
                        [InlineKeyboardButton("🎬Canal de pedidos🎬", url=f"https://t.me/{os.getenv("ORDERS_ID")}")]
                    ]))
            
            await client.send_message(
                chat_id=os.getenv("ORDERS_ID"),
                text=(
                    f"🎟Nueva solicitud:\n\n"
                    f"**Pedido**: __{user_message}__\n"
                    f"**Usuario**: {query.from_user.mention} (__{user_id_cb}__)\n"
                    f"**Link**: https://t.me/{group_chat}/{message_replied_id}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🫡Orden Lista🫡", callback_data=f"order_ready_{message_replied_id}"),
                            InlineKeyboardButton("❌No encontrado❌", callback_data=f"order_404_{message_replied_id}")
                        ]
                    ]
                ))

            await query.answer("Tu orden fue enviada a los administradores ✅", show_alert=False)
        except Exception as e:
            logger.error(f"Error en order_not_found -> {e}")
            await query.answer("Ocurrió un error al reenviar tu orden.", show_alert=True)

    elif query.data.startswith("order_404_"):

        if check_administration(query):
            splitted_query_data = query.data.split("_")
            msg_id = int(splitted_query_data[-1])

            await client.send_message(chat_id=os.getenv("GROUP_ID"), reply_to_message_id=msg_id, text="Lo sentimos, no encontramos su pedido.")

            await query.message.delete()

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
    
    elif query.data.startswith("edit_"):
        
        message_info = await get_message_info(client, query.data.split("_")[-1])
        
        match query.data.split("_")[1]:
            case "text":
                print(message_info.text)
            case "btns":
                print("botones")
                
    elif query.data == "become_vip":
        
        text = f"""
Coste del plan VIP 💎: 
    - 💳 Tarjeta ➡️ {os.getenv('VIP_PRICE_CUP')} CUP
    - 💳 Tarjeta ➡️ {os.getenv('VIP_PRICE_MLC')} MLC
    - 💵 USD/PayPal/Zelle ➡️ {os.getenv('VIP_PRICE_USD')} USD
    - 📱 Saldo Movil ➡️ {os.getenv('VIP_PRICE_CUP')} CUP

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
            [InlineKeyboardButton("💵 PayPal", callback_data="pay_edit_paypal")],
            [InlineKeyboardButton("⚡️ Zelle", callback_data="pay_edit_zelle")]
        ]
        
        await query.message.delete()
        
        await query.message.reply(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    elif query.data.startswith("pay_edit_"):
        
        data = query.data
        
        if data.endswith("metro"):
            await query.message.edit(
                text=f"No debe recortar la foto, envie con fecha y hora presentes.\n\nSolo toque los numeros para copiar:\n\n 💳Tarjeta: <code>{os.getenv('CUP_CARD')}</code>\n📱Confirmar: <code>{os.getenv('MOBILE')}</code>\n\nPresione en Confirmar✅ para enviar su evidencia de pago a los admins", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar✅", callback_data="confirm_pay")]]))
        
        elif data.endswith("bpa_cup"):
            await query.message.edit(
                text=f"No debe recortar la foto, envie con fecha y hora presentes.\n\nSolo toque los numeros para copiar:\n\n 💳Tarjeta: <code>{os.getenv('CUP_CARD2')}</code>\n📱Confirmar: <code>{os.getenv('MOBILE')}</code>\n\nPresione en Confirmar✅ para enviar su evidencia de pago a los admins", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar✅", callback_data="confirm_pay")]]))
        
        elif data.endswith("bpa_mlc"):
            await query.message.edit(
                text=f"No debe recortar la foto, envie con fecha y hora presentes.\n\nSolo toque los numeros para copiar:\n\n 💳Tarjeta: <code>{os.getenv('MLC_CARD')}</code>\n📱Confirmar: <code>{os.getenv('MOBILE')}</code>\n\nPresione en Confirmar✅ para enviar su evidencia de pago a los admins", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar✅", callback_data="confirm_pay")]]))
      
        elif data.endswith("enzona"):
            await query.message.delete()
            await query.message.reply_photo(
                photo=Path.cwd() / Path("assets") / Path("enzona_pic.jpg"), 
                caption="No debe recortar la foto, envie con fecha y hora presentes.\n\nPresione en Confirmar✅ para enviar su evidencia de pago a los admins",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar✅", callback_data="confirm_pay")]])
                )
        
        elif data.endswith("paypal"):
            await query.message.edit("❌No tenemos disponibilidad para esta funcion aun, sentimos las molestias😢")
        
        elif data.endswith("zelle"):
            await query.message.edit("❌No tenemos disponibilidad para esta funcion aun, sentimos las molestias😢")
       
        elif data.endswith("sm"):
            await query.message.edit(
                text=f"No debe recortar la foto, envie con fecha y hora presentes.\n\nSolo toque los numeros para copiar:\n\n 📱Movil: <code>{os.getenv('MOBILE')}</code>\n\nPresione en Confirmar✅ para enviar su evidencia de pago a los admins", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar✅", callback_data="confirm_pay")]]))
    
    elif query.data == "confirm_pay":
        
        await query.message.delete()
        
        await query.message.reply(
        text="📸 *Envíe su captura de pago ahora.*\n\nUna vez enviada la imagen, presione el botón de abajo para finalizar:", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar✅", callback_data="send_pay_admin")]]))
        
    elif query.data == "send_pay_admin":
        
        user_id = query.from_user.id
        
        photo_id = last_user_photo.get(user_id)
    
        if photo_id:
            await query.answer("✅ Procesando comprobante...")
            user_info = query.from_user
            caption = (
                f"🔔 Nuevo comprobante\n"
                f"👤 @{user_info.username or 'Sin username'}\n"
                f"🆔 `{user_id}`"
            )
        
            buttons = [
                [
                    InlineKeyboardButton("Aceptar Pago✅", callback_data=f"premium_accept_{user_id}"),
                    InlineKeyboardButton("Declinar Pago❌", callback_data=f"premium_decline_{user_id}")
                ]
            ]
            
            await client.send_photo(
                chat_id=int(os.getenv("PAY_GROUP")),
                photo=photo_id,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            
            del last_user_photo[user_id]
            
            await query.message.edit_text("✅ *¡Comprobante enviado a los administradores!*")
        else:
            await query.answer("⚠️ Primero envía la captura de pago.", show_alert=True)
    
    elif query.data.startswith("premium_"):
        
        data = query.data
        splitted_data = data.split("_")
        
        if splitted_data[1] == "accept":
            boolean, dead_date = update_user_premium(int(splitted_data[-1]), days=30)
            
            if boolean:
                await client.send_message(
                    chat_id=int(splitted_data[-1]),
                    text=(
                        "✅ *¡Pago Aceptado!*\n\n"
                        "🎉 *Felicidades*, su plan *VIP* ha sido activado correctamente.\n\n"
                        "📅 *Válido hasta:* `{dead_date}`\n\n"
                        "Disfrute de todos los beneficios exclusivos. Si tiene alguna duda, no dude en contactarnos.".format(dead_date=dead_date)
                    )
                )
        else:
            await client.send_message(
                chat_id=int(splitted_data[-1]),
                text=(
                    "⚠️ *Problema con su Pago*\n\n"
                    "Lamentamos informarle que hemos detectado un inconveniente con su comprobante de pago.\n\n"
                    "📋 *Posibles causas:*\n"
                    "• Monto incorrecto\n"
                    "• Captura no legible\n"
                    "• Pago no verificado\n\n"
                    "🆘 *¿Qué hacer?*\n"
                    "Contacte a la administración a través del grupo oficial para resolver este problema:\n"
                    "👉 @{group_id}\n\n"
                    "Estamos aquí para ayudarle.".format(
                        group_id=os.getenv('GROUP_ID')
                    )
                )
            )
            
        await query.message.delete()