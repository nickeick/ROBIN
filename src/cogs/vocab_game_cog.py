from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction, Message
import asyncio
from random import sample

IS_ENABLED = True

class VocabCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.countdown_text = "### Countdown \n # "
        self.mute_id = 870946768928534528

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    async def timer(self, message: Message, countdown_text: str, seconds: int):
        if seconds > 0:
            counter = await message.channel.send(content=countdown_text + str(seconds))
            for i in range(seconds-1, -1, -1):
                # Wait for a second before updating timer
                await asyncio.sleep(1)
                await counter.edit(content=countdown_text + str(i))
        return "Timer finished!"

    # Create an asynchronous task for message checking
    async def check_for_message(self, target, timer_duration, channel_id: int):
        try:
            # Wait for a message from the user in the same channel
            message = await self.bot.wait_for(
                'message',
                timeout=timer_duration,
                check=lambda m: m.channel.id == channel_id and m.content == target
            )
            return message
        except asyncio.TimeoutError:
            return None

    async def vocab_game(self, message: Message, target: str):
        """Start a timer that cancels if a specific message is received."""
        if message.channel.id != self.mute.id:
            await message.channel.send("You can only play this game in #mute!")
            return
        timer_duration = 10  # Duration of the timer in seconds

        # Run the tasks concurrently
        timer_task = asyncio.create_task(self.timer(message, f"### You have {timer_duration} seconds to type the word {target} \n # ", timer_duration))
        message_task = asyncio.create_task(self.check_for_message(target, timer_duration, self.mute_id))

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
            await message.channel.send("Time's up!")
        else:
            await result.reply(content=f"Successful Response!")
            await self.vocab_game(result, result.content)

    @app_commands.command()
    async def countdown(self, interaction: Interaction, seconds: int):
        await self.timer(interaction.message, self.countdown_text, seconds)

    @app_commands.command()
    async def vocab(self, interaction: Interaction):
        words = ['apple', 'banana', 'orange']
        target = sample(words, 1)[0]
        await interaction.response.send_message("Starting game...", ephemeral=True)
        await self.vocab_game(interaction.message, target)

            


async def setup(bot):
    await bot.add_cog(VocabCog(bot))