from aiohttp import web
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands, Interaction, Attachment, Member, Embed
import typing

IS_ENABLED = True

class NFTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if (not IS_ENABLED):
            await ctx.send('This Cog is disabled')
        return IS_ENABLED
    
    def make_embed(self, id: int, url: str, price: int):
        embed = Embed(title="NFT #" + str(id), description="Listed for " + str(price) + " Common Cents")
        embed.set_image(url=url)
        return embed

    @app_commands.command()
    async def list(self, interaction: Interaction, image: Attachment, price: int):
        if price < 1:
            await interaction.response.send_message("Your NFT's price must be above zero")
            return
        shop_amount = await self.bot.db_manager.get_nft_shop_amount(interaction.user.id)
        if shop_amount > 2:
            await interaction.response.send_message(f"You have the maximum items in your shop! ({shop_amount})")
            return
        if image.content_type.startswith("image/"):
            new_id = await self.bot.db_manager.add_new_nft(image.url, interaction.user.id, price)
            await interaction.response.send_message(f"NFT ID #{new_id} was added to your shop at {price}")

    @app_commands.command()
    async def shop(self, interaction: Interaction, person: typing.Optional[Member]):
        if person is None:
            person = interaction.user
        nfts = await self.bot.db_manager.get_nft_shop(person.id)
        output = []
        for nft in nfts:
            output.append(self.make_embed(nft[0], nft[1], nft[2]))
            




async def setup(bot):
    await bot.add_cog(NFTCog(bot))
    
    
    