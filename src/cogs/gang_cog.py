from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction, PermissionOverwrite, Member

IS_ENABLED = True

class GangCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server_admin_id = 578065628691431435

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @app_commands.checks.has_role(self.server_admin_id) # If has admin role
    @app_commands.command(name = 'addgang', description='Dont add gang to the end') 
    async def add_gang(self, interaction: Interaction, add_channel: str):
        channels = [] 
        for channel in self.bot.get_all_channels(): # Get a list of every gang
            if len(channel.name) > 5:
                if channel.name[-6:-1].lower == '-gang':
                    channels.append(channel.name)
        
        for channel in channels: # Check if gang already exists, exit command if so
            if channel.lower == add_channel.lower + '-gang':
                sent = await interaction.response.send_message('Gang already exists!')
                return
            
        channels.append(add_channel) # Get the alphabetic postion the channel should be put at
        channels.sort()
        n = 0
        for channel in channels:
            if channel == add_channel:
                n = channels.index(channel)
                break

        activities = interaction.guild.get_channel(579796688420732949) # Gang Activities category
        new_role = await interaction.guild.create_role(name=add_channel + " Gang")
        overwrites = {interaction.guild.default_role: PermissionOverwrite(read_messages=False),
                            new_role: PermissionOverwrite(read_messages=True)}
        await interaction.guild.create_text_channel(add_channel + '-gang', overwrites=overwrites, category=activities, position=n)
        sent = await interaction.response.send_message(add_channel + ' Gang has been made! Type "/join ' + add_channel + ' Gang" to join')

    @app_commands.command(name = 'joingang', description='Join a gang!') 
    async def join_gang(self, interaction: Interaction, member: Member, add_role: str):
        for role in interaction.guild.roles:
            if role.name.lower() in add_role:
                if  ('gang' not in role.name.lower()) or role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy" or role.name == 'The Server Brain Cell' or role.name == 'Server Genius' or role.name == 'Pingcord':
                    await interaction.channel.send('You cannot join this role: ' + role.name)
                    return
                else:
                    await member.add_roles(role)
                    if role.name == 'Movie Night Gang':
                        await interaction.channel.send('*This is an NSFW Gang*')
                    await interaction.channel.send('Added ' + member.display_name + ' to ' + role.name)
    
    # @app_commands.command(name='generategangs')
    # @app_commands.has_role(578065628691431435) #If has admin role
    # async def generate_gang_list(self, interaction: Interaction, name='generateganglist'):


async def setup(bot):
    await bot.add_cog(GangCog(bot))