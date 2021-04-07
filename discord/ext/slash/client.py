# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2021-present Trainjo

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import copy

from discord import Client
from discord.enums import InteractionType
from .core import SlashCommand, SlashCommandRegistrationError

COMMAND_LIMIT = 100

class SlashClient(Client):
    """Represents a client that handles slash commands."""
    def __init__(self, **options):
        super().__init__(**options)
        self._commands = {}

    def dispatch(self, event_name, *args, **kwargs):
        if event_name == 'ready':
            self._schedule_event(self._sync_commands(), 'on_' + event_name, *args, **kwargs)
        super().dispatch(event_name, *args, **kwargs)

    def add_command(self, command, guild_id=None):
        """Adds a :class:`.SlashCommand` into the internal list of commands.

        Parameters
        -----------
        command: :class:`SlashCommand`
            The command to add.
        guild_id: Optional[:class:`int`]
            The ID of the guild for which the command should work.
            Use `None` for global commands.
        """
        if not isinstance(command, SlashCommand):
            raise TypeError(f"The command '{command}' passed is not a command.")

        if not guild_id in self._commands:
            self._commands[guild_id] = {}

        if command.name in self._commands[guild_id]:
            raise SlashCommandRegistrationError("A command with name '{command.name}' already exists in the command group.")

        if len(self._commands[guild_id]) >= COMMAND_LIMIT:
            raise SlashCommandRegistrationError("Can not add command to group that already has {COMMAND_GROUP_LIMIT} commands.")

        self._commands[guild_id][command.name] = command

    def remove_command(self, name, guild_id=None):
        """Remove a :class:`SlashCommand` from the internal list of commands.
        
        Parameters
        -----------
        name: :class:`str`
            The name of the command to remove.
        guild_id: Optional[:class:`int`]
            The ID of the guild for which the command should work.
            Use `None` for global commands.

        Returns
        --------
        Optional[:class:`SlashCommand`]
            The command that was removed. If no command with given name
            existed ``None`` is returned instead.
        """
        try:
            return self._commands[guild_id].pop(name, None)
        except KeyError:
            return None

    def get_command(self, name, guild_id=None):
        """Get a :class:`.SlashCommand` from the internal list of commands.

        Parameters
        -----------
        name: :class:`str`
            The name of the command to get.
        guild_id: Optional[:class:`int`]
            The ID of the guild for which the command should work.
            Use `None` for global commands.

        Returns
        --------
        Optional[:class:`.SlashCommand`]
            The requested command, if found.

        """
        try:
            return self._commands[guild_id][name]
        except KeyError:
            return None

    def command(self, func, guild_id=None, **kwargs):
        """A shortcut decorator that invokes :func:`.command` and adds the
        command to the internal list of commands.
        """
        command = command(func, **kwargs)
        self.add_command(command, guild_id=guild_id)
        return command

    async def _sync_guild_commands(self, guild):
        commands_copy = copy.copy(self._commands.get(guild.id, {}))
        for app_command in guild.fetch_application_commands():
            try:
                command = commands_copy.pop(app_command.name)
            except KeyError:
                await app_command.delete()
            else:
                option = command.to_option()
                if not (app_command.name == option['name'] and
                        app_command.description == option['description'] and
                        app_command.options == option['options']):
                    await app_command.edit(**option)

        for command in commands_copy:
            await guild.create_application_command(**command.to_option())
        
    async def _sync_global_commands(self):
        commands_copy = copy.copy(self._commands.get(None, {}))
        for app_command in client.fetch_global_commands():
            try:
                command = commands_copy.pop(app_command.name)
            except KeyError:
                await app_command.delete()
            else:
                option = command.to_option()
                if not (app_command.name == option['name'] and
                        app_command.description == option['description'] and
                        app_command.options == option['options']):
                    await app_command.edit(**option)

        for command in commands_copy:
            await client.create_global_command(**command.to_option())
    
    async def _sync_commands(self):
        await self._sync_global_commands()
        for guild in self.guilds:
            await self._sync_guild_commands(guild)

    async def on_interaction(self, interaction):
        if interaction.type == InteractionType.ping:
            await interaction.send_response()
            
        if interaction.type == InteractionType.command:
            command = self._commands[interaction.command.guild][interaction.command.name]
            result = await command.invoke(interaction, **interaction.options)
            if not interaction.responded:
                interaction.send_response(result)
