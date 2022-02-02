import os
from http import HTTPStatus
from typing import List
from uuid import UUID

import pytest
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from botx import (
    Bot,
    BotAccountWithSecret,
    HandlerCollector,
    IncomingMessage,
    UnknownBotAccountError,
    build_bot_disabled_response,
    build_command_accepted_response,
)
from botx.logger import logger  # TODO: Implement separate logger here


def build_bot_accounts_from_env() -> List[BotAccountWithSecret]:
    load_dotenv()

    bot_accounts = []
    for raw_credentials in os.environ["BOT_CREDENTIALS"].split(","):
        host, secret_key, raw_bot_id = raw_credentials.replace("|", "@").split("@")
        bot_accounts.append(
            BotAccountWithSecret(
                id=UUID(raw_bot_id),
                host=host,
                secret_key=secret_key,
            ),
        )

    return bot_accounts


# - pybotx -
collector = HandlerCollector()


@collector.command("/debug", description="Simple debug command")
async def debug_handler(message: IncomingMessage, bot: Bot) -> None:
    await bot.answer_message("Hi!")


bot = Bot(collectors=[collector], bot_accounts=build_bot_accounts_from_env())


# - Starlette -
async def command_handler(request: Request) -> JSONResponse:
    try:
        bot.async_execute_raw_bot_command(await request.json())
    except ValueError:
        error_label = "Bot command validation error"
        logger.exception(error_label)

        return JSONResponse(
            build_bot_disabled_response(error_label),
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )
    except UnknownBotAccountError as exc:
        error_label = f"No credentials for bot {exc.bot_id}"
        logger.warning(error_label)

        return JSONResponse(
            build_bot_disabled_response(error_label),
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )

    return JSONResponse(
        build_command_accepted_response(),
        status_code=HTTPStatus.ACCEPTED,
    )


async def status_handler(request: Request) -> JSONResponse:
    status = await bot.raw_get_status(dict(request.query_params))
    return JSONResponse(status)


async def callback_handler(request: Request) -> JSONResponse:
    bot.set_raw_botx_method_result(await request.json())
    return JSONResponse(
        build_command_accepted_response(),
        status_code=HTTPStatus.ACCEPTED,
    )


app = Starlette(
    routes=[
        Route("/command", endpoint=command_handler, methods=["POST"]),
        Route("/status", endpoint=status_handler, methods=["GET"]),
        Route("/notification/callback", endpoint=callback_handler, methods=["POST"]),
    ],
    on_startup=[bot.startup],
    on_shutdown=[bot.shutdown],
)


# - tests -
@pytest.fixture
@pytest.mark.mock_authorization
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def bot_id() -> UUID:
    bot_accounts_list = list(bot.bot_accounts)
    return bot_accounts_list[0].id


def test__web_app__bot_status(
    bot_id: UUID,
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/status",
        params={
            "bot_id": str(bot_id),
            "chat_type": "chat",
            "user_huid": "f16cdc5f-6366-5552-9ecd-c36290ab3d11",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "result": {
            "commands": [
                {
                    "body": "/debug",
                    "description": "Simple debug command",
                    "name": "/debug",
                },
            ],
            "enabled": True,
            "status_message": "Bot is working",
        },
        "status": "ok",
    }


def test__web_app__bot_command(
    bot_id: UUID,
    test_client: TestClient,
) -> None:
    payload = {
        "bot_id": str(bot_id),
        "command": {
            "body": "/hello",
            "command_type": "user",
            "data": {},
            "metadata": {},
        },
        "attachments": [],
        "async_files": [],
        "entities": [],
        "source_sync_id": None,
        "sync_id": "6f40a492-4b5f-54f3-87ee-77126d825b51",
        "from": {
            "ad_domain": None,
            "ad_login": None,
            "app_version": None,
            "chat_type": "chat",
            "device": None,
            "device_meta": {
                "permissions": None,
                "pushes": False,
                "timezone": "Europe/Moscow",
            },
            "device_software": None,
            "group_chat_id": "30dc1980-643a-00ad-37fc-7cc10d74e935",
            "host": "cts.example.com",
            "is_admin": True,
            "is_creator": True,
            "locale": "en",
            "manufacturer": None,
            "platform": None,
            "platform_package_id": None,
            "user_huid": "f16cdc5f-6366-5552-9ecd-c36290ab3d11",
            "username": None,
        },
        "proto_version": 4,
    }
    response = test_client.post(
        "/command",
        json=payload,
    )

    assert response.status_code == HTTPStatus.ACCEPTED


def test__web_app__unknown_bot_response(
    test_client: TestClient,
) -> None:
    payload = {
        "bot_id": "123e4567-e89b-12d3-a456-426655440000",
        "command": {
            "body": "/hello",
            "command_type": "user",
            "data": {},
            "metadata": {},
        },
        "attachments": [],
        "async_files": [],
        "entities": [],
        "source_sync_id": None,
        "sync_id": "6f40a492-4b5f-54f3-87ee-77126d825b51",
        "from": {
            "ad_domain": None,
            "ad_login": None,
            "app_version": None,
            "chat_type": "chat",
            "device": None,
            "device_meta": {
                "permissions": None,
                "pushes": False,
                "timezone": "Europe/Moscow",
            },
            "device_software": None,
            "group_chat_id": "30dc1980-643a-00ad-37fc-7cc10d74e935",
            "host": "cts.example.com",
            "is_admin": True,
            "is_creator": True,
            "locale": "en",
            "manufacturer": None,
            "platform": None,
            "platform_package_id": None,
            "user_huid": "f16cdc5f-6366-5552-9ecd-c36290ab3d11",
            "username": None,
        },
        "proto_version": 4,
    }
    response = test_client.post(
        "/command",
        json=payload,
    )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test__web_app__disabled_bot_response(
    test_client: TestClient,
) -> None:
    response = test_client.post(
        "/command",
        json={"incorrect": "request"},
    )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {
        "error_data": {"status_message": "Bot command validation error"},
        "errors": [],
        "reason": "bot_disabled",
    }
