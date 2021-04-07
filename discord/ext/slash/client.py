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
from .core import SlashCommand, SlashCommandRegistrationError, command

COMMAND_LIMIT = 100

class SlashClient(Client):
    """Represents a client that handles slash commands."""
    def __init__(self, **options):
        super().__init__(**options)
        self._commands = {}

    def dispatch(self, event_name, *args, **kwargs):
        if event_name == 'ready':
            self._schedule_event(self._sync_commands, 'on_' + event_name, *args, **kwargs)
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

    def command(self, guild_id=None, **kwargs):
        """A shortcut decorator that invokes :func:`.command` and adds the
        command to the internal list of commands.
        """
        def decorator(func):
            wrapped = command(**kwargs)(func)
            self.add_command(wrapped, guild_id=guild_id)
            return wrapped
        return decorator

    async def _sync_guild_commands(self, guild):
        commands_copy = copy.copy(self._commands.get(guild.id, {}))
        for app_command in await guild.fetch_application_commands():
            try:
                command = commands_copy.pop(app_command.name)
            except KeyError:
                await app_command.delete()
            else:
                if not (app_command.name == command.name and
                        app_command.description == command.description and
                        app_command.options == command.options):
                    await app_command.edit(name=command.name, description=command.description, options=command.options)

        for command in commands_copy.values():
            await guild.create_application_command(name=command.name, description=command.description, options=command.options)
        
    async def _sync_global_commands(self):
        commands_copy = copy.copy(self._commands.get(None, {}))
        for app_command in await self.fetch_global_commands():
            try:
                command = commands_copy.pop(app_command.name)
            except KeyError:
                await app_command.delete()
            else:
                if not (app_command.name == command.name and
                        app_command.description == command.description and
                        app_command.options == command.options):
                    await app_command.edit(name=command.name, description=command.description, options=command.options)

        for command in commands_copy.values():
            await self.create_global_command(name=command.name, description=command.description, options=command.options)
    
    async def _sync_commands(self):
        await self._sync_global_commands()
        for guild in self.guilds:
            await self._sync_guild_commands(guild)

    async def on_interaction(self, interaction):
        if interaction.type == InteractionType.ping:
            await interaction.send_response()
            
        if interaction.type == InteractionType.application_command:
            name = interaction.command.name
            guild_id = interaction.command.guild and interaction.command.guild.id
            command = self.get_command(name, guild_id=guild_id)
            if command is None:
                await interaction.send_response("No implementation available", ethemeral=True)
            result = await command.invoke(interaction=interaction, options=interaction.options, client=self)
            if not interaction.responded:
                if result:
                    await interaction.send_response(result)
                else:
                    await interaction.send_response("Command had no response", ethemeral=True)
