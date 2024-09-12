from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from discord import Interaction 

IS_ENABLED = True

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @app_commands.command(description='List of helpful commands!')
    async def help(self, interaction: Interaction):
        message = 'Join different gangs in the #join-roles-here channel\n\n/play - Ask people if they are interested in playing a game with you\n\n🧠 Braincell Information 🧠\n/think - Use the server brain cell if you have one! ⚡\n/braincell - See who has the braincell! 🤔\n/cents - See how many times you\'ve /think\'ed! :coin:\n/leaderboard - View the leaderboards! 🥇\n\nStop by the #faq channel if you have any other questions!'  
        sent = await interaction.response.send_message(message)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))