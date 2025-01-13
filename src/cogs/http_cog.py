from aiohttp import web
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction
from datetime import date, timedelta, datetime

IS_ENABLED = True

class HTTPCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        app = web.Application()
        app.add_routes([web.get('/button', self.handle)])

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    async def handle(request):
        # Button has been pressed
        mute = self.bot.get_channel(870946768928534528)
        mute.send('The Button has been pressed')
        return web.Response(text='success')



async def setup(bot):
    await bot.add_cog(HTTPCog(bot))