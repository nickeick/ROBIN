from discord.ext import commands
from discord.ext.commands import Context, Cog, Bot
from discord import app_commands, Interaction, Message

IS_ENABLED = True

class CommandsCog(commands.Cog):
    """
    A class that inherits from the commands.Cog class with the purpose of implementing Server Admin-created simple text response commands

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
    addcom(command_name: str, output: str)
        Creates a new command or adds to an existing command in the database with a text output
    delcom(command_name: str)
        Removes all text output for one command
    editcom(command_name: str, current_output: str, new_output: str)
        Changes one specific output for one command to a different text
    commands()
        Sends a list of all text response command names
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
    @app_commands.checks.has_role(578065628691431435)
    async def addcom(self, interaction: Interaction, command_name: str, output: str):
        """
        Creates a new command or adds to an existing command in the database with a text output

        Checks
        ------
        has_role
            Checks for the Server Admin role

        Parameters
        ----------
        command_name: str
            Name of the command that will be added
        output: str
            Text that will be sent on the invocation of the command
        """
        await self.bot.db_manager.add_command(command_name, output, interaction.user.name)
        await interaction.response.send_message('Made command ' + command_name + ' to send ' + output)

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def delcom(self, interaction: Interaction, command_name: str):
        """
        Removes all text output for one command

        Checks
        ------
        has_role
            Checks for the Server Admin role

        Parameters
        ----------
        command_name: str
            Name of the command that will be removed
        """
        await self.bot.db_manager.delete_command(command_name)
        await interaction.response.send_message('Deleted ' + command_name)

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def editcom(self, interaction, command_name: str, current_output: str, new_output: str):
        """
        Changes one specific output for one command to a different text

        Checks
        ------
        has_role
            Checks for the Server Admin role

        Parameters
        ----------
        command_name: str
            Name of the command that will be edited
        current_output: str
            Output text of this command that will be replaced
        new_output: str
            Output text that will replace the current output
        """
        exists = await self.bot.db_manager.does_output_exist(command_name, current_output)
        if exists:
            await self.bot.db_manager.delete_command_output(command_name, current_output)
            await self.bot.db_manager.add_command(command_name, new_output, interaction.user.name)
            await interaction.response.send_message(command_name + " has been updated")
        else:
            await interaction.response.send_message(command_name + " failed to update because command or output does not exist")

    @app_commands.command()
    @app_commands.checks.has_role(578065628691431435)
    async def commands(self, interaction):
        """
        Sends a list of all text response command names

        Checks
        ------
        has_role
            Checks for the Server Admin role
        """
        comms = await self.bot.db_manager.get_all_commands()
        for comm in list(set(comms)):
            await interaction.channel.send(comm[0])
        await interaction.response.defer()



async def setup(bot):
    await bot.add_cog(CommandsCog(bot))