from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction

IS_ENABLED = True

class TallyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def tallyho(self, interaction: Interaction, counter_name: str):
        command_exists = await self.bot.db_manager.does_command_exist(counter_name)
        counter_exists = await self.bot.db_manager.does_counter_exist(counter_name)

        if not counter_exists and not command_exists:
            await self.bot.db_manager.add_counter(counter_name)
            await interaction.response.send_message('Added counter ' + counter_name)
        elif counter_exists:
            await interaction.response.send_message(counter_name + ' is already a counter!')
        else:
            await interaction.response.send_message('A command exists with the name "' + counter_name + '"')


    # @tallyho.error
    # async def add_gang_error(self, interaction: Interaction, error: app_commands.AppCommandError):
    #     if isinstance(error, commands.MissingRole):
    #         await interaction.response.send_message('You do not have permission to use this command!', ephemeral=True) # Permissions error
    #     else:
    #         await interaction.response.send_message('An error has occured', ephemeral=True) # Every other error

async def setup(bot):
    await bot.add_cog(TallyCog(bot))