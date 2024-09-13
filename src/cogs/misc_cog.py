from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction
from datetime import date, timedelta, datetime

IS_ENABLED = True

class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    @app_commands.command()
    async def whenjoin(self, interaction: Interaction):
        year = str(interaction.user.joined_at.year)
        month = str(interaction.user.joined_at.month)
        day = str(interaction.user.joined_at.day)
        hour = str(interaction.user.joined_at.hour)
        minute = str(interaction.user.joined_at.minute)
        second = str(interaction.user.joined_at.second)
        await interaction.response.send_message(month + '/' + day + '/' + year + ' (m/d/y) at ' + hour + ':' + minute + ':' + second + ' GMT')

    @app_commands.command()
    async def howlong(self, interaction: Interaction):
        diff = datetime.now() - interaction.user.joined_at
        await interaction.response.send_message('You have been in the Dojo for ' + str(diff.days) + ' days')

async def setup(bot):
    await bot.add_cog(MiscCog(bot))