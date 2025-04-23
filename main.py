"""
Main file for the Discord bot that interacts with the Pokemon Showdown API.
This bot allows users to search for Pokemon information using the Pokedex API and the Showdown WebSocket API.
"""

import json
from argparse import ArgumentParser

import requests
import discord
from discord.ext import commands

from websocket import Websocket
from constants import URL_POKEDEX, URL_POKEDEX_ICON, URL_SPRITE
from logger import Logger
from utils import parse_pokemon, pokemon_type
from buttons import NavigationView

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
async def ping(ctx):
    await ctx.reply("Pong!")

@bot.command()
async def dex(ctx, arg):
    async def parse_argument(bot, arg)->discord.Embed:
        """
        Parses the argument given by the user
        returns a discord embed with the pokemon information.
        """
        try:
            message = await bot.showdown_ws.request_pokemon_search(arg)
            soup = parse_pokemon(message)
            name = soup.a.string.lower()
            search = name.replace(" ", "").replace("-", "").replace("'", "").replace(".", "").replace(",", "").replace("!", "").replace("?", "")
            number = bot.pokedex_data.get(search).get("num")
            embed = discord.Embed(
                title=f"{number}. {name.title()}",
                description= pokemon_type(soup),
                color=discord.Color.blue()
            )
            embed.set_author(name="Pokedex", icon_url=URL_POKEDEX_ICON)
            res = requests.get(f"{URL_SPRITE}/xyani/{search}.gif", timeout=10) #3d sprite gif
            if res.status_code == requests.codes.NOT_FOUND:
                embed.set_thumbnail(url=f"{URL_SPRITE}/bwani/{search}.gif") #2d sprite gif
            else:
                embed.set_thumbnail(url=f"{URL_SPRITE}/xyani/{search}.gif")
            return embed
        except Exception as e:
            raise e

    async def edit_dex(o_msg, msg, arg):
        """
        This function will be called when the user clicks on the buttons
        It deletes the old message and replace it with a new one with the correct informations
        """
        try:
            embed = await parse_argument(bot, arg)
            number = int(embed.title.split(".")[0].strip())
            await msg.delete()
            msg = await o_msg.reply(embed=embed)
            await msg.edit(view=NavigationView(author=o_msg.author, callback=edit_dex, arguments=[o_msg, msg, number]))
        except Exception as e:
            bot.log.errorlog(e)
            
    try:
        embed = await parse_argument(bot, arg)
        number = int(embed.title.split(".")[0].strip())
        message = await ctx.reply(embed=embed)
        await message.edit(view=NavigationView(author=ctx.message.author, callback=edit_dex, arguments=[ctx, message, number]))
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