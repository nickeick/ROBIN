from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Member, RawReactionActionEvent

IS_ENABLED = True

class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.initiate_role_id = 759600936435449896

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        await member.add_roles(member.guild.get_role(self.initiate_role_id)) # Assign initiate role on user join


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if str(payload.emoji) == "☑️" and payload.message_id == 759611108541071380:
            await payload.member.remove_roles(payload.member.guild.get_role(self.initiate_role_id))

async def setup(bot):
    await bot.add_cog(EventsCog(bot))