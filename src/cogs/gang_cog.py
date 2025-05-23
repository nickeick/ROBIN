from typing import List
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction, PermissionOverwrite
import discord

IS_ENABLED = True

# I am leaving the old view for posterity's sake
class RoleManager(discord.ui.View):
        def __init__(self, role_id):
            super().__init__(timeout=None)
            self.role_id = role_id

        @discord.ui.button(label="Join", style=discord.ButtonStyle.green, custom_id='role_manager:green')
        async def join_button_callback(self, interaction: Interaction, button):
            if interaction.guild.get_role(self.role_id) in interaction.user.roles:
                await interaction.response.send_message('You are already in ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)
            else:
                await interaction.user.add_roles(interaction.guild.get_role(self.role_id))
                await interaction.response.send_message('Added to ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)

        @discord.ui.button(label="Leave", style=discord.ButtonStyle.red, custom_id='role_manager:red')
        async def leave_button_callback(self, interaction: Interaction, button):
            if interaction.guild.get_role(self.role_id) in interaction.user.roles:
                await interaction.user.remove_roles(interaction.guild.get_role(self.role_id))
                await interaction.response.send_message('Left ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)
            else:
                await interaction.response.send_message('You are not in ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)

class PersistentView(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)

        join_button = DynamicJoinButton(role_id=role_id)
        leave_button = DynamicLeaveButton(role_id=role_id)
        self.add_item(join_button)
        self.add_item(leave_button)

### -- DYNAMIC BUTTONS --
class DynamicJoinButton(discord.ui.Button):
    def __init__(self, role_id: int) -> None:
        super().__init__()
        self.label = 'Join'
        self.style = discord.ButtonStyle.green
        self.custom_id=f'button:join:role:{role_id}'
        self.role_id: int = role_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild.get_role(self.role_id) in interaction.user.roles:
            await interaction.response.send_message('You are already in ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)
        else:
            await interaction.user.add_roles(interaction.guild.get_role(self.role_id))
            await interaction.response.send_message('Added to ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)

class DynamicLeaveButton(discord.ui.Button):
    def __init__(self, role_id: int) -> None:
        super().__init__()
        self.label = 'Leave'
        self.style = discord.ButtonStyle.red
        self.custom_id=f'button:leave:role:{role_id}'
        self.role_id: int = role_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild.get_role(self.role_id) in interaction.user.roles:
            await interaction.user.remove_roles(interaction.guild.get_role(self.role_id))
            await interaction.response.send_message('Left ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)
        else:
            await interaction.response.send_message('You are not in ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)

class GangCog(commands.Cog):
    """
    A class that inherits from the commands.Cog class with the purpose of implementing the Server Brain Cell and its functions.

    ...

    Attributes
    ----------
    bot: commands.Bot
        The Bot object representing the discord bot
    all_gang_ids: List[int]
        A list of all gang role ids that are taken from the database

    Methods
    -------
    cog_check(ctx)
        A default method in Cogs for determining the Cog's availability
    
    Commands
    --------
    add_gang(gang_name: str)
        An admin is allowed to make a new gang which adds a role, channel, and database entry
    join_gang(gang_name: str)
        Allows a user to join a gang which includes a role and its associated channel
    leave_gang(gang_name: str)
        Allows a user to leave a gang
    generate_gangs_list()
        An admin is allowed to print a list of gang name text that each have 'join' and 'leave' buttons that add users to the connected gang
    """
    def __init__(self, bot: commands.Bot, all_gang_ids):
        self.bot = bot
        self.bot_test = 582060071052115978
        self.join_roles_here = 1027646452371046430
        for gang_id in all_gang_ids:
            self.bot.add_view(PersistentView(role_id=gang_id[0]))

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @app_commands.checks.has_role(578065628691431435) # If has admin role
    @app_commands.command(name = 'makegang', description='Dont add gang to the end') 
    async def add_gang(self, interaction: Interaction, gang_name: str):
        gang_channels = [] 
        for channel in interaction.guild.channels: # Get a list of every gang
            if len(channel.name) > 5:
                if channel.name[-5:].lower() == '-gang':
                    gang_channels.append(channel.name)
        
        for channel in gang_channels: # Check if gang already exists, exit command if so
            if channel.lower == gang_name.lower() + '-gang':
                sent = await interaction.response.send_message('Gang already exists!', ephemeral=True)
                return

        activities = interaction.guild.get_channel(579796688420732949) # Gang Activities category
        new_role = await interaction.guild.create_role(name=gang_name + " Gang") # Create New Role
        overwrites = {interaction.guild.default_role: PermissionOverwrite(read_messages=False),
                            new_role: PermissionOverwrite(read_messages=True)}
        channel_created = await interaction.guild.create_text_channel(gang_name + '-gang', overwrites=overwrites, category=activities, position=0) # Create New Text Channel

        gang_channels.append(gang_name.lower()) # Get the alphabetic postion the channel should be put at
        gang_channels.sort()
        put_after_channel_str = ''
        if (gang_channels.index(gang_name.lower()) > 0):
            put_after_channel_str = gang_channels[gang_channels.index(gang_name.lower())-1]
            for channel in interaction.guild.channels:
                if channel.name == put_after_channel_str:
                    await channel_created.move(after=channel)

        await self.bot.db_manager.add_gang(new_role.id, new_role.name.lower().strip())
                    
        sent = await interaction.response.send_message(gang_name + ' Gang has been made! Type "/join ' + gang_name + ' Gang" to join', ephemeral=True)

    @add_gang.error
    async def add_gang_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message('You do not have permission to use this command!', ephemeral=True) # Permissions error
        else:
            await interaction.response.send_message('An error has occured' + error, ephemeral=True) # Every other error

    # Attempt autocomplete
    async def gang_autocomplete(self, interaction: Interaction, current: str) -> List[app_commands.Choice[str]]:
        gang_roles = []
        for role in interaction.guild.roles: # Get a list of every gang role
            if len(role.name) > 4:
                if role.name[-4:].lower().strip() == 'gang':
                    gang_roles.append(role.name)
        
            return [ 
                app_commands.Choice(name=gang_name, value = gang_name)
                for gang_name in gang_roles if current.lower() in gang_name.lower()
            ]
    
    @app_commands.command(name = 'join', description='Join a gang') # Join gang
    @app_commands.autocomplete(gang_name=gang_autocomplete) 
    async def join_gang(self, interaction: Interaction, gang_name: str):
        role_names = list(map(lambda x : x.name.lower().strip(), interaction.guild.roles))
        if (gang_name.lower().strip() not in role_names):
            await interaction.response.send_message('Gang does not exist!', ephemeral=True)
            return
        movie_night_addendum = ''
        for role in interaction.guild.roles:
            if role.name.lower() in gang_name.strip().lower():
                if  ('gang' not in role.name.lower()) or role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy" or role.name == 'The Server Brain Cell' or role.name == 'Server Genius' or role.name == 'Pingcord':
                    await interaction.response.send_message('You cannot join this role: ' + role.name, ephemeral=True) # Dont let people join not gang roles
                else:
                    await interaction.user.add_roles(role)
                    if role.name == 'Movie Night Gang': # Warn people of nsw in movie night gang
                        movie_night_addendum = 'This is an NSFW gang \n' # This still might not work
                    await interaction.response.send_message(movie_night_addendum + 'Added ' + interaction.user.display_name + ' to ' + role.name, ephemeral=True)

    @app_commands.command(name = 'leave', description='Leave a gang') # Remove from gang
    @app_commands.autocomplete(gang_name=gang_autocomplete) 
    async def leave_gang(self, interaction: Interaction, gang_name: str):
        role_names = list(map(lambda x : x.name.lower().strip(), interaction.guild.roles))
        if (gang_name.lower().strip() not in role_names):
            await interaction.response.send_message('Gang does not exist!', ephemeral=True)
        for role in interaction.guild.roles:
            if role.name.lower() in gang_name.strip().lower():
                if ('gang' not in role.name.lower()) or role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy":
                    await interaction.response.send_message('You cannot leave this role: ' + role.name, ephemeral=True) # Dont let people leave not gang roles
                else:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message('Removed ' + interaction.user.display_name + ' from ' + role.name, ephemeral=True)

    @app_commands.checks.has_role(578065628691431435) #If has admin role
    @app_commands.command(name='generategangs')
    async def generate_gang_list(self, interaction: Interaction): #Gang List Maker ONLY TEST IN SPECIFIC CHANNEL IT WILL DELETE STUFF
        if interaction.channel_id != self.join_roles_here and interaction.channel_id != self.bot_test:
            await interaction.response.send_message('This command can only be used in #join-roles-here!', ephemeral=True)
            return
        
        await self.bot.db_manager.make_gang_table()
        
        # THIS DELETES THE HISTORY OF THE CHANNEL
        if(interaction.channel_id == self.join_roles_here):
            async for message in interaction.guild.get_channel(self.join_roles_here).history(limit=None):
                try:
                    await message.delete()
                except discord.Forbidden:
                    interaction.response.send_message('Could not delete message - No Permissions')
                except discord.HTTPException as e:
                    interaction.response.send_message('Could not delete message - {e}')

        gang_roles = {}
        for role in interaction.guild.roles: # Get a list of every gang role
            if len(role.name) > 4:
                if role.name[-4:].lower().strip() == 'gang':
                    if (role.id != 636466520591040512 and role.id != 838502048483377172 and role.id != 885402414000242688 and role.id != 889560965245456394 and role.id != 971100520007761971): # Filter out dumb gangs like gang gang, pop 69 in 2010 gang, etc
                        gang_roles[role.name.lower()] = role.id
                        gang_exists = await self.bot.db_manager.get_gang_id(role.name.lower().strip())
                        if gang_exists == None:
                            await self.bot.db_manager.add_gang(role.id, role.name.lower().strip())

        sorted_roles = dict(sorted(gang_roles.items()))
        for sorted_role_name, sorted_role_id in sorted_roles.items():
            await interaction.channel.send('# ' + interaction.guild.get_role(sorted_role_id).name, view=PersistentView(role_id=sorted_role_id))

        await interaction.response.send_message('Join Roles Here created!', ephemeral=True)

        @generate_gang_list.error # Error handler for adding someone to a gang
        async def generate_gang_list(self, interaction: Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.MissingRole):
                await interaction.response.send_message('You do not have permission to use this command!', ephemeral=True) # Permissions error
            else:
                await interaction.response.send_message('An error has occured', ephemeral=True) # Every other error


async def setup(bot):
    all_gang_ids = await bot.db_manager.get_all_gang_ids()
    #all_gang_ids = []
    await bot.add_cog(GangCog(bot, all_gang_ids))