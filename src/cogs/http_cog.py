from aiohttp import web
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands, Interaction
from datetime import date, timedelta, datetime

IS_ENABLED = True

# This cog exists for the purpose of handling the http server created in main
class HTTPCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.app = web.Application()
        self.app.add_routes([web.get('/button', self.handle)])

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    #@tasks.loop(seconds=5)
    async def handle(self, request):
        # Button has been pressed
        await self.bot.get_channel(870946768928534528).send('The Button has been pressed')
        return web.Response(text=f"Request Received")


async def setup(bot):
    await bot.add_cog(HTTPCog(bot))
    
    
    