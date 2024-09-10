from discord.ext import commands
from discord.ext.commands import Context, Cog
from discord import app_commands

IS_ENABLED = True

class MuteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dojo_id = 578065102310342677

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        mute = self.bot.get_channel(870946768928534528)
        if after.channel != None and after.channel.guild.id == self.dojo_id:
            await mute.set_permissions(member, send_messages = True, read_messages = True)
        if after.channel == None or after.channel.guild.id != self.dojo_id:
            await mute.set_permissions(member, send_messages = False, read_messages = False)

async def setup(bot):
    await bot.add_cog(MuteCog(bot))