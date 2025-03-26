import logging
import json
import requests
from argparse import ArgumentParser
from websockets.sync.client import connect
import discord
from discord.ext import commands
from bs4 import BeautifulSoup

URL_POKEDEX = "https://play.pokemonshowdown.com/data/pokedex.json"
URL_POKEDEX_ICON = "https://archives.bulbagarden.net/media/upload/thumb/6/61/DP_Pok%C3%A9dex.png/726px-DP_Pok%C3%A9dex.png"
URL_SPRITE = "https://play.pokemonshowdown.com/sprites"
WEBSOCKET = "wss://sim3.psim.us/showdown/websocket"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

def request_pokemon_search(searched: str):
    with connect(WEBSOCKET) as websocket:
        websocket.recv() # ignore |updateuser| message
        websocket.recv() # ignore |challstr| message (i should probably check what they are so its not hacked like that)
        websocket.send(f"|/dt {searched}")
        message = websocket.recv()
        return message
def parse_pokemon_search(message: str):
    m = [w for w in message.split("|pm|") if "pokemonnamecol" in w]
    html = m[0].split("/raw ")[1] # if websocket sends error, this will beak as there is nothing to split
    soup = BeautifulSoup(html, features="html.parser")
    return soup.a.string
def parse_pokemon_type(message: str):
    m = [w for w in message.split("|pm|") if "pokemonnamecol" in w]
    html = m[0].split("/raw ")[1] # if websocket sends error, this will beak as there is nothing to split
    soup = BeautifulSoup(html, features="html.parser")
    return soup.a.string
def pokemon_type(message: str) -> str:
    m = [w for w in message.split("|pm|") if "pokemonnamecol" in w]
    html = m[0].split("/raw ")[1] # if websocket sends error, this will beak as there is nothing to split
    soup = BeautifulSoup(html, features="html.parser")
    img = soup.find_all('img')
    res = "```ansi\n"
    for i in img:
        res += f"\x1B[2;45m {i['alt']} \x1B[0m"
    res += "```"
    return res
    #return "```ansi\n\x1B[2;41m Feu \x1B[0m \x1B[2;45m Vol \x1B[0m```" #TODO: not placeholder

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    logging.info(f'{bot.user} has connected to Discord!')

@bot.command()
async def foo(ctx, arg):
    await ctx.send(arg)

@bot.command()
async def dex(ctx, arg):
    search = parse_pokemon_search(request_pokemon_search(arg)).lower()
    response = requests.get(URL_POKEDEX, timeout=10)
    data = response.json()
    try:
        embed = discord.Embed(
            title=f"{data.get(search).get('num')}. {search.capitalize()}",
            description= pokemon_type(request_pokemon_search(arg)),
            color=discord.Color.blue()
        )
        embed.set_author(name="Pokedex", icon_url=URL_POKEDEX_ICON)
        res = requests.get(f"{URL_SPRITE}/xyani/{search}.gif", timeout=10)
        if res.status_code == requests.codes.NOT_FOUND:
            embed.set_thumbnail(url=f"{URL_SPRITE}/bwani/{search}.gif")
        else:
            embed.set_thumbnail(url=f"{URL_SPRITE}/xyani/{search}.gif")
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