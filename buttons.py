import discord
from discord.ext import commands

class Battle(discord.ui.View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Move 1", row=0, style=discord.ButtonStyle.primary)
    async def move1(self, interaction, button):
        await interaction.response.send_message("You pressed me!")
    @discord.ui.button(label="Move 2", row=0, style=discord.ButtonStyle.primary)
    async def move2(self, interaction, button):
        await interaction.response.send_message("You pressed me!")
    @discord.ui.button(label="Move 3", row=1, style=discord.ButtonStyle.primary)
    async def move3(self, interaction, button):
        await interaction.response.send_message("You pressed me!")
    @discord.ui.button(label="Move 4", row=1, style=discord.ButtonStyle.primary)
    async def move4(self, interaction, button):
        await interaction.response.send_message("You pressed me!")

class DuelRequest(discord.ui.View):
    dueler = None
    duelee = None
    def __init__(self, dueler, duelee, timeout=60):
        super().__init__(timeout=timeout)
        self.dueler = dueler
        self.duelee = duelee
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.primary)
    async def accept(self, interaction, button):
        if interaction.user == self.duelee:
            await interaction.response.send_message("You pressed me!")
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction, button):
        if interaction.user == self.duelee:
            await interaction.response.send_message(f"{self.duelee} declined the duel")

class NavigationView(discord.ui.View):
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
