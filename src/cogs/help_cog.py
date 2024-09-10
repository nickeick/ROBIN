from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

IS_ENABLED = True

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

async def setup(bot):
    await bot.add_cog(HelpCog(bot))