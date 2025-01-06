from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction

IS_ENABLED = True

class EloCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    @app_commands.command()
    async def elo(self, interaction: Interaction, person1: int, person2: int):
        number = 1/(1 + 10 ** ((person2 - person1)/400))
        await interaction.response.send_message("There is a " + str(number) + " percent chance that person 1 beats person 2")

async def setup(bot):
    await bot.add_cog(EloCog(bot))