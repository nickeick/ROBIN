from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction
import asyncio
from random import sample

IS_ENABLED = True

class VocabCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.countdown_text = "### Countdown \n # "
        self.mute = self.bot.get_channel(870946768928534528)

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    async def timer(self, interaction: Interaction, countdown_text: str, seconds: int):
        if seconds > 0:
            await interaction.response.send_message(content=countdown_text + str(seconds))
            for i in range(seconds-1, -1, -1):
                # Wait for a second before updating timer
                await asyncio.sleep(1)
                await interaction.edit_original_response(content=countdown_text + str(i))
        return "Timer finished!"

    @app_commands.command()
    async def countdown(self, interaction: Interaction, seconds: int):
        await self.timer(interaction, self.countdown_text, seconds)

    @app_commands.command()
    async def vocab(self, interaction: Interaction):
        words = ['apple', 'banana', 'orange']
        target = sample(words, 1)[0]
        """Start a timer that cancels if a specific message is received."""
        timer_duration = 10  # Duration of the timer in seconds
        user_id = interaction.author.id  # The ID of the user to listen for
        channel_id = interaction.channel.id  # The channel to listen in

        # Create an asynchronous task for message checking
        async def check_for_message(channel_id: int):
            try:
                # Wait for a message from the user in the same channel
                message = await bot.wait_for(
                    "message",
                    timeout=timer_duration,
                    check=lambda m: m.channel.id == channel.id
                )
                return f"Message received: {message.content}"
            except asyncio.TimeoutError:
                return None

        # Run the tasks concurrently
        timer_task = asyncio.create_task(self.timer(interaction, "You have 10 seconds to type the word " + target, timer_duration))
        message_task = asyncio.create_task(check_for_message(self.mute.id))

        # Wait for either the timer to finish or a message to be sent
        done, pending = await asyncio.wait(
            [timer_task, message_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel any unfinished tasks
        for task in pending:
            task.cancel()

        # Handle the result
        result = done.pop().result()
        if result == "Timer finished!":
            await interaction.response.send_message("Time's up!")
        else:
            await interaction.response.send_message(result)
            


async def setup(bot):
    await bot.add_cog(VocabCog(bot))