"""
Contains the Views that are used for the buttons in the bot.
"""

import discord
from discord.ext import commands

class NavigationView(discord.ui.View):
    """
    A view that contains buttons for navigating through a paginated message.
    The buttons only work for the author of the message being replied to.
    """
    def __init__(self, author, callback, arguments, timeout=60):
        super().__init__(timeout=timeout)
        self.author = author
        self.callback = callback
        self.arguments = arguments
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous(self, interaction, button):
        if interaction.user == self.author:
            await self.callback(self.arguments[0], self.arguments[1], self.arguments[2]-1)
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction, button):
        if interaction.user == self.author:
            await self.callback(self.arguments[0], self.arguments[1], self.arguments[2]+1)
