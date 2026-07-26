"""Import/registration smoke test.

Proves the src/ package imports cleanly (all absolute/relative imports and
config-driven paths resolve) and that the composition root wires up every
handler. This is the guard that catches restructure breakage.
"""


def _handler_count(client) -> int:
    groups = getattr(client.dispatcher, "groups", {})
    return sum(len(handlers) for handlers in groups.values())


def test_package_imports():
    import cinemalibrarybot  # noqa: F401
    from cinemalibrarybot.config import settings

    assert settings.DATA_DIR.exists()


def test_composition_root_exposes_handlers():
    import cinemalibrarybot.__main__ as app

    for name in (
        "hello",
        "search_posts",
        "info_posts",
        "stream_handler",
        "profile_panel",
        "query_manager",
        "inline_answer",
    ):
        assert callable(getattr(app, name)), f"missing handler: {name}"


def test_register_handlers_wires_the_bot():
    import asyncio

    import cinemalibrarybot.__main__ as app

    # kurigram's add_handler schedules the actual registration as a task on the
    # client's event loop, so we install a fresh loop, register, then drive it
    # briefly to let those tasks run before counting.
    loop = asyncio.new_event_loop()
    app.bot.loop = loop
    try:
        app.register_handlers()
        loop.run_until_complete(asyncio.sleep(0.05))
    finally:
        loop.close()

    # 22 message handlers + 1 callback-query + 1 inline-query handler.
    assert _handler_count(app.bot) >= 24
