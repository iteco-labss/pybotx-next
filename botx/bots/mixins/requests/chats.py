"""Definition for mixin that defines BotX API methods."""

from typing import List, Optional
from uuid import UUID

from botx.bots.mixins.requests.call_protocol import BotXMethodCallProtocol
from botx.clients.methods.v3.chats.add_user import AddUser
from botx.clients.methods.v3.chats.create import Create
from botx.clients.methods.v3.chats.remove_user import RemoveUser
from botx.clients.methods.v3.chats.stealth_disable import StealthDisable
from botx.clients.methods.v3.chats.stealth_set import StealthSet
from botx.models import sending
from botx.models.enums import ChatTypes


class ChatsRequestsMixin:
    """Mixin that defines methods for communicating with BotX API."""

    async def create_chat(
        self: BotXMethodCallProtocol,
        credentials: sending.SendingCredentials,
        name: str,
        members: List[UUID],
        chat_type: ChatTypes,
        description: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> UUID:
        return await self.call_method(
            Create(
                name=name,
                description=description,
                members=members,
                avatar=avatar,
                chat_type=chat_type,
            ),
            credentials=credentials,
        )

    async def enable_stealth_mode(
        self: BotXMethodCallProtocol,
        credentials: sending.SendingCredentials,
        chat_id: UUID,
        disable_web: bool = False,
        burn_in: Optional[int] = None,
        expire_in: Optional[int] = None,
    ) -> None:
        """Enable stealth mode

        Arguments:
            credentials: credentials of chat.
            chat_id: id of chat to enable stealth,
            disable_web: disable web client for chat,
            burn_in: time to burn,
            expire_in: time to expire,
        """
        return await self.call_method(
            StealthSet(
                group_chat_id=chat_id,
                disable_web=disable_web,
                burn_in=burn_in,
                expire_in=expire_in,
            ),
            credentials=credentials,
        )

    async def disable_stealth_mode(
        self: BotXMethodCallProtocol,
        credentials: sending.SendingCredentials,
        chat_id: UUID,
    ) -> None:
        """Disable stealth mode

        Arguments:
            credentials: credentials of chat.
            chat_id: id of chat to disable stealth,
        """
        return await self.call_method(
            StealthDisable(group_chat_id=chat_id), credentials=credentials,
        )

    async def add_users(
        self: BotXMethodCallProtocol,
        credentials: sending.SendingCredentials,
        chat_id: UUID,
        user_huids: List[UUID],
    ) -> None:
        """Add users to chat.

        Arguments:
            credentials: credentials of chat.
            chat_id: id of chat to add users,
            user_huids: list of user's huids
        """
        return await self.call_method(
            AddUser(group_chat_id=chat_id, user_huids=user_huids),
            credentials=credentials,
        )

    async def remove_users(
        self: BotXMethodCallProtocol,
        credentials: sending.SendingCredentials,
        chat_id: UUID,
        user_huids: List[UUID],
    ) -> None:
        """Remove users from chat.

        Arguments:
            credentials: credentials of chat.
            chat_id: id of chat to remove users,
            user_huids: list of user's huids
        """
        return await self.call_method(
            RemoveUser(group_chat_id=chat_id, user_huids=user_huids),
            credentials=credentials,
        )
