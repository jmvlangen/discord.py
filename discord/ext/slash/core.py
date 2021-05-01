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

import asyncio
import inspect
import itertools
import re

from discord.user import User
from discord.member import Member
from discord.abc import GuildChannel
from discord.channel import TextChannel, VoiceChannel, CategoryChannel
from discord.role import Role
from discord.command import is_valid_name, is_valid_description, is_valid_choice_name, is_valid_choice_value
from discord.command import ApplicationCommandOption
from discord.errors import DiscordException

COMMAND_GROUP_LIMIT = 25
COMMAND_CHOICE_LIMIT = 25

INDENT_PATTERN = re.compile("\s+")
NAME_PATTERN = re.compile("[\w-]+")
TYPE_PATTERN = re.compile("\s*:\s*(.+)")
CHOICE_PATTERN = re.compile("-(.+):(.+)")

class Argument:
    """An argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    def __init__(self, *, name, description, required=True):
        if not is_valid_name(name):
            raise TypeError("The name '{name}' is not a valid name for a command argument.")
        if not is_valid_description(description):
            raise TypeError("The description '{description}' is not a valid description for a command argument.")
        
        self.name = name
        self.description = description
        self.required = required

    def to_option(self):
        """Give this command argument as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.string` by
        default. Overwrite this method for a different type.

        """
        return ApplicationCommandOption.string(name=self.name, description=self.description, required=self.required)

    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to the correct type in case it was given for this argument.

        Overwrite this method to get custom argument types.
        """
        return str(value)

class StringArgument(Argument):
    """A string argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.
    choices: Mapping[:class:`str`, :class`str`]
        A mapping of choice names to their corresponding values.
        Is empty if there are no choices.

    """
    def __init__(self, *, name, description, required=True, choices=None):
        super().__init__(name=name, description=description, required=required)

        if choices is None:
            choices = {}
        if len(choices) > COMMAND_CHOICE_LIMIT:
            raise TypeError(f"The number of choices of a command argument can not exceed {COMMAND_CHOICE_LIMIT}.")
        for name, value in choices.items():
            if not is_valid_choice_name(name):
                raise TypeError(f"The name '{name}' is invalid for a choice")
            if not is_valid_choice_value(value):
                raise TypeError(f"The value '{value}' is invalid for a choice")

        self.choices = choices

    def to_option(self):
        """Give this command argument as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.string`.

        """
        return ApplicationCommandOption.string(name=self.name, description=self.description,
                                               required=self.required, choices=self.choices)

class IntegerArgument(Argument):
    """An integer argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.
    choices: Mapping[:class:`str`, :class`int`]
        A mapping of choice names to their corresponding values.
        Is empty if there are no choices.

    """
    def __init__(self, *, name, description, required=True, choices=None):
        super().__init__(name=name, description=description, required=required)

        if choices is None:
            choices = {}
        if len(choices) > COMMAND_CHOICE_LIMIT:
            raise TypeError(f"The number of choices of a command argument can not exceed {COMMAND_CHOICE_LIMIT}.")
        for name, value in choices.items():
            if not is_valid_choice_name(name):
                raise TypeError(f"The name '{name}' is invalid for a choice")
            if not isinstance(value, int):
                raise TypeError(f"The value '{value}' is invalid for a choice")

        self.choices = choices

    def to_option(self):
        """Give this command argument as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.integer`.

        """
        return ApplicationCommandOption.integer(name=self.name, description=self.description,
                                                required=self.required, choices=self.choices)

    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to an integer."""
        return int(value)

class BooleanArgument(Argument):
    """A boolean argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """

    def to_option(self):
        """Give this command argument as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.boolean`

        """
        return ApplicationCommandOption.boolean(name=self.name, description=self.description, required=self.required)

    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a boolean."""
        return bool(value)

class UserArgument(Argument):
    """A User argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    def to_option(self):
        """Give this command argument as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.user`

        """
        return ApplicationCommandOption.user(name=self.name, description=self.description, required=self.required)

    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a :class:`User`."""
        if isinstance(value, User) or isinstance(value, Member):
            return value

        if not isinstance(value, int):
            value = int(value)
            
        if guild is not None:
            member = guild.get_member(value)
            if member is None:
                member = await guild.fetch_member(value)
            return member

        if client is not None:
            user = client.get_user(value)
            if user is None:
                user = await client.fetch_user(value)
            return user

        raise ArgumentError(f"Can not convert {value} to a user when missing client and guild.")

class MemberArgument(UserArgument):
    """A Member argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a :class:`Member`."""
        if isinstance(value, Member):
            return value

        if isinstance(value, User):
            user_id = value.id
        else:
            user_id = int(value)
            
        if guild is not None:
            member = guild.get_member(user_id)
            if member is None:
                member = await guild.fetch_member(user_id)
            return member

        raise ArgumentError(f"Can not convert {value} into a Member when missing a guild.")

class ChannelArgument(Argument):
    """A Channel argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    def to_option(self):
        """Give this command argument as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.channel`

        """
        return ApplicationCommandOption.channel(name=self.name, description=self.description, required=self.required)

    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a :class:`GuildChannel`."""
        if isinstance(value, GuildChannel):
            return value

        if not isinstance(value, int):
            value = int(value)
            
        if guild is not None:
            channel = guild.get_channel(value)
            if channel is None:
                channel = await guild.fetch_channel(value)
            return channel

        if channel is not None:
            channel = client.get_channel(value)
            if channel is None:
                channel = await client.fetch_channel(value)
            return channel

        raise ArgumentError(f"Can not convert {value} to a channel when missing client and guild.")

class TextChannelArgument(ChannelArgument):
    """A TextChannel argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a :class:`TextChannel`."""
        channel = super().convert(value, client=client, guild=guild)
        
        if not isinstance(channel, TextChannel):
            raise ArgumentError(f"The given channel {value} is not a TextChannel.")

        return channel

class VoiceChannelArgument(ChannelArgument):
    """A VoiceChannel argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a :class:`VoiceChannel`."""
        channel = super().convert(value, client=client, guild=guild)
        
        if not isinstance(channel, VoiceChannel):
            raise ArgumentError(f"The given channel {value} is not a VoiceChannel.")

        return channel

class CategoryChannelArgument(ChannelArgument):
    """A CategoryChannel argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a :class:`CategoryChannel`."""
        channel = super().convert(value, client=client, guild=guild)
        
        if not isinstance(channel, TextChannel):
            raise ArgumentError(f"The given channel {value} is not a CategoryChannel.")

        return channel

class RoleArgument(Argument):
    """A User argument of a :class:`.SlashCommand`

    Attributes
    -----------
    name: :class:`str`
        The name of this argument.
    description: :class:`str`
        The description of this argument.
    required: :class: `bool`
        Whether this argument is required or optional.

    """
    def to_option(self):
        """Give this command argument as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.role`

        """
        return ApplicationCommandOption.role(name=self.name, description=self.description, required=self.required)

    async def convert(self, value, *, client=None, guild=None):
        """Convert ``value`` to a :class:`Role`."""
        if isinstance(value, Role):
            return value

        if not isinstance(value, int):
            value = int(value)
            
        if guild is not None:
            role = guild.get_role(value)
            if role is None:
                await guild.fetch_roles()
            return guild.get_role(value)

        raise ArgumentError(f"Can not convert {value} to a role when missing a guild.")

ARGUMENT_CLASS_DICT = {
    str : StringArgument,
    int : IntegerArgument,
    bool : BooleanArgument,
    User : UserArgument,
    Member : MemberArgument,
    GuildChannel : ChannelArgument,
    TextChannel : TextChannelArgument,
    VoiceChannel : VoiceChannelArgument,
    CategoryChannel : CategoryChannelArgument,
    Role : RoleArgument,
}

def _parse_command_doc(doc):
    doc = inspect.cleandoc(doc)

    lineIterator = iter(doc.splitlines())
    try:
        description = next(lineIterator).strip()
    except StopIteration:
        description = ""

    for line in lineIterator:
        line = line.strip()
        if len(line) == 0:
            break
        description += " " + line

    arg_types = {}
    arg_block = {}

    lastline = ""
    for line in lineIterator:
        arg_name = NAME_PATTERN.match(lastline)
        indent1 = INDENT_PATTERN.match(line)
        if not (indent1 and arg_name):
            lastline = line
            continue
        
        arg_name = arg_name.group()
        indent1 = indent1.group()
        nameline = lastline[len(arg_name):]
        arg_block[arg_name] = line[len(indent1):]
        
        arg_type = TYPE_PATTERN.match(nameline)
        if arg_type:
            arg_types[arg_name] = arg_type.group(1)
        
        for line in lineIterator:
            if not line.startswith(indent1):
                lastline = line
                break

            arg_block[arg_name] += "\n" + line[len(indent1):]
            
    arg_descriptions = {}
    arg_choices = {}
    
    for arg_name, block in arg_block.items():
        lineIterator = iter(block.splitlines())
        try:
            arg_descriptions[arg_name] = next(lineIterator).strip()
        except StopIteration:
            arg_descriptions[arg_name] = ""

        arg_choice_dict = {}
        choice_block = None
        for line in lineIterator:
            if line.startswith("-"):
                if choice_block:
                    choice_match = CHOICE_PATTERN.fullmatch(choice_block)
                    if choice_match:
                        choice_name = choice_match.group(1).strip()
                        choice_value = choice_match.group(2).strip()
                        arg_choice_dict[choice_name] = choice_value
                        
                choice_block = line.strip()

            elif choice_block:
                choice_block += " " + line.strip()
            else:
                arg_descriptions[arg_name] += " " + line.strip()

        if len(arg_choice_dict) > 0:
            arg_choices[arg_name] = arg_choice_dict
                
    return description, arg_types, arg_descriptions, arg_choices

def _get_argument_class(type_):
    if type_ in ARGUMENT_CLASS_DICT:
        return ARGUMENT_CLASS_DICT[type_]
    else:
        return type_

class SlashCommandError(DiscordException):
    pass

class SlashCommandRegistrationError(DiscordException):
    pass

class ArgumentError(DiscordException):
    pass

class SlashCommandParseError(SlashCommandError):
    pass

class SlashCommand:
    r"""An implementation of a Discord slash command.

    You should create commands using the appropriate decorator.

    .. container:: operations
    
        ..describe:: x == y
    
            Checks if two commands are equal.

        ..describe:: x != y

            Checks if two commands are not equal.
    
    Attributes
    ----------
    parent: Optional[:class:`Group`]
        The group this command belongs to if any.
    name: :class:`str`
        The name of this command.
    description: :class:`str`
        The description of this command.
    arguments: List[:class:`.Argument`]
        A list of arguments for this command in the order they should be provided.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the command is called.

    """
    def __init__(self, func, **kwargs):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        self.name = kwargs.get('name') or func.__name__
        if not is_valid_name(self.name):
            raise TypeError(f"Command name '{self.name}' is invalid.")

        self._callback = func

        description, arg_types, arg_descriptions, arg_choices = _parse_command_doc(inspect.getdoc(func))

        self.description = kwargs.get(description) or description
        if not is_valid_description(description):
            raise TypeError(f"Command description '{self.description}' is invalid.")

        arg_types = {**arg_types, **kwargs.get('arg_types', {})}
        arg_descriptions = {**arg_descriptions, **kwargs.get('arg_descriptions', {})}
        arg_choices = {**arg_choices, **kwargs.get('arg_choices', {})}
        
        signature = inspect.signature(func)

        params = iter(signature.parameters.items())
        try:
            name, param = next(params)
        except StopIteration:
            raise TypeError("Command coroutine requires at least one argument for the interaction.")
        else:
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                raise TypeError("Command coroutine does not support capturing all positional arguments, like with '*args*'")

        self.arguments = []
        add_additional = False
        for name, param in params:
            if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                raise TypeError("Command coroutine does not support positional only arguments.")
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                raise TypeError("Command coroutine does not support capturing all positional arguments, like with '*args*'")
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                add_additional = True
                continue

            required = (param.default == inspect.Parameter.empty)
            
            type_ = arg_types.pop(name, None) or param.annotation
            if isinstance(type_, str):
                type_ = eval(type_, func.__globals__)
                
            cls = _get_argument_class(type_)
            if not issubclass(cls, Argument):
                raise TypeError(f"The type of the argument '{name}' must be a subclass of Argument, not {cls}")

            choices = arg_choices.pop(name, None)
            if choices:
                argument = cls(name=name, description=arg_descriptions.pop(name, None), required=required, choices=choises)
            else:
                argument = cls(name=name, description=arg_descriptions.pop(name, None), required=required)
            self.arguments.append(argument)

        if add_additional:
            names = []
            for name in itertools.chain(arg_types.keys(), arg_descriptions.keys(), arg_choices.keys()):
                if name not in names:
                    names.append(name)

            for name in names:
                type_ = arg_types.pop(name, None)
                if isinstance(type_, str):
                    type_ = eval(type_, func.__globals__)

                cls = _get_argument_class(type_)
                if not isinstance(cls, Argument):
                    raise TypeError(f"The type of the argument '{name}' must be a subclass of Argument, not {type_}")

                choices = arg_choices.pop(name, None)
                if choices:
                    argument = cls(name=name, description=arg_descriptions.pop(name, None), required=False, choices=choises)
                else:
                    argument = cls(name=name, description=arg_descriptions.pop(name, None), required=False)
                self.arguments.append(argument)

    @property
    def callback(self):
        return self._callback

    def __call__(self, *args, **kwargs):
        """|coro|

        Calls the internal callback of the command.
        """
        return self.callback(*args, **kwargs)

    async def invoke(self, *, interaction, options, client):
        try:
            args = {arg.name : await arg.convert(options[arg.name], client=client, guild=interaction.guild)
                    for arg in self.arguments if arg.name in options}
        except KeyError as e:
            raise SlashCommandError(f"Command {self.name} is missing argument '{e}'")
        return await self(interaction, **args)

    @property
    def options(self):
        """List[:class:`ApplicationCommandOption`] The options of this command"""
        return [arg.to_option() for arg in self.arguments]

    def to_option(self):
        """Give this command as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.sub_command`

        """
        return ApplicationCommandOption.sub_command(name=self.name, description=self.description,
                                                    options=self.options)

class SlashGroup(SlashCommand):
    """An implementation of a Discord slash command group.

    Note that this group may be what discord calls a command if it is at
    the top level.
    
    Attributes
    ----------
    parent: Optional[:class:`.SlashGroup`]
         The group this command group belongs to if any.
    name: :class:`str`
         The name of this command group.
    description: :class:`str`
         The description of this command group.

    """
    def __init__(self, *, name, description):
        if not is_valid_name(name):
            raise TypeError(f"The name '{name}' is not valid for a command group.")
        if not is_valid_description(description):
            raise TypeError(f"The description '{description}' is not valid for a command group.")

        self.name = name
        self.description = description
        self.all_commands = {}

    @property
    def commands(self):
        """Set[:class:`.SlashCommand`]: A unique set of commands that are registered."""
        return set(self.all_commands.values())

    @property
    def options(self):
        """List[:class:`ApplicationCommandOption`] The options of this command"""
        return [command.to_option() for command in self.commands]

    def add_command(self, command):
        """Adds a :class:`.SlashCommand` into the internal list of commands.

        Parameters
        -----------
        command: :class:`.SlashCommand`
            The command to add.
        """
        if not isinstance(command, SlashCommand):
            raise TypeError(f"The command '{command}' passed is not a command.")

        if isinstance(self, SlashGroup):
            command.parent = self

        if command.name in self.all_commands:
            raise SlashCommandRegistrationError("A command with name '{command.name}' already exists in the command group.")

        if len(self.all_commands) >= COMMAND_GROUP_LIMIT:
            raise SlashCommandRegistrationError("Can not add command to group that already has {COMMAND_GROUP_LIMIT} commands.")

        self.all_commands[command.name] = command

    def remove_command(self, name):
        """Remove a :class:`.SlashCommand` from the internal list of commands.
        
        Parameters
        -----------
        name: :class:`str`
            The name of the command to remove.

        Returns
        --------
        Optional[:class:`.SlashCommand`]
            The command that was removed. If no command with given name
            existed ``None`` is returned instead.
        """
        return self.all_commands.pop(name, None)

    def get_command(self, name):
        """Get a :class:`.SlashCommand` from the internal list of commands.

        Parameters
        -----------
        name: :class:`str`
            The name of the command to get.

        Returns
        --------
        Optional[:class:`.SlashCommand`]
            The requested command, if found.

        """
        return self.all_commands.get(name)

    def command(self, **kwargs):
        """A shortcut decorator that invokes :func:`.command` and adds the
        command to the internal list of commands.
        """
        def decorator(func):
            wrapped = command(**kwargs)(func)
            self.add_command(wrapped)
            return wrapped
        return decorator

    async def invoke(self, *, interaction, options, client):
        result = None
        for name, command in self.all_commands.items():
            if name in options:
                result = await command.invoke(interaction=interaction, options=options[name], client=client)

        return result

    def to_option(self):
        """Give this command as a :class:`ApplicationCommandOption`.
        
        The :class:`ApplicationCommandOption` will have type
        :ref:`ApplicationCommandOptionType.sub_command_group`

        """
        return ApplicationCommandOption.sub_command_group(name=self.name, description=self.description,
                                                          options=self.options)

# Decorators

def command(**attrs):
    """A decorator that transforms a coroutine into a :class:`.Command`.

    By default the ``name`` attribute will be equal to the coroutine's name.

    By default the ``arguments`` attribute will be determined by
    inspecting the coroutine's signature. The first positional
    argument will receive the :class:`Interaction` when the command is
    called, and does not contribute to the ``arguments``
    attribute. For each other parameter an :class:`.Argument` is added
    to ``arguments`` with the same name. If it has a default argument
    the corresponding :class`.Argument` will be made
    optional. Potential annotations are used to determine the specific
    subclass of :class:`Argument` used. By default this is always
    :class:`StringArgument`.

    The docstring of the provided coroutine will be inspected to fill
    in the ``description`` attribute as well as the ``description``
    attributes of the ``arguments``.

    The ``description`` attribute of this command is simply the first
    paragraph of the docstring. Leading and trailing whitespace on
    each line is removed. Lines are concatenated by putting a single
    space (' ') in between them. If descriptions of arguments are
    provided there should be at least one blank line between this
    paragraph and the arguments.

    For each argument one can provide additional information through
    the docstring through the following format:
    - First a line with the name of the argument. Optionally one can put
      a colon (':') after the argument followed by the type the argument
      should have.
    - An indented block containing the description of this argument. As
      with the description of the command, all leading and trailing
      whitespace of each line will be removed. Lines are concatenated
      with a single space (' ') in between them.

    Optionally, as part of the argument description, one can provide
    choices for that argument. Each choice should be formatted like
    '- [name] : [value]' where the '-' is at the start of a line.
    Note that all text after a '-' will be considered part of this format
    until the next '-' is encountered.

    """
    def decorator(coro):
        return SlashCommand(coro, **attrs)

    return decorator
