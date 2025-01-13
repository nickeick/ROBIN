from aiohttp import web
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands, Interaction
from datetime import date, timedelta, datetime

IS_ENABLED = True

class HTTPCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.app = web.Application()
        self.app.add_routes([web.get('/button', self.handle)])
        self.mute = self.bot.get_channel(870946768928534528)

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    @tasks.loop(seconds=5)
    async def handle(self, request):
        # Button has been pressed
        if now() - self.bot.timestamp <= 5:
            self.mute.send('The Button has been pressed')

    @message_loop.before_loop
    async def before_message_loop(self):
        print("Waiting for the bot to be ready...")
        await self.bot.wait_until_ready()  # Ensure the bot is ready before starting the loop
        self.bot.timestamp = datetime.now()

    # async def start_app(self):
    #     web.run_app(self.app, port=8080)


async def setup(bot):
    await bot.add_cog(HTTPCog(bot))
    
    
    