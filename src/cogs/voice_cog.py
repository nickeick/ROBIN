from discord.ext import commands
from discord.ext.commands import Context, Cog
from discord import app_commands
from discord import Member, Interaction
import asyncio

import checks.checks

IS_ENABLED = True

class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dojo_id = 578065102310342677

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @checks.checks.is_in_dojo()
    @checks.checks.has_voice_state()
    @app_commands.command(description='Server mute someone in call for 1 minute at the cost of 1 brain cell')
    async def mute(self, interaction: Interaction, member: Member):
        if member.voice is not None:
            await member.edit(mute=True)
            await interaction.response.send_message(f"You have muted {member.nick}")
            await asyncio.sleep(60)
            await member.edit(mute=False)
        else:
            await interaction.response.send_message("The person you want to mute is not in a voice channel")




async def setup(bot):
    await bot.add_cog(VoiceCog(bot))