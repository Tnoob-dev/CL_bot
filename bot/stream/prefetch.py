import asyncio
import logging
from typing import Set, Optional, Callable, Awaitable
from pyrogram import Client, raw
from pyrogram.file_id import FileId, PHOTO_TYPES
from .config import StreamConfig
from .cache import global_chunk_cache, global_coordinator, global_download_semaphore
from .tg_download import fetch_chunk, FileReferenceExpiredError

logger = logging.getLogger(__name__)


def _build_location(file_id: FileId):
    if file_id.file_type in PHOTO_TYPES:
        return raw.types.InputPhotoFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size or "y",
        )
    return raw.types.InputDocumentFileLocation(
        id=file_id.media_id,
        access_hash=file_id.access_hash,
        file_reference=file_id.file_reference,
        thumb_size=file_id.thumbnail_size or "",
    )


class PrefetchManager:
    def __init__(self):
        self.active_tasks: Set[asyncio.Task] = set()

    def start_prefetch(
        self, client: Client, dc_id: int, file_id_str: str, location, offset: int,
        start_part: int, part_count: int, chunk_size: int, file_size: int,
        message_id: Optional[int] = None,
        refresh_callback: Optional[Callable[[int], Awaitable[object]]] = None,
    ):
        task = asyncio.create_task(
            self._prefetch_worker(
                client, dc_id, file_id_str, location, offset, start_part, part_count,
                chunk_size, file_size, message_id, refresh_callback,
            )
        )
        self.active_tasks.add(task)
        task.add_done_callback(self.active_tasks.discard)

    async def _prefetch_worker(
        self, client: Client, dc_id: int, file_id_str: str, location, start_offset: int,
        start_part: int, part_count: int, chunk_size: int, file_size: int,
        message_id: Optional[int], refresh_callback,
    ):
        try:
            session = await client.get_session(dc_id, is_media=True)
            current_offset = start_offset

            for _ in range(start_part, start_part + part_count):
                if current_offset >= file_size:
                    break

                cached_chunk = await global_chunk_cache.get(file_id_str, current_offset)
                if not cached_chunk:
                    should_download = await global_coordinator.wait_or_start(file_id_str, current_offset)
                    if should_download:
                        try:
                            try:
                                chunk = await fetch_chunk(
                                    session, location, current_offset, chunk_size,
                                    StreamConfig.SLEEP_THRESHOLD, global_download_semaphore,
                                    StreamConfig.MAX_TELEGRAM_RETRIES, StreamConfig.RETRY_BASE_DELAY,
                                )
                            except FileReferenceExpiredError:
                                if message_id and refresh_callback:
                                    fresh_info = await refresh_callback(message_id)
                                    if fresh_info:
                                        file_id_str = fresh_info.file_id
                                        new_file_id = FileId.decode(file_id_str)
                                        location = _build_location(new_file_id)
                                        session = await client.get_session(dc_id, is_media=True)
                                        chunk = await fetch_chunk(
                                            session, location, current_offset, chunk_size,
                                            StreamConfig.SLEEP_THRESHOLD, global_download_semaphore,
                                            StreamConfig.MAX_TELEGRAM_RETRIES, StreamConfig.RETRY_BASE_DELAY,
                                        )
                                    else:
                                        chunk = None
                                else:
                                    chunk = None

                            if chunk:
                                await global_chunk_cache.put(file_id_str, current_offset, chunk)
                        finally:
                            await global_coordinator.finish(file_id_str, current_offset)
                current_offset += chunk_size
        except Exception as e:
            logger.debug(f"Prefetch abortado/fallo: {e}")

global_prefetch_manager = PrefetchManager()