# This example covers advanced startup options and uses some real world examples for why you may need them.

import asyncio
import logging
import logging.handlers
import os

from typing import List, Optional
from dotenv import load_dotenv

import sqlite3
import discord
from discord.ext.commands import Context
from discord.ext import commands
from aiohttp import ClientSession, web

from threading import Thread
from datetime import datetime

from database_manager import DatabaseManager


class CustomBot(commands.Bot):
    def __init__(
        self,
        *args,
        db_manager: DatabaseManager,
        web_client: ClientSession,
        testing_guild_id: Optional[int] = None,
        timestamp: datetime,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.db_manager = db_manager
        self.timestamp = timestamp



    async def setup_hook(self) -> None:

        # here, we are loading extensions prior to sync to ensure we are syncing interactions defined in those extensions.

        for filename in os.listdir('src/cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded: cogs.{filename[:-3]}')


        # In overriding setup hook,
        # we can do things that require a bot prior to starting to process events from the websocket.
        # In this case, we are using this to ensure that once we are connected, we sync for the testing guild.
        # You should not do this for every guild or for global sync, those should only be synced when changes happen.
        if self.testing_guild_id:
            guild = discord.Object(self.testing_guild_id)
            # We'll copy in the global commands to test with:
            self.tree.copy_global_to(guild=guild)
            # followed by syncing to the testing guild.
            await self.tree.sync(guild=guild)

        # This would also be a good place to connect to our database and
        # load anything that should be in memory prior to handling events.

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        # edit the existing event loop
        # httpcog = self.get_cog('HTTPCog')
        # if httpcog is not None:
        #     print("Endpoint opened")
        #     self.loop.create_task(httpcog.start_app())
        

    async def close(self):
        await super().close()
        await self.db_manager.close()

timestamp = datetime.now()
def update_timestamp(request):
        # Button has been pressed
        timestamp = datetime.now()

def start_aiohttp_server():
    app = web.Application()
    app.router.add_get('/button', update_timestamp)
    web.run_app(app, port=8080)

thread = Thread(target=start_aiohttp_server(), daemon=True)
thread.start()

async def main():

    # Setup the bot and db stuff
    load_dotenv()
    DATABASE_PATH = os.getenv('DATABASE_PATH')
    TEST_GUILD = os.getenv('TEST_GUILD')

    # When taking over how the bot process is run, you become responsible for a few additional things.

    # 1. logging

    # for this example, we're going to set up a rotating file logger.
    # for more info on setting up logging,
    # see https://discordpy.readthedocs.io/en/latest/logging.html and https://docs.python.org/3/howto/logging.html

    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    intents.voice_states = True
    intents.message_content = True

    # Alternatively, you could use:
    # discord.utils.setup_logging(handler=handler, root=False)

    async with ClientSession() as our_client, DatabaseManager(DATABASE_PATH) as db_manager:
        # 2. We become responsible for starting the bot.
            async with CustomBot(commands.when_mentioned, db_manager=db_manager, web_client=our_client, intents=intents, testing_guild_id=TEST_GUILD, timestamp=timestamp) as bot:

                await bot.start(os.getenv('TOKEN'))



# For most use cases, after defining what needs to run, we can just tell asyncio to run it:
asyncio.run(main())

