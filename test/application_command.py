from discord import Intents
from discord import Client
from discord import InvalidArgument
from discord import ApplicationCommandOption
from discord import User
from discord.abc import GuildChannel
from discord import Role
from discord import Embed
from discord import File

from asyncio import sleep
from asyncio import Queue

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

with open("guild.txt") as guildFile:
    GUILD_ID = int(guildFile.read()) # The guild to test commands on

intents = Intents.default()
intents.members = True
client = Client(intents = intents)

command_create_queue = Queue()
command_update_queue = Queue()
command_delete_queue = Queue()
interaction_queue = Queue()

@client.event
async def on_application_command_create(command):
    await command_create_queue.put(command)

@client.event
async def on_application_command_update(old_command, command):
    await command_update_queue.put((old_command, command))

@client.event
async def on_application_command_delete(command):
    await command_delete_queue.put(command)

@client.event
async def on_interaction(interaction):
    if interaction.is_command_interaction():
        await interaction_queue.put(interaction)
    else:
        await interaction.send_response("No implementation")

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)

    # Part 1: Clear all guild commands
    try:
        commands = await guild.fetch_application_commands()
        for command in commands:
            await command.delete()
            await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 1 Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 1 Success!")

    # Part 2: Creating some invalid commands (1/5)
    try:
        command = await guild.create_application_command(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 2 (1/5) Success!")
    except Exception as e:
        log.info(f"Part 2 (1/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 2 (1/5) Failure: {command} returned")
    # (2/5)
    try:
        command = await guild.create_application_command(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 2 (2/5) Success!")
    except Exception as e:
        log.info(f"Part 2 (2/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 2 (2/5) Failure: {command} returned")
    # (3/5)
    try:
        command = await guild.create_application_command(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 2 (3/5) Success!")
    except Exception as e:
        log.info(f"Part 2 (3/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 2 (3/5) Failure: {command} returned")
    # (4/5)
    try:
        command = await guild.create_application_command(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 2 (4/5) Success!")
    except Exception as e:
        log.info(f"Part 2 (4/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 2 (4/5) Failure: {command} returned")
    # (5/5)
    try:
        command = await guild.create_application_command(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 2 (5/5) Success!")
    except Exception as e:
        log.info(f"Part 2 (5/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 2 (5/5) Failure: {command} returned")

    # Part 3: Command with no arguments (1/5)
    try:
        command = await guild.create_application_command(name="tmp", description="Do not use yet")
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 3 (1/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 3 (1/5) Success!")
    # (2/5)
    try:
        await command.edit(description="Still don't use")
        old_command, new_command = await command_update_queue.get()
        # assert old_command.description == "Do not use yet"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 3 (2/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 3 (2/5) Success!")
    # (3/5)
    try:
        await command.edit(name="test", description="Now try this out")
        old_command, new_command = await command_update_queue.get()
        # assert old_command.name == "tmp"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 3 (3/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 3 (3/5) Success!")
    # (4/5)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response("You used /test")
    except Exception as e:
        log.info(f"Part 3 (4/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 3 (4/5) Success!")
    # (5/5)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 3 (5/5) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 3 (5/5) Success!")

    # Part 4: Command with a String argument (1/17)
    try:
        option = ApplicationCommandOption.String(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 4 (1/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (1/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (1/17) Failure: {option} returned")
    # (2/17)
    try:
        option = ApplicationCommandOption.String(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 4 (2/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (2/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (2/17) Failure: {option} returned")
    # (3/17)
    try:
        option = ApplicationCommandOption.String(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 4 (3/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (3/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (3/17) Failure: {option} returned")
    # (4/17)
    try:
        option = ApplicationCommandOption.String(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 4 (4/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (4/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (4/17) Failure: {option} returned")
    # (5/17)
    try:
        option = ApplicationCommandOption.String(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 4 (5/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (5/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (5/17) Failure: {option} returned")
    # (6/17)
    try:
        option = ApplicationCommandOption.String(name="tmp", description="tmp", choices={"" : "tmp"})
    except InvalidArgument:
        log.info(f"Part 4 (6/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (6/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (6/17) Failure: {option} returned")
    # (7/17)
    try:
        option = ApplicationCommandOption.String(name="tmp", description="tmp", choices={"tmp"*34 : "tmp"})
    except InvalidArgument:
        log.info(f"Part 4 (7/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (7/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (7/17) Failure: {option} returned")
    # (8/17)
    try:
        option = ApplicationCommandOption.String(name="tmp", description="tmp", choices={"tmp" : ""})
    except InvalidArgument:
        log.info(f"Part 4 (8/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (8/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (8/17) Failure: {option} returned")
    # (9/17)
    try:
        option = ApplicationCommandOption.String(name="tmp", description="tmp", choices={"tmp" : "tmp" * 34})
    except InvalidArgument:
        log.info(f"Part 4 (9/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (9/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (9/17) Failure: {option} returned")
    # (10/17)
    try:
        option = ApplicationCommandOption.String(name="tmp", description="tmp", choices={f"tmp{i}" : f"tmp{i}" for i in range(26)})
    except InvalidArgument:
        log.info(f"Part 4 (10/17) Success!")
    except Exception as e:
        log.info(f"Part 4 (10/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (10/17) Failure: {option} returned")
    # (11/17)
    try:
        option = ApplicationCommandOption.String(name="string", description="Mandatory string argument")
        command = await guild.create_application_command(name="test", description="Use me to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 4 (11/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (11/17) Success!")
    # (12/17)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], str)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
    except Exception as e:
        log.info(f"Part 4 (12/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (12/17) Success!")
    # (13/17)
    try:
        option = ApplicationCommandOption.String(name="string", description="Optional string argument", required=False)
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Mandatory string argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 4 (13/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (13/17) Success!")
    # (14/17)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        if option.name in interaction.options:
            assert isinstance(interaction.options[option.name], str)
            await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
        else:
            await interaction.send_response(f"You used /test with no argument")
    except Exception as e:
        log.info(f"Part 4 (14/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (14/17) Success!")
    # (15/17)
    try:
        option = ApplicationCommandOption.String(name="string",
                                                 description="Mandatory string argument with choices",
                                                 choices={"first" : "first", "second" : "second", "third" : "third"})
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Optional string argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 4 (15/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (15/17) Success!")
    # (16/17)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], str)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
    except Exception as e:
        log.info(f"Part 4 (16/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (16/17) Success!")
    # (17/17)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 4 (17/17) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 4 (17/17) Success!")

    # Part 5: Command with an integer argument (1/15)
    try:
        option = ApplicationCommandOption.Integer(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 5 (1/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (1/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (1/15) Failure: {option} returned")
    # (2/15)
    try:
        option = ApplicationCommandOption.Integer(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 5 (2/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (2/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (2/15) Failure: {option} returned")
    # (3/15)
    try:
        option = ApplicationCommandOption.Integer(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 5 (3/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (3/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (3/15) Failure: {option} returned")
    # (4/15)
    try:
        option = ApplicationCommandOption.Integer(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 5 (4/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (4/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (4/15) Failure: {option} returned")
    # (5/15)
    try:
        option = ApplicationCommandOption.Integer(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 5 (5/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (5/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (5/15) Failure: {option} returned")
    # (6/15)
    try:
        option = ApplicationCommandOption.Integer(name="tmp", description="tmp", choices={"" : 0})
    except InvalidArgument:
        log.info(f"Part 5 (6/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (6/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (6/15) Failure: {option} returned")
    # (7/15)
    try:
        option = ApplicationCommandOption.Integer(name="tmp", description="tmp", choices={"tmp"*34 : 0})
    except InvalidArgument:
        log.info(f"Part 5 (7/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (7/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (7/15) Failure: {option} returned")
    # (8/15)
    try:
        option = ApplicationCommandOption.Integer(name="tmp", description="tmp", choices={f"tmp{i}" : i for i in range(26)})
    except InvalidArgument:
        log.info(f"Part 5 (8/15) Success!")
    except Exception as e:
        log.info(f"Part 5 (8/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (8/15) Failure: {option} returned")
    # (9/15)
    try:
        option = ApplicationCommandOption.Integer(name="integer", description="Mandatory integer argument")
        command = await guild.create_application_command(name="test", description="Use me to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 5 (9/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (9/15) Success!")
    # (10/15)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], int)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
    except Exception as e:
        log.info(f"Part 5 (10/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (10/15) Success!")
    # (11/15)
    try:
        option = ApplicationCommandOption.Integer(name="integer", description="Optional integer pargument", required=False)
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Mandatory integer argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 5 (11/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (11/15) Success!")
    # (12/15)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        if option.name in interaction.options:
            assert isinstance(interaction.options[option.name], int)
            await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
        else:
            await interaction.send_response(f"You used /test with no argument")
    except Exception as e:
        log.info(f"Part 5 (12/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (12/15) Success!")
    # (13/15)
    try:
        option = ApplicationCommandOption.Integer(name="integer",
                                                 description="Mandatory integer argument with choices",
                                                 choices={"first" : 1, "second" : 2, "third" : 3})
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Optional integer argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 5 (13/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (13/15) Success!")
    # (14/15)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], int)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
    except Exception as e:
        log.info(f"Part 5 (14/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (14/15) Success!")
    # (15/15)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 5 (15/15) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 5 (15/15) Success!")

    # Part 6: Command with a boolean argument (1/10)
    try:
        option = ApplicationCommandOption.Boolean(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 6 (1/10) Success!")
    except Exception as e:
        log.info(f"Part 6 (1/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (1/10) Failure: {option} returned")
    # (2/10)
    try:
        option = ApplicationCommandOption.Boolean(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 6 (2/10) Success!")
    except Exception as e:
        log.info(f"Part 6 (2/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (2/10) Failure: {option} returned")
    # (3/10)
    try:
        option = ApplicationCommandOption.Boolean(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 6 (3/10) Success!")
    except Exception as e:
        log.info(f"Part 6 (3/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (3/10) Failure: {option} returned")
    # (4/10)
    try:
        option = ApplicationCommandOption.Boolean(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 6 (4/10) Success!")
    except Exception as e:
        log.info(f"Part 6 (4/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (4/10) Failure: {option} returned")
    # (5/10)
    try:
        option = ApplicationCommandOption.Boolean(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 6 (5/10) Success!")
    except Exception as e:
        log.info(f"Part 6 (5/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (5/10) Failure: {option} returned")
    # (6/10)
    try:
        option = ApplicationCommandOption.Boolean(name="boolean", description="Mandatory boolean argument")
        command = await guild.create_application_command(name="test", description="Use me to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 6 (6/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (6/10) Success!")
    # (7/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], bool)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
    except Exception as e:
        log.info(f"Part 6 (7/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (7/10) Success!")
    # (8/10)
    try:
        option = ApplicationCommandOption.Boolean(name="boolean", description="Optional boolean pargument", required=False)
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Mandatory boolean argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 6 (8/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (8/10) Success!")
    # (9/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        if option.name in interaction.options:
            assert isinstance(interaction.options[option.name], bool)
            await interaction.send_response(f"You used /test with '{interaction.options[option.name]}'")
        else:
            await interaction.send_response(f"You used /test with no argument")
    except Exception as e:
        log.info(f"Part 6 (9/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (9/10) Success!")
    # (10/10)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 6 (10/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 6 (10/10) Success!")

    # Part 7: Command with a user argument (1/10)
    try:
        option = ApplicationCommandOption.User(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 7 (1/10) Success!")
    except Exception as e:
        log.info(f"Part 7 (1/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (1/10) Failure: {option} returned")
    # (2/10)
    try:
        option = ApplicationCommandOption.User(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 7 (2/10) Success!")
    except Exception as e:
        log.info(f"Part 7 (2/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (2/10) Failure: {option} returned")
    # (3/10)
    try:
        option = ApplicationCommandOption.User(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 7 (3/10) Success!")
    except Exception as e:
        log.info(f"Part 7 (3/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (3/10) Failure: {option} returned")
    # (4/10)
    try:
        option = ApplicationCommandOption.User(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 7 (4/10) Success!")
    except Exception as e:
        log.info(f"Part 7 (4/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (4/10) Failure: {option} returned")
    # (5/10)
    try:
        option = ApplicationCommandOption.User(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 7 (5/10) Success!")
    except Exception as e:
        log.info(f"Part 7 (5/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (5/10) Failure: {option} returned")
    # (6/10)
    try:
        option = ApplicationCommandOption.User(name="user", description="Mandatory user argument")
        command = await guild.create_application_command(name="test", description="Use me to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 7 (6/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (6/10) Success!")
    # (7/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], User)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name].mention}'")
    except Exception as e:
        log.info(f"Part 7 (7/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (7/10) Success!")
    # (8/10)
    try:
        option = ApplicationCommandOption.User(name="user", description="Optional user pargument", required=False)
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Mandatory user argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 7 (8/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (8/10) Success!")
    # (9/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        if option.name in interaction.options:
            assert isinstance(interaction.options[option.name], User)
            await interaction.send_response(f"You used /test with '{interaction.options[option.name].mention}'")
        else:
            await interaction.send_response(f"You used /test with no argument")
    except Exception as e:
        log.info(f"Part 7 (9/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (9/10) Success!")
    # (10/10)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 7 (10/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 7 (10/10) Success!")

    # Part 8: Command with a channel argument (1/10)
    try:
        option = ApplicationCommandOption.Channel(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 8 (1/10) Success!")
    except Exception as e:
        log.info(f"Part 8 (1/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (1/10) Failure: {option} returned")
    # (2/10)
    try:
        option = ApplicationCommandOption.Channel(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 8 (2/10) Success!")
    except Exception as e:
        log.info(f"Part 8 (2/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (2/10) Failure: {option} returned")
    # (3/10)
    try:
        option = ApplicationCommandOption.Channel(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 8 (3/10) Success!")
    except Exception as e:
        log.info(f"Part 8 (3/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (3/10) Failure: {option} returned")
    # (4/10)
    try:
        option = ApplicationCommandOption.Channel(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 8 (4/10) Success!")
    except Exception as e:
        log.info(f"Part 8 (4/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (4/10) Failure: {option} returned")
    # (5/10)
    try:
        option = ApplicationCommandOption.Channel(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 8 (5/10) Success!")
    except Exception as e:
        log.info(f"Part 8 (5/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (5/10) Failure: {option} returned")
    # (6/10)
    try:
        option = ApplicationCommandOption.Channel(name="channel", description="Mandatory channel argument")
        command = await guild.create_application_command(name="test", description="Use me to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 8 (6/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (6/10) Success!")
    # (7/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], GuildChannel)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name].mention}'")
    except Exception as e:
        log.info(f"Part 8 (7/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (7/10) Success!")
    # (8/10)
    try:
        option = ApplicationCommandOption.Channel(name="channel", description="Optional channel pargument", required=False)
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Mandatory channel argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 8 (8/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (8/10) Success!")
    # (9/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        if option.name in interaction.options:
            assert isinstance(interaction.options[option.name], GuildChannel)
            await interaction.send_response(f"You used /test with '{interaction.options[option.name].mention}'")
        else:
            await interaction.send_response(f"You used /test with no argument")
    except Exception as e:
        log.info(f"Part 8 (9/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (9/10) Success!")
    # (10/10)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 8 (10/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 8 (10/10) Success!")

    # Part 9: Command with a role argument (1/10)
    try:
        option = ApplicationCommandOption.Role(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 9 (1/10) Success!")
    except Exception as e:
        log.info(f"Part 9 (1/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (1/10) Failure: {option} returned")
    # (2/10)
    try:
        option = ApplicationCommandOption.Role(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 9 (2/10) Success!")
    except Exception as e:
        log.info(f"Part 9 (2/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (2/10) Failure: {option} returned")
    # (3/10)
    try:
        option = ApplicationCommandOption.Role(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 9 (3/10) Success!")
    except Exception as e:
        log.info(f"Part 9 (3/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (3/10) Failure: {option} returned")
    # (4/10)
    try:
        option = ApplicationCommandOption.Role(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 9 (4/10) Success!")
    except Exception as e:
        log.info(f"Part 9 (4/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (4/10) Failure: {option} returned")
    # (5/10)
    try:
        option = ApplicationCommandOption.Role(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 9 (5/10) Success!")
    except Exception as e:
        log.info(f"Part 9 (5/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (5/10) Failure: {option} returned")
    # (6/10)
    try:
        option = ApplicationCommandOption.Role(name="role", description="Mandatory role argument")
        command = await guild.create_application_command(name="test", description="Use me to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 9 (6/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (6/10) Success!")
    # (7/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name], Role)
        await interaction.send_response(f"You used /test with '{interaction.options[option.name].mention}'")
    except Exception as e:
        log.info(f"Part 9 (7/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (7/10) Success!")
    # (8/10)
    try:
        option = ApplicationCommandOption.Role(name="role", description="Optional role pargument", required=False)
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert old_command.options[0].description == "Mandatory role argument"
        assert command == new_command
    except Exception as e:
        log.info(f"Part 9 (8/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (8/10) Success!")
    # (9/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        if option.name in interaction.options:
            assert isinstance(interaction.options[option.name], Role)
            await interaction.send_response(f"You used /test with '{interaction.options[option.name].mention}'")
        else:
            await interaction.send_response(f"You used /test with no argument")
    except Exception as e:
        log.info(f"Part 9 (9/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (9/10) Success!")
    # (10/10)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 9 (10/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 9 (10/10) Success!")

    # Part 10: Command with a sub command (1/10)
    try:
        option = ApplicationCommandOption.SubCommand(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 10 (1/10) Success!")
    except Exception as e:
        log.info(f"Part 10 (1/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (1/10) Failure: {option} returned")
    # (2/10)
    try:
        option = ApplicationCommandOption.SubCommand(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 10 (2/10) Success!")
    except Exception as e:
        log.info(f"Part 10 (2/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (2/10) Failure: {option} returned")
    # (3/10)
    try:
        option = ApplicationCommandOption.SubCommand(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 10 (3/10) Success!")
    except Exception as e:
        log.info(f"Part 10 (3/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (3/10) Failure: {option} returned")
    # (4/10)
    try:
        option = ApplicationCommandOption.SubCommand(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 10 (4/10) Success!")
    except Exception as e:
        log.info(f"Part 10 (4/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (4/10) Failure: {option} returned")
    # (5/10)
    try:
        option = ApplicationCommandOption.SubCommand(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 10 (5/10) Success!")
    except Exception as e:
        log.info(f"Part 10 (5/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (5/10) Failure: {option} returned")
    # (6/10)
    try:
        option = ApplicationCommandOption.SubCommand(name="sub", description="Use me to test")
        command = await guild.create_application_command(name="test", description="Use sub to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 10 (6/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (6/10) Success!")
    # (7/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert option.name in interaction.options
        await interaction.send_response(f"You used /test sub")
    except Exception as e:
        log.info(f"Part 10 (7/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (7/10) Success!")
    # (8/10)
    try:
        suboption = ApplicationCommandOption.String(name="string", description="A string argument")
        option = ApplicationCommandOption.SubCommand(name="sub", description="Use me to test", options=[suboption])
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert len(old_command.options[0].options) == 0
        assert command == new_command
    except Exception as e:
        log.info(f"Part 10 (8/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (8/10) Success!")
    # (9/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name][suboption.name], str)
        await interaction.send_response(f"You used /test sub with '{interaction.options[option.name][suboption.name]}'")
    except Exception as e:
        log.info(f"Part 10 (9/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (9/10) Success!")
    # (10/10)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 10 (10/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 10 (10/10) Success!")

    # Part 11: Command with a sub command group (1/10)
    try:
        option = ApplicationCommandOption.SubCommandGroup(name="", description="tmp")
    except InvalidArgument:
        log.info(f"Part 11 (1/10) Success!")
    except Exception as e:
        log.info(f"Part 11 (1/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (1/10) Failure: {option} returned")
    # (2/10)
    try:
        option = ApplicationCommandOption.SubCommandGroup(name="tmp" * 11, description="tmp")
    except InvalidArgument:
        log.info(f"Part 11 (2/10) Success!")
    except Exception as e:
        log.info(f"Part 11 (2/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (2/10) Failure: {option} returned")
    # (3/10)
    try:
        option = ApplicationCommandOption.SubCommandGroup(name="tmp?", description="tmp")
    except InvalidArgument:
        log.info(f"Part 11 (3/10) Success!")
    except Exception as e:
        log.info(f"Part 11 (3/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (3/10) Failure: {option} returned")
    # (4/10)
    try:
        option = ApplicationCommandOption.SubCommandGroup(name="tmp", description="")
    except InvalidArgument:
        log.info(f"Part 11 (4/10) Success!")
    except Exception as e:
        log.info(f"Part 11 (4/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (4/10) Failure: {option} returned")
    # (5/10)
    try:
        option = ApplicationCommandOption.SubCommandGroup(name="tmp", description="tmp" * 34)
    except InvalidArgument:
        log.info(f"Part 11 (5/10) Success!")
    except Exception as e:
        log.info(f"Part 11 (5/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (5/10) Failure: {option} returned")
    # (6/10)
    try:
        suboption = ApplicationCommandOption.SubCommand(name="sub", description="Use me to test")
        option = ApplicationCommandOption.SubCommandGroup(name="group", description="Use sub to test", options=[suboption])
        command = await guild.create_application_command(name="test", description="Use group sub to test", options=[option])
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 11 (6/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (6/10) Success!")
    # (7/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert suboption.name in interaction.options[option.name]
        await interaction.send_response(f"You used /test group sub")
    except Exception as e:
        log.info(f"Part 11 (7/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (7/10) Success!")
    # (8/10)
    try:
        subsuboption = ApplicationCommandOption.String(name="string", description="A string argument")
        suboption = ApplicationCommandOption.SubCommand(name="sub", description="Use me to test", options=[subsuboption])
        option = ApplicationCommandOption.SubCommandGroup(name="group", description="Use sub to test", options=[suboption])
        await command.edit(options=[option])
        old_command, new_command = await command_update_queue.get()
        # assert len(old_command.options[0].options[0].options) == 0
        assert command == new_command
    except Exception as e:
        log.info(f"Part 11 (8/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (8/10) Success!")
    # (9/10)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        assert isinstance(interaction.options[option.name][suboption.name][subsuboption.name], str)
        await interaction.send_response(f"You used /test group sub with '{interaction.options[option.name][suboption.name][subsuboption.name]}'")
    except Exception as e:
        log.info(f"Part 11 (9/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (9/10) Success!")
    # (10/10)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 11 (10/10) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 11 (10/10) Success!")

    # Part 12: All possible interaction responses (1/13)
    try:
        command = await guild.create_application_command(name="test", description="Use me 11 times")
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 12 (1/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (1/13) Success!")
    # (2/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response("Publicly visible response")
    except Exception as e:
        log.info(f"Part 12 (2/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (2/13) Success!")
    # (3/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response("Ephemeral response", ephemeral=True)
    except Exception as e:
        log.info(f"Part 12 (3/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (3/13) Success!")
    # (4/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response(None)
        await sleep(3)
        await interaction.edit_response(content="Delayed publicly visible response")
    except Exception as e:
        log.info(f"Part 12 (4/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (4/13) Success!")
    # (5/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response(None, ephemeral=True)
        await sleep(3)
        await interaction.edit_response(content="Delayed ephemeral response")
    except Exception as e:
        log.info(f"Part 12 (5/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (5/13) Success!")
    # (6/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response("Text to speech response", tts=True)
    except Exception as e:
        log.info(f"Part 12 (6/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (6/13) Success!")
    # (7/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        embed = Embed(title="Embed response")
        await interaction.send_response(embed=embed)
    except Exception as e:
        log.info(f"Part 12 (7/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (7/13) Success!")
    # (8/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        embed = Embed(title="Embeds response")
        await interaction.send_response(embeds=[embed])
    except Exception as e:
        log.info(f"Part 12 (8/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (8/13) Success!")
    # (9/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response("Attempting to respond twice")
        await interaction.send_response("The second response")
    except InvalidArgument:
        log.info(f"Part 12 (9/13) Success!")
    except Exception as e:
        log.info(f"Part 12 (9/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (9/13) Failure: Second response worked")
    # (10/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        embed = Embed(title="Test embed")
        await interaction.send_response(embed=embed, embeds=[embed])
    except InvalidArgument:
        await interaction.send_response("Internal test")
        log.info(f"Part 12 (10/13) Success!")
    except Exception as e:
        log.info(f"Part 12 (10/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (10/13) Failure: Combining embed and embeds worked")
    # (11/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        embed = Embed(title="Test embed")
        await interaction.send_response(embeds=[embed for i in range(11)])
    except InvalidArgument:
        await interaction.send_response("Internal test")
        log.info(f"Part 12 (11/13) Success!")
    except Exception as e:
        log.info(f"Part 12 (11/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (11/13) Failure: Embeds too long was accepted")
    # (12/13)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.send_response("Last response of this iteration of /test")
    except Exception as e:
        log.info(f"Part 12 (12/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (12/13) Success!")
    # (13/13)
    try:
        await command.delete()
        assert command == await command_delete_queue.get()
    except Exception as e:
        log.info(f"Part 12 (13/13) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 12 (13/13) Success!")

    # Part 13: Following up on interactions (1/33)
    try:
        command = await guild.create_application_command(name="test", description="Use me and wait")
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 13 (1/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (1/33) Success!")
    # (2/33)
    try:
        interaction = await interaction_queue.get()
        assert command == interaction.command
        await interaction.edit_response(content="Failed edit")
    except InvalidArgument:
        log.info(f"Part 13 (2/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (2/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (2/33) Failure: Could edit non-existent response")
    # (3/33)
    try:
        await interaction.send_response("Initial response")
    except Exception as e:
        log.info(f"Part 13 (3/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (3/33) Success!")
    # (4/33)
    try:
        await sleep(3)
        await interaction.edit_response(content="Changed response")
    except Exception as e:
        log.info(f"Part 13 (4/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (4/33) Success!")
    # (5/33)
    try:
        await sleep(3)
        embed = Embed(title="Added embed")
        await interaction.edit_response(embed=embed)
    except Exception as e:
        log.info(f"Part 13 (5/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (5/33) Success!")
    # (6/33)
    try:
        await sleep(3)
        embed = Embed(title="Another embed")
        await interaction.edit_response(embeds=[embed])
    except Exception as e:
        log.info(f"Part 13 (6/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (6/33) Success!")
    # (7/33)
    try:
        embed = Embed(title="Failed embed")
        await interaction.edit_response(embed=embed, embeds=[embed])
    except InvalidArgument:
        log.info(f"Part 13 (7/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (7/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (7/33) Failure: Could use both embed and embeds")
    # (8/33)
    try:
        embed = Embed(title="Failed embed")
        await interaction.edit_response(embeds=[embed for i in range(11)])
    except InvalidArgument:
        log.info(f"Part 13 (8/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (8/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (8/33) Failure: Could use too many embeds")
    # (9/33)
    try:
        await sleep(3)
        await interaction.edit_response(content=None)
    except Exception as e:
        log.info(f"Part 13 (9/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (9/33) Success!")
    # (10/33)
    try:
        await sleep(3)
        await interaction.edit_response(content="Final response")
    except Exception as e:
        log.info(f"Part 13 (10/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (10/33) Success!")
    # (11/33)
    try:
        await sleep(3)
        await interaction.edit_response(embeds=None)
    except Exception as e:
        log.info(f"Part 13 (11/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (11/33) Success!")
    # (12/33)
    try:
        await sleep(3)
        await interaction.delete_response()
    except Exception as e:
        log.info(f"Part 13 (12/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (12/33) Success!")
    # (13/33)
    try:
        await interaction.send_message("Text message")
    except Exception as e:
        log.info(f"Part 13 (13/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (13/33) Success!")
    # (14/33)
    try:
        await interaction.send_message("Ephemeral message", ephemeral=True)
    except Exception as e:
        log.info(f"Part 13 (14/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (14/33) Success!")
    # (15/33)
    try:
        await interaction.send_message("Text to speech message", tts=True)
    except Exception as e:
        log.info(f"Part 13 (15/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (15/33) Success!")
    # (16/33)
    try:
        embed = Embed(title="An embed")
        await interaction.send_message("Embed message", embed=embed)
    except Exception as e:
        log.info(f"Part 13 (16/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (16/33) Success!")
    # (17/33)
    try:
        embed = Embed(title="An embed")
        await interaction.send_message("Embeds message", embeds=[embed])
    except Exception as e:
        log.info(f"Part 13 (17/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (17/33) Success!")
    # (18/33)
    try:
        embed = Embed(title="Failed embed")
        await interaction.send_message("Failed message", embed=embed, embeds=[embed])
    except InvalidArgument:
        log.info(f"Part 13 (18/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (18/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (18/33) Failure: Could use embed and embeds")
    # (19/33)
    try:
        embed = Embed(title="Failed embed")
        await interaction.send_message("Failed message", embeds=[embed for i in range(11)])
    except InvalidArgument:
        log.info(f"Part 13 (19/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (19/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (19/33) Failure: Could provide too many embeds")
    # (20/33)
    try:
        f = File("tmp.txt")
        await interaction.send_message("File message", file=f)
    except Exception as e:
        log.info(f"Part 13 (20/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (20/33) Success!")
    # (21/33)
    try:
        f = File("tmp.txt")
        await interaction.send_message("File message", files=[f])
    except Exception as e:
        log.info(f"Part 13 (21/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (21/33) Success!")
    # (22/33)
    try:
        f = File("tmp.txt")
        await interaction.send_message("Failed message", file=f, files=[f])
    except InvalidArgument:
        log.info(f"Part 13 (22/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (22/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (22/33) Failure: Could combine file and files")
    # (23/33)
    try:
        message = await interaction.send_message("Initial message")
    except Exception as e:
        log.info(f"Part 13 (23/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (23/33) Success!")
    # (24/33)
    try:
        await sleep(3)
        await message.edit(content="Changed message")
    except Exception as e:
        log.info(f"Part 13 (24/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (24/33) Success!")
    # (25/33)
    try:
        await sleep(3)
        embed = Embed(title="Added embed")
        await message.edit(embed=embed)
    except Exception as e:
        log.info(f"Part 13 (25/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (25/33) Success!")
    # (26/33)
    try:
        await sleep(3)
        embed = Embed(title="Another embed")
        await message.edit(embeds=[embed])
    except Exception as e:
        log.info(f"Part 13 (26/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (26/33) Success!")
    # (27/33)
    try:
        embed = Embed(title="Failed embed")
        await message.edit(embed=embed, embeds=[embed])
    except InvalidArgument:
        log.info(f"Part 13 (27/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (27/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (27/33) Failure: Could use both embed and embeds")
    # (28/33)
    try:
        embed = Embed(title="Failed embed")
        await message.edit(embeds=[embed for i in range(11)])
    except InvalidArgument:
        log.info(f"Part 13 (28/33) Success!")
    except Exception as e:
        log.info(f"Part 13 (28/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (28/33) Failure: Could use too many embeds")
    # (29/33)
    try:
        await sleep(3)
        await message.edit(content=None)
    except Exception as e:
        log.info(f"Part 13 (29/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (29/33) Success!")
    # (30/33)
    try:
        await sleep(3)
        await message.edit(content="Final response")
    except Exception as e:
        log.info(f"Part 13 (30/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (30/33) Success!")
    # (31/33)
    try:
        await sleep(3)
        await message.edit(embeds=None)
    except Exception as e:
        log.info(f"Part 13 (31/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (31/33) Success!")
    # (32/33)
    try:
        await sleep(3)
        await message.delete()
    except Exception as e:
        log.info(f"Part 13 (32/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (32/33) Success!")
    # (32/33)
    try:
        await command.delete()
    except Exception as e:
        log.info(f"Part 13 (33/33) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 13 (33/33) Success!")

    # Part 14: Checking command registration (1/3)
    try:
        command = await guild.create_application_command(name='test', description='Do not use me')
        assert command == await command_create_queue.get()
    except Exception as e:
        log.info(f"Part 14 (1/3) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 14 (1/3) Success!")
    # (2/3)
    try:
        commands = await guild.fetch_application_commands()
        assert command in commands
        assert command in guild.application_commands
        assert command == guild.get_application_command(command.id)
    except Exception as e:
        log.info(f"Part 14 (2/3) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 14 (2/3) Success!")
    # (3/3)
    try:
        assert command in client.application_commands
        assert command == client.get_application_command(command.id)
    except Exception as e:
        log.info(f"Part 14 (3/3) Failure: {type(e)}: {e}")
    else:
        log.info(f"Part 14 (3/3) Success!")

with open('token.txt') as tokenFile:
    client.run(tokenFile.read())
    
