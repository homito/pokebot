import logging
import json
import requests
from argparse import ArgumentParser
import discord
from discord.ext import commands

URL_POKEDEX = "https://play.pokemonshowdown.com/data/pokedex.json"
URL_SPRITE = "https://play.pokemonshowdown.com/sprites"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    logging.info(f'{bot.user} has connected to Discord!')

@bot.command()
async def foo(ctx, arg):
    await ctx.send(arg)

@bot.command()
async def dex(ctx, arg):
    search = arg.split(" ")[0]
    response = requests.get(URL_POKEDEX, timeout=10)
    data = response.json()
    try:
        embed = discord.Embed(
            title=search.capitalize(),
            description=f"National Dex number: {data.get(search).get('num')}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"{URL_SPRITE}/gen5/{search}.png")
        res = requests.get(f"{URL_SPRITE}/xyani/{search}.gif", timeout=10)
        if res.status_code == requests.codes.NOT_FOUND:
            embed.set_image(url=f"{URL_SPRITE}/bwani/{search}.gif")
        else:
            embed.set_image(url=f"{URL_SPRITE}/xyani/{search}.gif")
        await ctx.send(embed=embed)
    except AttributeError:
        await ctx.send("Pokemon not found")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
            "-c", "--config", help="Config file", required=True, dest="config"
        )
    args = parser.parse_args()

    config = json.load(open(args.config))
    handler = logging.FileHandler(filename=config["log_config"]["log_file"], encoding='utf-8', mode='w')
    bot.run(config["token"], log_handler = handler, log_level = config["log_config"]["log_level"])