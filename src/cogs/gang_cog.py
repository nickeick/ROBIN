from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction, Client, Guild

IS_ENABLED = True

class GangCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @app_commands.command(name = 'addgang', description='Dont add gang to the end') 
    @app_commands.has_role(578065628691431435) #If has admin role
    async def add_gang(self, interaction: Interaction, client: Client, guild: Guild, add_channel: str):
        channels = [] 
        for channel in client.get_all_channels(): # Get a list of every gang
            n = 5
            channel_ending = ''
            while (n > 0 ):
                channel_ending += channel.name[-n]
                n = n-1
            if channel_ending.lower == '-gang':
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
                n = n+1
                break

        guild.create_text_channel(add_channel + '-gang', category=579796688420732949, position=n )
        sent = await interaction.response.send_message('Gang created!')


    
    # @app_commands.command()
    # @app_commands.has_role(578065628691431435) #If has admin role
    # async def generate_gang_list(self, interaction: Interaction, name='generateganglist'):

async def setup(bot):
    await bot.add_cog(GangCog(bot))