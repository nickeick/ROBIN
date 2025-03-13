from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction

IS_ENABLED = True

class EloCog(commands.Cog):
    """
    A class that inherits from the commands.Cog class with the purpose of implementing the ELO calculating commands

    ...

    Attributes
    ----------
    bot: commands.Bot
        The Bot object representing the discord bot

    Methods
    -------
    cog_check(ctx)
        A default method in Cogs for determining the Cog's availability
    
    Commands
    --------
    elo(person1: int, person2: int)
        Calculates the expected chance that person 1 will beat person 2 given that they have their respective elos
    """
    def __init__(self, bot: commands.Bot):
        """
        Parameters
        ----------
        bot: commands.Bot
            The Bot object representing the discord bot
        """
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    @app_commands.command()
    async def elo(self, interaction: Interaction, person1: int, person2: int):
        """
        Calculates the expected chance that person 1 will beat person 2 given that they have their respective elos

        Parameters
        ----------
        person1: int
            Elo representing the person whose chances to win will be calculated
        person2: int
            Elo representing the person against person 1 whose chances of losing will be calculated
        """
        number = 1/(1 + 10 ** ((person2 - person1)/400))
        await interaction.response.send_message("There is a " + str(number * 100) + " percent chance that person 1 beats person 2")

async def setup(bot):
    await bot.add_cog(EloCog(bot))