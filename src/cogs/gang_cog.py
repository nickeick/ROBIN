from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction, PermissionOverwrite, Channel, Guild
import discord

IS_ENABLED = True

class RoleManager(discord.ui.View):
        def __init__(self, role_id):
            super().__init__()
            self.role_id = role_id

        @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
        async def join_button_callback(self, interaction: Interaction, guild: Guild, button):
            if guild.get_role(self.role_id) in interaction.user.roles:
                await interaction.response.send_message('You are already in ' + guild.get_role(self.role_id).name, ephemeral=True)
            else:
                interaction.user.add_roles(guild.get_role(self.role_id))
                await interaction.response.send_message('Added to ' + guild.get_role(self.role_id).name, ephemeral=True)
            await interaction.response.defer()

        @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
        async def leave_button_callback(self, interaction: Interaction, guild: Guild, button):
            if guild.get_role(self.role_id) in interaction.user.roles:
                interaction.user.remove_roles(guild.get_role(self.role_id))
                await interaction.response.send_message('Left ' + guild.get_role(self.role_id).name, ephemeral=True)
            else:
                await interaction.response.send_message('You are not in ' + guild.get_role(self.role_id).name, ephemeral=True)
            await interaction.response.defer()
    

class GangCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_test = 582060071052115978
        self.join_roles_here = 1027646452371046430

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @app_commands.checks.has_role(578065628691431435) # If has admin role
    @app_commands.command(name = 'makegang', description='Dont add gang to the end') 
    async def add_gang(self, interaction: Interaction, guild: Guild, add_channel: str):
        gang_channels = [] 
        for channel in guild.channels: # Get a list of every gang
            if len(channel.name) > 5:
                if channel.name[-6:-1].lower == '-gang':
                    gang_channels.append(channel.name)
        
        for channel in gang_channels: # Check if gang already exists, exit command if so
            if channel.lower == add_channel.lower + '-gang':
                sent = await interaction.response.send_message('Gang already exists!', ephemeral=True)
                return
            
        gang_channels.append(add_channel) # Get the alphabetic postion the channel should be put at
        gang_channels.sort()
        n = 0
        for channel in gang_channels:
            if channel == add_channel:
                n = gang_channels.index(channel)
                break

        activities = interaction.guild.get_channel(579796688420732949) # Gang Activities category
        new_role = await interaction.guild.create_role(name=add_channel + " Gang") # Create New Role
        overwrites = {interaction.guild.default_role: PermissionOverwrite(read_messages=False),
                            new_role: PermissionOverwrite(read_messages=True)}
        await interaction.guild.create_text_channel(add_channel + '-gang', overwrites=overwrites, category=activities, position=n) # Create New Text Channel
        sent = await interaction.response.send_message(add_channel + ' Gang has been made! Type "/join ' + add_channel + ' Gang" to join', ephemeral=True)

    @app_commands.command(name = 'join', description='Join a gang!') # Join gang
    async def join_gang(self, interaction: Interaction, add_role: str):
        movie_night_addendum = ''
        for role in interaction.guild.roles:
            if role.name.lower() in add_role.strip().lower():
                if  ('gang' not in role.name.lower()) or role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy" or role.name == 'The Server Brain Cell' or role.name == 'Server Genius' or role.name == 'Pingcord':
                    await interaction.response.send_message('You cannot join this role: ' + role.name, ephemeral=True) # Dont let people join not gang roles
                else:
                    await interaction.user.add_roles(role)
                    if role.name == 'Movie Night Gang': # Warn people of nsw in movie night gang
                        movie_night_addendum = 'This is an NSFW gang \n' # This still might not work
                    await interaction.response.send_message(movie_night_addendum + 'Added ' + interaction.user.display_name + ' to ' + role.name, ephemeral=True)

    @app_commands.command(name = 'leave', description='Leave a gang') # Remove from gang
    async def leave_gang(self, interaction: Interaction, remove_role: str):
        for role in interaction.guild.roles:
            if role.name.lower() in remove_role.strip().lower():
                if ('gang' not in role.name.lower()) or role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy":
                    await interaction.response.send_message('You cannot leave this role: ' + role.name, ephemeral=True) # Dont let people leave not gang roles
                else:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message('Removed ' + interaction.user.display_name + ' from ' + role.name, ephemeral=True)

    @app_commands.has_role(578065628691431435) #If has admin role
    @app_commands.command(name='generategangs')
    async def generate_gang_list(self, interaction: Interaction, guild: Guild, channel: Channel, name='generateganglist'): #Gang List Maker ONLY TEST IN SPECIFIC CHANNEL IT WILL DELETE STUFF
        if interaction.channel_id != self.join_roles_here and interaction.channel_id != self.bot_test: 
            await interaction.response.send_message('This command can only be used in #join-roles-here!')
            return
        
        # THIS DELETES THE HISTORY OF THE CHANNEL
        # if(interaction.channel_id == self.join_roles_here):
        #     async for message in channel.history(limit=none):
        #         try:
        #             await message.delete()
        #         except discord.Forbidden:
        #             interaction.response.send_message('Could not delete message - No Permissions')
        #         except discord.HTTPException as e:
        #             interaction.response.send_message('Could not delete message - {e}')

        gang_roles = []
        for role in guild.roles: # Get a list of every gang role
            if len(role.name) > 4:
                if role.name[-5:-1].lower == 'gang':
                    if (role.id != 636466520591040512 and role.id != 838502048483377172): # Filter out gang gang and pop 69 in 2010 gang
                        gang_roles.append(role.id)

        for role in gang_roles:
            await interaction.channel.send(guild.get_role(role).name, view=RoleManager(role_id=role))

        await interaction.response.send_messages('Join Roles Here created!', ephemeral=True)


async def setup(bot):
    await bot.add_cog(GangCog(bot))