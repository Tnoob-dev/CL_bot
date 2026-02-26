from entry.entry import bot
from utils.functions import check_administration
from pyrogram.client import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from pyrogram.filters import command, private, document, video, photo
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from pathlib import Path
from typing import List
import os
import logging
import asyncio


# state for saving messages of files and other data
contrib_state = {}


# Logger
logger = logging.getLogger(__name__)


def init_user_contrib_state(user_id: int, massive_mode: bool = False) -> None:
    contrib_state[str(user_id)] = {
        "collecting": True,
        "massive_mode": massive_mode,
        "messages": [],
        "links": []
    }


def get_user_contrib_state(user_id: int) -> dict | None:
    return contrib_state.get(str(user_id))


@bot.on_message(command("contrib") & private)
async def contrib(client: Client, message: Message):

    user_id = message.from_user.id
    if str(user_id) not in contrib_state:
        init_user_contrib_state(user_id, massive_mode=True)

    await message.reply(
        "Modo masivo activado con las siguientes caracteristicas:\n\n"
        "```OwO\nModo collecion: activado\nSi lees esto eres gay```"
    )
    
    print(contrib_state)


# end_massive command, to end the complete task
@bot.on_message(command("contrib_end") & private)
async def contrib_end(client: Client, message: Message):

    user_id = message.from_user.id
    user_contrib_state = get_user_contrib_state(user_id)

    if not user_contrib_state or not user_contrib_state.get("massive_mode"):
        await message.reply("No se encuentra en modo masivo")
        return

    await message.reply("Mensajes enviados, gracias por su contribucion🔥")
    
    del contrib_state[str(user_id)]

# end command, forward all the messages to the backup channel
@bot.on_message(command("p_end") & private)
async def end_collection(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        user_contrib_state = get_user_contrib_state(user_id)

        if not user_contrib_state or not user_contrib_state.get("collecting"):
            await message.reply("Usted no se encuentra en el modo coleccion")
            return

        messages: List[int] = user_contrib_state["messages"]

        if not messages:
            await message.reply("No ha enviado ningun archivo en esta coleccion")
            del contrib_state[str(user_id)]
            return

        # forward messages to backup channel
        for message_id in messages:
            success = False # Flag: if True, means file sent to backup channel succesfully
        
            # while loop...
            while not success:
                try:
                    
                    # forwarding
                    await client.copy_message(chat_id=int(os.getenv("CONTRIBUTIONS")), from_chat_id=os.getenv("SENDER_BOT"), message_id=message_id)
                    success = True # change flag to True and go for the next file
                    
                except FloodWait as f: # if exists flood sleep bot the time estimated
                    
                    await asyncio.sleep(f.value)

       
        await message.reply("Mensaje(s) enviados al canal de aportes")

        # delete user from memory
        del contrib_state[str(user_id)]

    except PeerIdInvalid as e:
        await message.reply(
            f"Error -> **{e}**\n\nEste error tal vez es porque despues de inicializar el bot "
            "no puso algun mensaje random en el canal de aportes"
        )

# without commands, append messages id to user contrib_state message schema
# this will only wait for a document, video or photo
@bot.on_message(private & (document | video | photo))
async def collect_messages(client: Client, message: Message):
    try:
        if message.from_user and message.from_user.id is not None:
            user_id = message.from_user.id
            user_contrib_state = get_user_contrib_state(user_id)
            if user_contrib_state and user_contrib_state.get("collecting"):
                user_contrib_state["messages"].append(message.id)
    except AttributeError as error:
        logger.error(error)
