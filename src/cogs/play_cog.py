from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from discord import Interaction, Guild

import discord

IS_ENABLED = True

class PlayView(discord.ui.View): # Create a class called PlayView that subclasses discord.ui.View
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green) # Create a button with the label "Yes" with color green
    async def yes_button_callback(self, interaction: Interaction, button):
        await interaction.user.add_roles(interaction.guild.get_role(757388821540372561)) # Add user to the "Yes" role
        if interaction.user.mention not in interaction.message.content: # If user is listed as a "yes" and presses "No," remove from "yes"
            await interaction.message.edit(content=interaction.message.content + '\n*' + interaction.user.mention + '*')
        await interaction.response.defer()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red) # Create a button with the label "No" with color red
    async def no_button_callback(self, interaction: Interaction, button):
        await interaction.user.add_roles(interaction.guild.get_role(757389176449531954)) # Add user to the "No" role
        if interaction.user.mention in interaction.message.content: # If user is listed as a "yes" and presses "No," remove from "yes"
            await interaction.message.edit(content=interaction.message.content.replace('\n*' + interaction.user.mention + '*', ''))
        await interaction.response.defer()

class PlayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.yes_role_id = 757388821540372561
        self.no_role_id = 757389176449531954

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    async def remove_roles(self, guild: Guild) -> None: # Remove all existing assignments of the YES and NO roles
        for id_type in [self.yes_role_id, self.no_role_id]:
            for member in guild.get_role(id_type).members:
                await member.remove_roles(guild.get_role(id_type))

    @app_commands.command(description= 'Ask people if they are interested in playing a game with you')
    async def play(self, interaction: Interaction, time: str=None):
        if time == None:
            time = ''
        await self.remove_roles(interaction.guild)
        mention = ""
        for role in interaction.guild.roles:
                if role.name.lower() == interaction.channel.name.replace('-', ' '):
                    mention = role.mention
        if mention == "":
            sent = await interaction.response.send_message('Dojo, is anyone interested in playing ' + time + "\n\nYesses:\n*" + interaction.user.mention + '*', view=PlayView(timeout=None))
        else:
            sent = await interaction.response.send_message(mention + 'is anyone interested in playing ' + time + "\n\nYesses:\n*" + interaction.user.mention + '*', view=PlayView(timeout=None))


async def setup(bot):
    await bot.add_cog(PlayCog(bot))