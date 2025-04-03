from discord.ext import commands, tasks
from discord.ext.commands import Context, Cog
from discord import app_commands
from discord import Member, Interaction
import asyncio
import datetime

import checks.checks

IS_ENABLED = True
time = datetime.time(hour=5, minute=0, tzinfo=datetime.timezone.utc)

class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dojo_id = 578065102310342677
        self.muted_today = []
        self.reset_mute_lock.start()

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @checks.checks.is_in_dojo()
    @checks.checks.has_voice_state()
    @app_commands.command(description='COSTS 1 COMMON CENT: Server mute someone in call for 1 minute')
    async def mute(self, interaction: Interaction, member: Member):
        if member.id in self.muted_today:
            await interaction.response.send_message(f"{member.nick} has already been muted today!")
            return

        if member.voice is not None:
            if member.voice.channel.guild.id != self.dojo_id:
                await interaction.response.send_message(f"You can only mute someone in a Dojo voice channel")
                return
            
            points = await self.bot.db_manager.get_brain_cells(interaction.user.name)

            if points < 1:
                await interaction.response.send_message(f"You don't have enough common cents (1) to use this command")
                return
            
            await self.bot.db_manager.remove_brain_cells(interaction.user.name, 1)
            await member.edit(mute=True)
            await interaction.response.send_message(f"You have spent 1 Common Cent to mute {member.nick} for 60 seconds")
            self.muted_today.append(member.id)
            await asyncio.sleep(60)
            await member.edit(mute=False)
        else:
            await interaction.response.send_message("The person you want to mute is not in a voice channel")

    @mute.error
    async def mute_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)

    @tasks.loop(time=time)
    async def reset_mute_lock(self):
        self.muted_today = []




async def setup(bot):
    await bot.add_cog(VoiceCog(bot))