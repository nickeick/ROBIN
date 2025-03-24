from discord.ext import commands
from discord import app_commands, Interaction, Guild

def is_in_dojo():
    async def predicate(interaction: Interaction):
        dojo_id = 578065102310342677
        if interaction.guild.id == dojo_id:
            return
        raise app_commands.DisabledCommand(message="This command is not enabled for this server")
    return app_commands.check(predicate)

def is_admin():
    async def predicate(interaction: Interaction):
        admin_id = 578065628691431435
        if any(role.id == admin_id for role in interaction.user.roles):
            return
        raise app_commands.MissingPermissions(["Admin"])
    return app_commands.check(predicate)

def has_brain_cell():
    async def predicate(interaction: Interaction):
        braincell_id = 771408034957623348
        if any(role.id == braincell_id for role in interaction.user.roles):
            return
        raise app_commands.MissingRole(771408034957623348)
    return app_commands.check(predicate)

def has_voice_state():
    async def predicate(interaction: Interaction):
        if interaction.user.voice is not None:
            return
        raise app_commands.ChannelNotFound(message="This command requires being in a voice channel")
    return app_commands.check(predicate)
