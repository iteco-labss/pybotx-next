from io import TextIOWrapper
from typing import Any, Dict, List, NoReturn, Optional, Union
from uuid import UUID

import aiohttp

from botx.botbase import BotBase
from botx.core.dispatcher import AsyncDispatcher

from .types import (
    BubbleElement,
    KeyboardElement,
    ResponseCommand,
    ResponseCommandResult,
    ResponseFile,
    ResponseNotification,
    ResponseNotificationResult,
    ResponseRecipientsEnum,
    Status,
    SyncID,
)


class AsyncBot(BotBase):
    bot_id: UUID
    bot_host: str
    _session: aiohttp.ClientSession

    def __init__(self):
        super().__init__()

        self._dispatcher = AsyncDispatcher()
        self._session = aiohttp.ClientSession()

    async def start(self) -> NoReturn:
        await self._dispatcher.start()

    async def stop(self) -> NoReturn:
        await self._dispatcher.shutdown()

    async def parse_status(self) -> Status:
        return await self._dispatcher.parse_request({}, request_type="status")

    async def parse_command(self, data: Dict[str, Any]) -> bool:
        return await self._dispatcher.parse_request(data, request_type="command")

    async def send_message(
        self,
        text: str,
        chat_id: Union[SyncID, UUID, List[UUID]],
        bot_id: UUID,
        host: str,
        *,
        recipients: Union[List[UUID], str] = ResponseRecipientsEnum.all,
        bubble: Optional[List[List[BubbleElement]]] = None,
        keyboard: Optional[List[List[KeyboardElement]]] = None,
    ) -> str:
        if not bubble:
            bubble = []
        if not keyboard:
            keyboard = []

        if isinstance(chat_id, SyncID):
            return await self._send_command_result(
                text=text,
                chat_id=chat_id,
                bot_id=bot_id,
                host=host,
                recipients=recipients,
                bubble=bubble,
                keyboard=keyboard,
            )
        elif isinstance(chat_id, UUID) or isinstance(chat_id, list):
            group_chat_ids = []
            if isinstance(chat_id, UUID):
                group_chat_ids.append(chat_id)
            elif isinstance(chat_id, list):
                group_chat_ids = chat_id

            return await self._send_notification_result(
                text=text,
                group_chat_ids=group_chat_ids,
                bot_id=bot_id,
                host=host,
                recipients=recipients,
                bubble=bubble,
                keyboard=keyboard,
            )

    async def _send_command_result(
        self,
        text: str,
        chat_id: SyncID,
        bot_id: UUID,
        host: str,
        recipients: Union[List[UUID], str],
        bubble: List[List[BubbleElement]],
        keyboard: List[List[KeyboardElement]],
    ) -> str:
        response_result = ResponseCommandResult(
            body=text, bubble=bubble, keyboard=keyboard
        )

        response = ResponseCommand(
            bot_id=bot_id,
            sync_id=str(chat_id),
            command_result=response_result,
            recipients=recipients,
        ).dict()

        async with self._session.post(
            self._url_command.format(host), json=response
        ) as resp:
            return await resp.text()

    async def _send_notification_result(
        self,
        text: str,
        group_chat_ids: List[UUID],
        bot_id: UUID,
        host: str,
        recipients: Union[List[UUID], str],
        bubble: List[List[BubbleElement]],
        keyboard: List[List[KeyboardElement]],
    ) -> str:
        response_result = ResponseNotificationResult(
            body=text, bubble=bubble, keyboard=keyboard
        )
        response = ResponseNotification(
            bot_id=bot_id,
            notification=response_result,
            group_chat_ids=group_chat_ids,
            recipients=recipients,
        ).to_dict()

        async with self._session.post(
            self._url_notification.format(host), json=response
        ) as resp:
            return await resp.text()

    async def send_file(
        self, file: TextIOWrapper, chat_id: Union[SyncID, UUID], bot_id: UUID, host: str
    ) -> str:
        response = ResponseFile(bot_id=bot_id, sync_id=chat_id, file=file).dict()

        async with self._session.post(
            self._url_notification.format(host), data=response
        ) as resp:
            return await resp.text()
