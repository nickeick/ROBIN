from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Member, RawReactionActionEvent, Message


IS_ENABLED = True

class EventsCog(commands.Cog):
    """
    A class that inherits from the commands.Cog class with the purpose of implementing events that are triggered

    ...

    Attributes
    ----------
    bot: commands.Bot
        The Bot object representing the discord bot
    
    Listeners
    ---------
    on_member_join(member: Member) -- https://discordpy.readthedocs.io/en/stable/api.html?highlight=on_member_join#discord.on_member_join
        Called when a Member joins a Guild
    on_raw_reaction_add(payload: RawReactionActionEvent) -- https://discordpy.readthedocs.io/en/stable/api.html?highlight=on_raw_reaction_add#discord.on_raw_reaction_add
        Called when a message has a reaction added regardless of the state of the internal message cache
    on_message(message: Message) -- https://discordpy.readthedocs.io/en/stable/api.html?highlight=on_message#discord.on_message
        Called when a message is created and sent
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.initiate_role_id = 759600936435449896
        self.dojo_id = 578065102310342677

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        """
        Adds a new member to the Initiate Role which prevents the user from seeing large parts of the Dojo

        Parameters
        ----------
        member: Member
            Object representing new member who has just joined a Guild
        """
        if member.guild.id == self.dojo_id:
            await member.add_roles(member.guild.get_role(self.initiate_role_id)) # Assign initiate role on user join


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        """
        Removes the initiate role when someone reacts with a check on the correct message

        Parameters
        ----------
        payload: RawReactionActionEvent
            Object representing a reaction that has happened
        """
        if str(payload.emoji) == "☑️" and payload.message_id == 759611108541071380:
            await payload.member.remove_roles(payload.member.guild.get_role(self.initiate_role_id))

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """
        Checks if a Server Admin-created command is sent and sends the corresponding output
        If someone starts their sentence with "I'm" then it responds with their message back to them
        If someone thanks the robot then she responds with a "You're welcome"

        Parameters
        ----------
        message: Message
            Object representing the message that a user has sent
        """
        if message.author == self.bot.user:
            return
        if message.content.startswith('!'):
            outputs = await self.bot.db_manager.get_output(message.content)
            for output in outputs:
                await message.channel.send(output[0])
        if message.content.startswith("I'm "):
            if message.guild.id == self.dojo_id:
                message_content = message.content.replace("I'm ", '').strip()
                await message.reply(content="Hi " + message_content + ", I'm Robin")
        if "thank you robin" in message.content.lower():
            await message.reply(content="You're welcome")


async def setup(bot):
    await bot.add_cog(EventsCog(bot))