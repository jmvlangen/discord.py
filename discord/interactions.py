# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from . import utils
from .enums import try_enum, InteractionType, InteractionResponseType, ApplicationCommandOptionType
from .member import Member
from .message import Message
from .errors import InvalidArgument

__all__ = (
    'Interaction',
    'InteractionMessage',
)

if TYPE_CHECKING:
    from .types.interactions import (
        Interaction as InteractionPayload,
    )
    from .guild import Guild
    from .abc import GuildChannel


class Interaction:
    """Represents a Discord interaction.

    An interaction happens when a user does an action that needs to
    be notified. Current examples are slash commands but future examples
    include forms and buttons.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The interaction's ID.
    type: :class:`InteractionType`
        The interaction type.
    guild_id: Optional[:class:`int`]
        The guild ID the interaction was sent from.
    channel_id: Optional[:class:`int`]
        The channel ID the interaction was sent from.
    application_id: :class:`int`
        The application ID that the interaction was for.
    user: Optional[Union[:class:`User`, :class:`Member`]]
        The user or member that sent the interaction.
    token: :class:`str`
        The token to continue the interaction. These are valid
        for 15 minutes.
    """

    __slots__ = (
        'id',
        'type',
        'guild_id',
        'channel_id',
        'data',
        'application_id',
        'user',
        'token',
        'version',
        '_state',
        'responded',
    )

    def __init__(self, *, data: InteractionPayload, state=None):
        self._state = state
        self.responded = False
        self._from_data(data)

    def _from_data(self, data: InteractionPayload):
        self.id = int(data['id'])
        self.type = try_enum(InteractionType, data['type'])
        self.data = data.get('data')
        self.token = data['token']
        self.version = data['version']
        self.channel_id = utils._get_as_snowflake(data, 'channel_id')
        self.guild_id = utils._get_as_snowflake(data, 'guild_id')
        self.application_id = utils._get_as_snowflake(data, 'application_id')
        try:
            self.user = Member(data=data['member'], guild=self.guild, state=self._state)
        except KeyError:
            self.user = self._state.store_user(data['user'])

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild the interaction was sent from."""
        return self._state and self._state.get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[GuildChannel]:
        """Optional[:class:`abc.GuildChannel`]: The channel the interaction was sent from.

        Note that due to a Discord limitation, DM channels are not resolved since there is
        no data to complete them.
        """
        guild = self.guild
        return guild and guild.get_channel(self.channel_id)

    def __repr__(self):
        result = f"<Interaction id={self.id} type={self.type}"
        if self.user is not None:
            result += f" user={self.user}"
        if self.channel is not None:
            result += f" channel={self.channel}"
        result += ">"
        return result

    async def send_response(self, content=None, *, tts=None, embed=None, embeds=None,
                            allowed_mentions=None, ephemeral=False):
        """|coro|

        Responds to an interaction.

        The content must be a type that can convert to a string through ``str(content)``.

        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type. You cannot mix the ``embed`` parameter with the
        ``embeds`` parameter, which must be a :class:`list` of :class:`Embed` objects to send.

        If this interaction is a ping all provided arguments are ignored.

        One should use this method within 3 seconds of receiving the
        interaction. After that the interaction will remain valid for 15 minutes. For long
        computations you should use this method with ``None`` to create a temporary message
        that the bot is thinking, which can later be edited with ``edit_response``.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content of the response to send. If set to ``None`` will display a
            message that a response will be sent later
        ephemeral: :class:`bool`
            Whether the response should be visible only to the user that invoked
            this interaction.
        tts: :class:`bool`
            Indicates if the response should be sent using text-to-speech.
        embed: :class:`Embed`
            The rich embed for the response. This cannot be mixed with
            ``embeds`` parameter.
        embeds: List[:class:`Embed`]
            A list of embeds to send with the response. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this response.

        Raises
        --------
        HTTPException
            Sending the response failed.
        NotFound
            This interaction was not found.
        Forbidden
            The interaction token has expired.
        InvalidArgument
            You have already sent a response to this interaction or you specified
            both ``embed`` and ``embeds`` or the length of ``embeds`` was invalid.

        """
        if self.responded:
            raise InvalidArgument(f"Can not respond to {self} twice, use edit_response instead.")
        if embeds is not None and embed is not None:
            raise InvalidArgument('Cannot mix embed and embeds keyword arguments.')
        if embeds is not None and len(embeds) > 10:
            raise InvalidArgument('embeds has a maximum of 10 elements.')

        if embed is not None:
            embeds = [embed]

        if self.type == InteractionType.ping:
            response = InteractionResponse(pong=True)
        else:
            response = InteractionResponse(content=content, tts=tts, embeds=embeds,
                                           allowed_mentions=allowed_mentions, ephemeral=ephemeral)
        await self._state.http.create_interaction_response(self.id, self.token, response.to_dict())
        self.responded = True

    def edit_response(self, **fields):
        """|coro|

        Edit the response to this interaction.

        The content must be able to be transformed into a string via ``str(content)``.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content to edit the response with or ``None`` to clear it.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the response with.
        embed: Optional[:class:`Embed`]
            The embed to edit the response with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        allowed_mentions: Optional[:class:`AllowedMentions`]
            Controls the mentions being processed in the response. ``None``
            suppresses all mentions.

        Raises
        -------
        HTTPException
            Editing the response failed.
        Forbidden
            The interaction token has expired.
        InvalidArgument
            You have not responded to this interaction yet or you specified
            both ``embed`` and ``embeds`` or the length of ``embeds`` was invalid.
        """
        payload = {}

        if not self.responded:
            raise InvalidArgument(f"Can not edit a response of {self} if no response was sent yet.")

        try:
            content = fields['content']
        except KeyError:
            pass
        else:
            if content is not None:
                content = str(content)
            payload['content'] = content

        try:
            embeds = fields['embeds']
        except KeyError:
            pass
        else:
            if embeds is None:
                payload['embeds'] = None
            else:
                if len(embeds) > 10:
                    raise InvalidArgument('embeds has a maximum of 10 elements')
                payload['embeds'] = [embed.to_dict() for embed in embeds]

        try:
            embed = fields['embed']
        except KeyError:
            pass
        else:
            if 'embeds' in payload:
                raise InvalidArgument('Cannot mix embed and embeds keyword arguments')
            if embed is None:
                payload['embeds'] = None
            else:
                payload['embeds'] = [embed.to_dict()]

        try:
            allowed_mentions = fields['allowed_mentions']
        except KeyError:
            pass
        else:
            payload['allowed_mentions'] = allowed_mentions.to_dict()

        return self._state.http.edit_original_interaction_response(self.application_id, self.token, **payload)

    def delete_response(self):
        """|coro|

        Delete the response to this interaction.

        Raises
        ------
        Forbidden
            The interaction token has expired.
        NotFound
            There was no response for this interaction or the response was ephemeral.
        HTTPException
            Deleting the response failed.
        """
        return self._state.http.delete_original_interaction_response(self.application_id, self.token)

    async def send_message(self, content=None, *, username=None,
                           avatar_url=None, tts=False, file=None, files=None, embed=None,
                           embeds=None, allowed_mentions=None, ephemeral=False):
        """|coro|

        Sends a followup message on this interaction.

        The content must be a type that can convert to a string through ``str(content)``.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`File` object.

        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type. You cannot mix the ``embed`` parameter with the
        ``embeds`` parameter, which must be a :class:`list` of :class:`Embed` objects to send.

        Parameters
        ------------
        content: :class:`str`
            The content of the message to send.
        username: :class:`str`
            The username to send with this message. Right now this is ignored by
            discord and the default username is always used.
        avatar_url: Union[:class:`str`, :class:`Asset`]
            The avatar URL to send with this message. Right now this is ignored by
            discord and the default avatar is always used.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        file: :class:`File`
            The file to upload. This cannot be mixed with ``files`` parameter.
        files: List[:class:`File`]
            A list of files to send with the content. This cannot be mixed with the
            ``file`` parameter.
        embed: :class:`Embed`
            The rich embed for the content to send. This cannot be mixed with
            ``embeds`` parameter.
        embeds: List[:class:`Embed`]
            A list of embeds to send with the content. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.
        ephemeral: :class:`bool`
            Whether this message should be visible only to the user that invoked
            this interaction.

        Raises
        --------
        HTTPException
            Sending the message failed.
        InvalidArgument
            You specified both ``file`` and ``files`` or you specified both
            ``embed`` and ``embeds`` or the length of ``embeds`` was invalid.

        Returns
        ---------
        :class:`InteractionMessage`
            The message that was sent.
        """

        payload = {}
        if files is not None and file is not None:
            raise InvalidArgument('Cannot mix file and files keyword arguments.')
        if embeds is not None and embed is not None:
            raise InvalidArgument('Cannot mix embed and embeds keyword arguments.')

        if embeds is not None:
            if len(embeds) > 10:
                raise InvalidArgument('embeds has a maximum of 10 elements.')
            payload['embeds'] = [e.to_dict() for e in embeds]

        if embed is not None:
            payload['embeds'] = [embed.to_dict()]

        if files is not None:
            payload['files'] = files

        if file is not None:
            payload['files'] = [file]

        if content is not None:
            payload['content'] = str(content)

        payload['tts'] = tts
        if avatar_url is not None:
            payload['avatar_url'] = str(avatar_url)
        if username is not None:
            payload['username'] = username

        if allowed_mentions is not None:
            payload['allowed_mentions'] = allowed_mentions.to_dict()

        if ephemeral:
            payload['flags'] = 64

        data = await self._state.http.create_followup_message(self.application_id, self.token, **payload)

        return InteractionMessage(interaction=self, data=data)

    def edit_message(self, message_id, **fields):
        """|coro|

        Edits a message sent on this interaction.

        This is a lower level interface to :meth:`InteractionMessage.edit` in case
        you only have an ID.

        Parameters
        ------------
        message_id: :class:`int`
            The message ID to edit.
        content: Optional[:class:`str`]
            The content to edit the message with or ``None`` to clear it.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the message with.
        embed: Optional[:class:`Embed`]
            The embed to edit the message with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.

        Raises
        -------
        HTTPException
            Editing the message failed.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or the length of
            ``embeds`` was invalid.
        """

        payload = {}

        try:
            content = fields['content']
        except KeyError:
            pass
        else:
            if content is not None:
                content = str(content)
            payload['content'] = content

        try:
            embeds = fields['embeds']
        except KeyError:
            pass
        else:
            if embeds is None:
                payload['embeds'] = None
            else:
                if len(embeds) > 10:
                    raise InvalidArgument('embeds has a maximum of 10 elements')
                payload['embeds'] = [embed.to_dict() for embed in embeds]

        try:
            embed = fields['embed']
        except KeyError:
            pass
        else:
            if 'embeds' in payload:
                raise InvalidArgument('Cannot mix embed and embeds keyword arguments')
            if embed is None:
                payload['embeds'] = None
            else:
                payload['embeds'] = [embed.to_dict()]

        try:
            allowed_mentions = fields['allowed_mentions']
        except KeyError:
            pass
        else:
            payload['allowed_mentions'] = allowed_mentions.to_dict()

        return self._state.http.edit_followup_message(self.application_id, self.token, message_id, **payload)

    def delete_message(self, message_id):
        """|coro|

        Deletes a message sent on this interaction.

        This is a lower level interface to :meth:`InteractionMessage.delete` in case
        you only have an ID.

        Parameters
        ------------
        message_id: :class:`int`
            The message ID to delete.

        Raises
        -------
        HTTPException
            Deleting the message failed.
        """
        return self._state.http.delete_followup_message(self.application_id, self.token, message_id)

class InteractionResponse:
    """Represents a response to an :class:`Interaction`

    """

    def __init__(self, *, pong=False, content=None, tts=None,
                 embeds=None, allowed_mentions=None, ephemeral=False):
        if pong:
            self.type = InteractionResponseType.pong
        else:
            if content is None and embeds is None:
                self.type = InteractionResponseType.deferred_channel_message_with_source
            else:
                self.type = InteractionResponseType.channel_message_with_source
            self.content = content
            self.tts = tts
            self.embeds = embeds
            self.allowed_mentions = allowed_mentions
            self.ephemeral = ephemeral

    def to_dict(self):
        result = {'type' : self.type.value}

        data = {}
        if self.content is not None:
            data['content'] = str(self.content)
        if self.tts != None:
            data['tts'] = self.tts
        if self.embeds is not None:
            data['embeds'] = [embed.to_dict() for embed in self.embeds]
        if self.allowed_mentions is not None:
            data['allowed_mentions'] = self.allowed_mentions.to_dict()
        if self.ephemeral:
            data['flags'] = 64
        if len(data) > 0:
            result['data'] = data

        return result

class InteractionMessage(Message):
    """Represents a message sent through an interaction.

    This allows you to edit or delete a message sent through an
    interaction you received.

    This inherits from :class:`discord.Message` with changes to
    :meth:`edit` and :meth:`delete` to work.

    """

    __slots__ = ('_interaction')

    def __init__(self, *, interaction, data):
        self._interaction = interaction
        Message.__init__(self, state=interaction._state, channel=interaction.channel, data=data)

    def edit(self, **fields):
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content to edit the message with or ``None`` to clear it.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the message with.
        embed: Optional[:class:`Embed`]
            The embed to edit the message with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.
            See :meth:`.abc.Messageable.send` for more information.

        Raises
        -------
        HTTPException
            Editing the message failed.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or the length of
            ``embeds`` was invalid.
        """
        return self._interaction.edit_message(self.id, **fields)

    def delete(self):
        """|coro|

        Deletes the message.

        Raises
        ------
        HTTPException
            Deleting the message failed.
        """

        return self._interaction.delete_message(self.id)
