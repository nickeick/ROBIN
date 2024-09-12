from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Member, RawReactionActionEvent, Message

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

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author == self.bot.user:
            return
        if message.content.startswith('!'):
            outputs = await self.bot.db_manager.get_output(message.content)
            for output in outputs:
                await message.channel.send(output[0])
        if ' im ' in message.content.lower:
            for x in range(len(message.content)):
                if 'im' in message.content[x:].lower:
                    what_they_are = message.content[message.content.lower.find('im', x) + 3:]
                    await message.channel.send('Hi ' + what_they_are + ', I\'m Robin')
        if ' i\'m ' in message.content.lower:
            for x in range(len(message.content)):
                if 'i\'m' in message.content[x:].lower:
                    what_they_are = message.content[message.content.lower.find('i\'m', x) + 4:]
                    await message.channel.send('Hi ' + what_they_are + ', I\'m Robin')

async def setup(bot):
    await bot.add_cog(EventsCog(bot))