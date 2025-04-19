import logging
import json
from argparse import ArgumentParser
from websockets.sync.client import connect
import requests
import discord
from discord.ext import commands
from bs4 import BeautifulSoup

URL_POKEDEX = "https://play.pokemonshowdown.com/data/pokedex.json"
URL_POKEDEX_ICON = "https://archives.bulbagarden.net/media/upload/thumb/6/61/DP_Pok%C3%A9dex.png/726px-DP_Pok%C3%A9dex.png"
URL_SPRITE = "https://play.pokemonshowdown.com/sprites"
WEBSOCKET = "wss://sim3.psim.us/showdown/websocket"

TYPE_COLORS = {
    "Normal": "\x1B[1;47;30m Normal \x1B[0m",
    "Fighting": "\x1B[1;41m Fighting \x1B[0m",
    "Flying": "\x1B[1;45m Flying \x1B[0m",
    "Poison": "\x1B[1;35m Poison \x1B[0m",
    "Ground": "\x1B[1;41m Ground \x1B[0m",
    "Rock": "\x1B[1;41m Rock \x1B[0m",
    "Bug": "\x1B[1;32m Bug \x1B[0m",
    "Ghost": "\x1B[1m Ghost \x1B[0m",
    "Steel": "\x1B[1;46m Steel \x1B[0m",
    "Fire": "\x1B[1;41m Fire \x1B[0m",
    "Water": "\x1B[1;45m Water \x1B[0m",
    "Grass": "\x1B[1;32m Grass \x1B[0m",
    "Electric": "\x1B[1;33m Electric \x1B[0m",
    "Psychic": "\x1B[1;35m Psychic \x1B[0m",
    "Ice": "\x1B[1;45m Ice \x1B[0m",
    "Dragon": "\x1B[1;45;30m Dragon \x1B[0m",
    "Dark": "\x1B[1;40m Dark \x1B[0m",
    "Fairy": "\x1B[1;35m Fairy \x1B[0m"
}

pokedex_data = None

class Battle(discord.ui.view):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Move 1", style=discord.ButtonStyle.primary)
    async def move1(self, interaction, button):
        await interaction.response.send_message("You pressed me!")
    @discord.ui.button(label="Move 2", style=discord.ButtonStyle.primary)
    async def move2(self, interaction, button):
        await interaction.response.send_message("You pressed me!")
    @discord.ui.button(label="Move 3", style=discord.ButtonStyle.primary)
    async def move3(self, interaction, button):
        await interaction.response.send_message("You pressed me!")
    @discord.ui.button(label="Move 4", style=discord.ButtonStyle.primary)
    async def move4(self, interaction, button):
        await interaction.response.send_message("You pressed me!")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

def request_pokemon_search(searched: str):
    """
    This function will send a message to the websocket
    and return the response while ignoring the first two messages
    """
    with connect(WEBSOCKET) as websocket:
        websocket.recv() # ignore |updateuser| message
        websocket.recv() # ignore |challstr| message (i should probably check what they are so its not hacked like that)
        websocket.send(f"|/dt {searched}")
        message = websocket.recv()
        return message
def parse_pokemon(message:str):
    m = [w for w in message.split("|pm|") if "pokemonnamecol" in w]
    html = m[0].split("/raw ")[1] # if websocket sends error, this will beak as there is nothing to split
    return BeautifulSoup(html, features="html.parser")
def pokemon_type(soup: BeautifulSoup) -> str:
    """
    This function will parse the message from the websocket
    it returns the type of the pokemon
    """
    img = soup.find_all('img')
    res = "```ansi\n"
    for i in img:
        res += TYPE_COLORS[i['alt']] + " "
    res += "```"
    return res

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    logging.info(f'{bot.user} has connected to Discord!')

    #get the pokedex data
    response = requests.get(URL_POKEDEX, timeout=10)
    global pokedex_data
    pokedex_data = response.json()
    print("Pokedex data loaded")
    logging.info("Pokedex data loaded")

@bot.command()
async def duel(ctx, arg):
    dueler = ctx.message.author
    duelee = ctx.message.mentions[0]
    await ctx.send(f"{dueler.mention} wants to duel {duelee.mention}", view=DuelRequest(dueler=dueler, duelee=duelee, timeout=60))

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

@bot.command()
async def dex(ctx, arg):
    #get the message from the websocket
    message = request_pokemon_search(arg)
    #parse the message
    soup = parse_pokemon(message)
    #get the pokemon name
    search = soup.a.string.lower()
    try:
        embed = discord.Embed(
            title=f"{pokedex_data.get(search).get('num')}. {search.capitalize()}",
            description= pokemon_type(soup),
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