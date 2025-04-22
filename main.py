import logging
import json
from argparse import ArgumentParser
import requests
import discord
from discord.ext import commands
from bs4 import BeautifulSoup

from websocket import Websocket
from constants import *
from logger import Logger



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

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pokedex_data = None
        self.showdown_ws = None

    def set_logger(self, logger):
        self.log = logger

intents = discord.Intents.default()
intents.message_content = True

bot = MyBot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    bot.log.infolog(f'{bot.user} has connected to Discord!')

    #get the pokedex data
    response = requests.get(URL_POKEDEX, timeout=10)
    bot.pokedex_data = response.json()
    bot.log.infolog("Pokedex data loaded")

    #create the websocket connection
    bot.showdown_ws = await Websocket.create(logger=bot.log, username="pokebotdiscord123")
    bot.log.infolog("Websocket connection created")

@bot.command()
async def duel(ctx, arg):
    dueler = ctx.message.author
    duelee = ctx.message.mentions[0]
    await ctx.send(f"{dueler.mention} wants to duel {duelee.mention}", view=DuelRequest(dueler=dueler, duelee=duelee, timeout=60))

@bot.command()
async def dex(ctx, arg):
    #get the message from the websocket
    message = await bot.showdown_ws.request_pokemon_search(arg)
    try:
        #parse the message
        soup = parse_pokemon(message)
        #get the pokemon name
        name = soup.a.string.lower()
        search = name.replace(" ", "")
        embed = discord.Embed(
            title=f"{bot.pokedex_data.get(search).get('num')}. {name.title()}",
            description= pokemon_type(soup),
            color=discord.Color.blue()
        )
        embed.set_author(name="Pokedex", icon_url=URL_POKEDEX_ICON)
        res = requests.get(f"{URL_SPRITE}/xyani/{search}.gif", timeout=10)
        if res.status_code == requests.codes.NOT_FOUND:
            embed.set_thumbnail(url=f"{URL_SPRITE}/bwani/{search}.gif")
        else:
            embed.set_thumbnail(url=f"{URL_SPRITE}/xyani/{search}.gif")
        await ctx.reply(embed=embed)
    except Exception as e:
        bot.log.errorlog(e)
        await ctx.reply("Pokemon not found")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
            "-c", "--config", help="Config file", required=True, dest="config"
        )
    args = parser.parse_args()

    config = json.load(open(args.config))
    logger = Logger(config["log_config"])
    bot.set_logger(logger.get_logger())
    bot.run(config["token"], log_handler=logger.get_handler(), log_level=config["log_config"]["log_level"])