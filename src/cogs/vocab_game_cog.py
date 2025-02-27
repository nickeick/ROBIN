from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, Interaction, Message
import asyncio
from random import sample
import os
import pickle

IS_ENABLED = True

class VocabCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.countdown_text = "### Countdown \n # "
        self.mute_id = 870946768928534528
        # Path to the language model that contains your word embeddings
        self.file_path = 'assets/fasttext.p'
        if os.path.exists(self.file_path):
            self.model = pickle.load(open(self.file_path, "rb"))
        else:
            self.model = None

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    async def timer(self, channel, countdown_text: str, seconds: int):
        if seconds > 0:
            counter = await channel.send(content=countdown_text + str(seconds))
            for i in range(seconds-1, -1, -1):
                # Wait for a second before updating timer
                await asyncio.sleep(1)
                await counter.edit(content=countdown_text + str(i))
        return "Timer finished!"

    # Create an asynchronous task for message checking
    async def check_for_message(self, targets, timer_duration: int, channel_id: int, used_words: list):
        try:
            # Wait for a message from the user in the same channel
            message = await self.bot.wait_for(
                'message',
                timeout=timer_duration,
                check=lambda m: m.channel.id == channel_id and m.content.lower() in targets and m.content.lower() not in used_words
            )
            return message
        except asyncio.TimeoutError:
            return None

    # Access the word embeddings and find the most similar words to the input word
    async def get_similar_words(self, word: str, topn: int):
        if self.model:
            words = self.model.most_similar(word, topn=topn)
            words_list = list(set(map(lambda x: x[0].lower(), words)))
            return words_list

    async def vocab_game(self, channel, targets: list, used_words: list):
        """Start a timer that cancels if a specific message is received."""
        if channel.id != self.mute_id:
            await channel.send("You can only play this game in #mute!")
            return
        
        if targets == None:
            await channel.send("No similar words found")
            return

        timer_duration = 10  # Duration of the timer in seconds

        # Run the tasks concurrently
        timer_task = asyncio.create_task(self.timer(channel, f"### You have {timer_duration} seconds to type a similar word \n # ", timer_duration))
        message_task = asyncio.create_task(self.check_for_message(targets, timer_duration, self.mute_id, used_words))

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
            await channel.send("Time's up!")
        else:
            used_words.append(result.content.lower())
            targets = self.get_similar_words(result.content.lower(), 100)
            await result.reply(content=f"Successful Response!")
            await self.vocab_game(result.channel, targets, used_words)

    @app_commands.command()
    async def countdown(self, interaction: Interaction, seconds: int):
        await interaction.response.defer()
        await self.timer(interaction.channel, self.countdown_text, seconds)

    @app_commands.command()
    async def vocab(self, interaction: Interaction):
        starting_words = ['apple', 'banana', 'orange', 'blueberry', 'strawberry', 'cherry', 'grapefruit', 'kiwi', 'mango', 'peach', 'watermelon', 'pear', 'raspberry']
        starting_word = sample(starting_words, 1)
        used_words = [starting_word]
        if self.model:
            targets = self.get_similar_words(starting_word, 100)
            await interaction.response.defer()
            await self.vocab_game(interaction.channel, targets, used_words)
        else:
            await interaction.response.send_message("Sorry! I can't find the model")

# Testing by adding a comment


async def setup(bot):
    await bot.add_cog(VocabCog(bot))