from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction, PermissionOverwrite
import discord

IS_ENABLED = True

class RoleManager(discord.ui.View):
        def __init__(self, role_id):
            super().__init__()
            self.role_id = role_id

        @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
        async def join_button_callback(self, interaction: Interaction, button):
            if interaction.guild.get_role(self.role_id) in interaction.user.roles:
                await interaction.response.send_message('You are already in ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)
            else:
                await interaction.user.add_roles(interaction.guild.get_role(self.role_id))
                await interaction.response.send_message('Added to ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)

        @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
        async def leave_button_callback(self, interaction: Interaction, button):
            if interaction.guild.get_role(self.role_id) in interaction.user.roles:
                await interaction.user.remove_roles(interaction.guild.get_role(self.role_id))
                await interaction.response.send_message('Left ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)
            else:
                await interaction.response.send_message('You are not in ' + interaction.guild.get_role(self.role_id).name, ephemeral=True)
    

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
            
        gang_channels.append(gang_name.lower()) # Get the alphabetic postion the channel should be put at
        gang_channels.sort()
        print(gang_channels)
        n = gang_channels.index(gang_name.lower())
        print(n)

        activities = interaction.guild.get_channel(579796688420732949) # Gang Activities category
        new_role = await interaction.guild.create_role(name=gang_name + " Gang") # Create New Role
        overwrites = {interaction.guild.default_role: PermissionOverwrite(read_messages=False),
                            new_role: PermissionOverwrite(read_messages=True)}
        await interaction.guild.create_text_channel(gang_name + '-gang', overwrites=overwrites, category=activities, position=n) # Create New Text Channel
        sent = await interaction.response.send_message(gang_name + ' Gang has been made! Type "/join ' + gang_name + ' Gang" to join', ephemeral=True)

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

    @app_commands.checks.has_role(578065628691431435) #If has admin role
    @app_commands.command(name='generategangs')
    async def generate_gang_list(self, interaction: Interaction): #Gang List Maker ONLY TEST IN SPECIFIC CHANNEL IT WILL DELETE STUFF
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
        for role in interaction.guild.roles: # Get a list of every gang role
            if len(role.name) > 4:
                if role.name[-4:].lower().strip() == 'gang':
                    if (role.id != 636466520591040512 and role.id != 838502048483377172): # Filter out gang gang and pop 69 in 2010 gang
                        gang_roles.append(role.id)

        for role in gang_roles:
            await interaction.channel.send(interaction.guild.get_role(role).name, view=RoleManager(role_id=role))

        await interaction.response.send_message('Join Roles Here created!', ephemeral=True)


async def setup(bot):
    await bot.add_cog(GangCog(bot))