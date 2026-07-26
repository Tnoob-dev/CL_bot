from pyrogram.client import Client
import logging
import tgcrypto  # noqa: F401  (imported for its side effect: MTProto crypto backend)

from cinemalibrarybot.config import settings

# Logger
logger = logging.getLogger(__name__)

#######################
# BOT INITIALIZATION  #
#######################

# The .env is already loaded by cinemalibrarybot.config on import. The session
# file is stored under the runtime data directory as <DATA_DIR>/<NAME>.session.
bot: Client = Client(
    name=settings.session_path,
    api_id=settings.TELEGRAM_API_ID,
    api_hash=settings.TELEGRAM_API_HASH,
    bot_token=settings.TELEGRAM_BOT_TOKEN,
)
