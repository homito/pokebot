import json
from argparse import ArgumentParser

import requests
import discord
from discord.ext import commands

from websocket import Websocket
from constants import URL_POKEDEX, URL_POKEDEX_ICON, URL_SPRITE
from logger import Logger
from utils import parse_pokemon, pokemon_type, navigation_callback
from buttons import DuelRequest, Battle, NavigationView

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pokedex_data = None
        self.showdown_ws = None
        self.username = None
        self.password = None

    def set_logger(self, logger):
        self.log = logger
    def set_showdown_account(self, username, password):
        self.username = username
        self.password = password

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
    bot.showdown_ws = await Websocket.create(logger=bot.log, username=bot.username, password=bot.password)
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
        number = bot.pokedex_data.get(name).get("num")
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
        await ctx.reply(embed=embed, view=NavigationView(author=ctx.message.author, callback=dex, arguments=[ctx, number]))
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
    bot.set_showdown_account(config["showdown_account"]["username"], config["showdown_account"]["password"])
    bot.run(config["token"], log_handler=logger.get_handler(), log_level=config["log_config"]["log_level"])