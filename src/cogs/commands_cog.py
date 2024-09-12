from discord.ext import commands
from discord.ext.commands import Context, Cog, Bot
from discord import app_commands, Interaction, Message

IS_ENABLED = True

class CommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def addcom(self, interaction: Interaction, command_name: str, output: str):
        await self.bot.db_manager.add_command(command_name, output, interaction.user.name)
        await interaction.response.send_message('Made command ' + command_name + ' to send ' + output)

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def delcom(self, interaction: Interaction, command_name: str):
        await self.bot.db_manager.delete_command(command_name)
        await interaction.response.send_message('Deleted ' + command_name)

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def editcom(self, interaction, command_name: str, current_output: str, new_output: str):
        exists = await self.bot.db_manager.does_command_exist(command_name, current_output)
        if exists:
            await self.bot.db_manager.delete_command_output(command, current_output)
            await self.bot.db_manager.add_command(command_name, new_output, interaction.user.name)
            await interaction.response.send_message(command_name + " has been updated")
        else:
            await interaction.response.send_message(command_name + " failed to update because command or output does not exist")

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def commands(self, interaction):
        comms = await self.bot.db_manager.get_all_commands()
        for comm in list(set(comms)):
            await interaction.channel.send(comm[0])
        await interaction.response.defer()



async def setup(bot):
    await bot.add_cog(CommandsCog(bot))