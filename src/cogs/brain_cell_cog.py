from typing import Optional
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands, Interaction, Guild, Client
import discord
from random import randint

IS_ENABLED = True

class LeaderboardView(discord.ui.View): # Create a class called LeaderboardView that subclasses discord.ui.View
    @discord.ui.button(label="Left", style=discord.ButtonStyle.blurple, emoji="⬅️") # Create a button with the label "Left"
    async def left_button_callback(self, interaction: Interaction, button):
        braincell_cog = interaction.client.get_cog('BrainCellCog')
        content: str = interaction.message.content
        contentLines = content.split("\n")

        # 11-20
        startingIndex = int(contentLines[1].split(".")[0]) - 10
        endingIndex = startingIndex + 9

        if(startingIndex >= 1):
            to_send = await braincell_cog.printLeaderboard(interaction, startingIndex, endingIndex)
            await interaction.message.edit(content=to_send)
        await interaction.response.defer()

    @discord.ui.button(label="Right", style=discord.ButtonStyle.blurple, emoji="➡️") # Create a button with the label "Right"
    async def right_button_callback(self, interaction: Interaction, button):
        braincell_cog = interaction.client.get_cog('BrainCellCog')
        content: str = interaction.message.content
        contentLines = content.split("\n")

        # 11-20
        startingIndex = int(contentLines[1].split(".")[0]) + 10
        endingIndex = startingIndex + 9

        to_send = await braincell_cog.printLeaderboard(interaction, startingIndex, endingIndex)
        await interaction.message.edit(content=to_send)
        await interaction.response.defer()

class BrainCellCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.think_locked = []
        self.genius_id = 779433226560864267
        self.dojo_id = 578065102310342677
        self.main_dojo_id = 578065102310342679
        self.braincell_role_id = 771408034957623348
        self.braincell_swap.start()

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED

    async def update_genius(self, name: str, guild: Guild):
        for member in guild.members:        # Remove previous Server Genius
            if guild.get_role(self.genius_id) in member.roles:
                await member.remove_roles(guild.get_role(self.genius_id))
        genius_member = guild.get_member_named(name)
        await genius_member.add_roles(guild.get_role(self.genius_id))

    async def printLeaderboard(self, interaction: Interaction, lowerBound: int, upperBound: int):
        items = await self.bot.db_manager.get_all_points()
        filteredItems = list(filter(lambda x : interaction.guild.get_member_named(x[0]) is not None, items))
        if (lowerBound - 1) > len(filteredItems):
            to_send = interaction.message.content
            return to_send

        to_send = '🪙  **Common Cents Leaderboard:**  🪙\n'
        for index in range(lowerBound, upperBound + 1):
            if index > len(filteredItems):
                break

            item = filteredItems[index - 1]
            name = interaction.guild.get_member_named(item[0]).display_name
            to_send += str(index) + '. ' + name + ':'

            # buffer up to 60 characters, but with less b/c of name
            buffer = ' ' * (60 - len(name)*2)
            to_send += buffer

            cents = item[1]
            while cents > 0:
                if (cents // 100) > 0:
                    to_send += '💎'
                    cents -= 100
                elif (cents // 10) > 0:
                    to_send += '💵'
                    cents -= 10
                else:
                    to_send += '🪙'
                    cents -= 1
            to_send += '|   ' + str(item[1]) + '\n'
        return to_send

    @app_commands.command(description='See who has the braincell')
    async def braincell(self, interaction: Interaction):
        to_send = ''
        for member in interaction.guild.members:
            if interaction.guild.get_role(self.braincell_role_id) in member.roles:
                to_send += member.display_name + ' is hogging the server brain cell\n'
        await interaction.response.send_message(to_send)

    @app_commands.command(description='Use the braincell to think')
    async def think(self, interaction: Interaction):
        if interaction.guild.get_role(self.braincell_role_id) in interaction.user.roles:
            if interaction.user.id not in self.think_locked:
                old_leader = await self.bot.db_manager.get_point_leader()
                await interaction.response.send_message("🧠 This makes cents 🪙")
                await self.bot.db_manager.add_brain_cell(interaction.user.name)
                new_leader = await self.bot.db_manager.get_point_leader()
                if old_leader != new_leader:
                    self.update_genius(new_leader, interaction.guild)
                self.think_locked.append(interaction.user.id)
            else:
                await interaction.response.send_message("You've already got your cent <:bonk:772161497031507968>")
        else:
            await interaction.response.send_message("You don't have the brain cell <:bonk:772161497031507968>")

    @app_commands.commmand(name='give', description='Give someone your braincells')
    async def give_braincell(self, interaction: Interaction, receiver: discord.Member, amount: int):
        try:
            give = (receiver.group(1), amount.group(2))
            assert interaction.guild.get_member_named(give[0]) != None, "Member does not exist"
            
            author_select = (str(interaction.user.name),)
            self.c.execute('SELECT points FROM braincell_points WHERE name=?', author_select) # Check if user doing command is doing anything nefarious
            author_points = self.c.fetchone()
            assert author_points != None, "You have no Common Cents"
            assert author_points[0] >= int(give[1]), "You do not have enough Common Cents to give"
            assert int(give[1]) >= 0, "You cannot gift negative points"
            assert str(interaction.user.name) != str(receiver.name), "You cannot gift to yourself"

            receive_select = (str(receiver.name),)
            self.c.execute('SELECT points FROM braincell_points WHERE name=?', receive_select) # Check on receiver
            receive_points = self.c.fetchone()

            author_replace = (str(interaction.user.name), author_points[0]-int(give[1])) # Give braincell
            self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", author_replace)
            if receive_points == None:
                receive_replace = (str(receiver.name), int(give[1]))
            else:
                receive_replace = (str(receiver.name), receive_points[0]+int(give[1]))
            self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", receive_replace)
            self.db.commit()
            await interaction.response.send_message("You have given " + give[1] + " Common Cents to " + give[0])

        except AssertionError as err: # Catch neferious actions
            await interaction.response.send_message(err, ephemeral=True)

    @app_commands.command(description='View the cents leaderboard')
    async def leaderboard(self, interaction: Interaction):
        to_send = await self.printLeaderboard(interaction, 1, 10)
        sent = await interaction.response.send_message(to_send, view=LeaderboardView())

    @app_commands.command(description='See how many times you\'ve /think\'ed')
    async def cents(self, interaction: Interaction):
        await interaction.response.send_message('This is not a real command you just got pranked <:tracerdab:633510729915564050>')

    @tasks.loop(minutes = 20)
    async def braincell_swap(self):
        await self.bot.wait_until_ready()
        members = self.bot.get_channel(self.main_dojo_id).members      #get the-main-dojo members
        not_bots = list(filter(lambda x : not x.bot, members))
        braincell_role = self.bot.get_guild(self.dojo_id).get_role(self.braincell_role_id)
        for member in not_bots:
            if braincell_role in member.roles:
                await member.remove_roles(braincell_role)
        size = len(not_bots)
        braincell_amount = 2
        for times in range(braincell_amount):
            new_user = randint(0,size-1)
            await not_bots[new_user].add_roles(braincell_role)
        self.think_locked = []

async def setup(bot):
    await bot.add_cog(BrainCellCog(bot))