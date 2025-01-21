from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction
import asyncio

IS_ENABLED = True

class VocabCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.countdown_text = "### Countdown \n # "

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    async def timer(self, interaction: Interaction, countdown_text: str, seconds: int):
        if seconds > 0:
            await interaction.response.send_message(content=countdown_text + str(seconds))
            for i in range(seconds, -1, -1):
                await asyncio.sleep(1)
                interaction.edit_original_response(content=countdown_text = str(i))

    @app_commands.command()
    async def countdown(self, interaction: Interaction, seconds: int):
        await self.timer(interaction, self.countdown_text, seconds)  


async def setup(bot):
    await bot.add_cog(VocabCog(bot))