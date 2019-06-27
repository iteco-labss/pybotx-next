from typing import Callable

import pytest

from botx import BotXException, HandlersCollector
from botx.core import DEFAULT_HANDLER_BODY, FILE_HANDLER_NAME, SYSTEM_FILE_TRANSFER


class TestHandlersCollector:
    def test_handlers_adding(self, handler_factory):
        collector = HandlersCollector()
        collector.handler(handler_factory("sync"))
        collector.handler(handler_factory("sync"), command="sync2")
        assert len(collector.handlers) == 2

    def test_raising_exception_adding_duplicates(self, handler_factory):
        collector = HandlersCollector()

        with pytest.raises(BotXException):
            collector.handler(handler_factory("sync"))
            collector.handler(handler_factory("sync"))

    def test_handler_decorator(self, handler_factory):
        handler_body = "/handler"

        collector = HandlersCollector()

        handler_func = collector.handler(command=handler_body)(handler_factory("sync"))

        handler = collector.handlers["/handler"]
        assert handler.callback.callback == handler_func

    def test_raising_exception_in_handlers_merge(self, handler_factory):
        collector1 = HandlersCollector()
        collector1.handler(handler_factory("sync"))

        collector2 = HandlersCollector()
        collector2.handler(handler_factory("sync"))

        with pytest.raises(BotXException):
            collector1.include_handlers(collector2)

    def test_successful_merging(self, handler_factory):
        collector1 = HandlersCollector()
        collector1.handler(handler_factory("sync"), command="sync1")

        collector2 = HandlersCollector()
        collector2.handler(handler_factory("sync"), command="sync2")

        collector1.include_handlers(collector2)

    def test_raising_exception_with_name_errors(self):
        class ClassHandler:
            def __init__(self, f: Callable):
                self._f = f

            def __call__(self, *args, **kwargs):
                self._f(*args, **kwargs)

        collector = HandlersCollector()

        with pytest.raises(BotXException):

            @collector.handler
            @ClassHandler
            def handler1(*_):
                pass

        @collector.handler(name="class_handler")
        @ClassHandler
        def handler2(*_):
            pass

    def test_decorator_accept_many_commands(self, handler_factory):
        collector = HandlersCollector()
        command_names_list = [f"/cmd{i}" for i in range(1, 4)]

        collector.handler(handler_factory("sync"), commands=command_names_list)
        assert len(collector.handlers) == 3
        assert list(collector.handlers.keys()) == command_names_list

    def test_decorator_accept_body_with_commands(self, handler_factory):
        collector = HandlersCollector()
        command_names_list = [f"/cmd{i}" for i in range(4)]

        collector.handler(
            handler_factory("sync"), command="/cmd0", commands=["cmd1", "cmd2", "cmd3"]
        )
        assert len(collector.handlers) == 4
        assert set(collector.handlers.keys()) == set(command_names_list)

    def test_decorator_accept_list_of_commands_when_callback_is_none(self):
        collector = HandlersCollector()

        @collector.handler(commands=["info", "/information"])
        def get_processed_information(*_):
            pass

        assert "/info" in collector.handlers
        assert "/information" in collector.handlers


class TestHandlersCollectorNamingRules:
    def test_decorator_auto_naming(self):
        collector = HandlersCollector()

        @collector.handler
        def handler_function(*_):
            pass

        handler = collector.handlers[f"/handler-function"]
        assert handler.name == handler_function.__name__

    def test_naming_rules_for_common_commands(self, handler_factory):
        handler_name = "sync-handler"

        collector = HandlersCollector()
        function = handler_factory("sync")
        collector.handler(function, name=handler_name)

        handler = collector.handlers[f"/{handler_name}"]
        assert handler.callback.callback == function
        assert handler.name == handler_name
        assert handler.description == f"{handler_name.capitalize()} handler"

    def test_naming_rules_for_system_commands(self, handler_factory):
        system_command = "chat_created"
        handler_body = f"system:{system_command}"

        collector = HandlersCollector()
        function = handler_factory("sync")
        collector.system_command_handler(
            function, command=system_command, name=system_command
        )

        handler = collector.handlers[handler_body]
        assert handler.callback.callback == function
        assert handler.name == system_command
        assert handler.description == f"{system_command.capitalize()} handler"

    def test_many_slashes_are_replaced_by_one(self, handler_factory):
        collector = HandlersCollector()
        collector.handler(handler_factory("sync"), command="/////command")

        assert "/command" in collector.handlers


class TestHandlersCollectorExtraCommands:
    def test_system_command_attributes(self, handler_factory):
        system_command = "chat_created"
        handler_body = f"system:{system_command}"

        collector = HandlersCollector()
        collector.system_command_handler(
            handler_factory("sync"), command=system_command
        )

        handler = collector.handlers[handler_body]
        assert handler.system_command_handler

    def test_hidden_command_attributes(self, handler_factory):
        handler_body = "/cmd"

        collector = HandlersCollector()
        collector.hidden_command_handler(handler_factory("sync"), command=handler_body)

        handler = collector.handlers[handler_body]
        assert handler.exclude_from_status

    def test_file_handler_attributes(self, handler_factory):
        collector = HandlersCollector()
        collector.file_handler(handler_factory("sync"))

        handler = collector.handlers[SYSTEM_FILE_TRANSFER]
        assert handler.name == FILE_HANDLER_NAME
        assert handler.system_command_handler

    def test_default_handler_attributes(self, handler_factory):
        collector = HandlersCollector()
        collector.default_handler(handler_factory("sync"))

        handler = collector.handlers[DEFAULT_HANDLER_BODY]
        assert handler.use_as_default_handler

    def test_chat_created_attributes(self, handler_factory):
        collector = HandlersCollector()
        collector.chat_created_handler(handler_factory("sync"))

        handler = collector.handlers["system:chat_created"]
        assert handler.system_command_handler