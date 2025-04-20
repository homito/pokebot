import logging
import json
from argparse import ArgumentParser
import websockets
import requests
import discord
from discord.ext import commands
from bs4 import BeautifulSoup

URL_POKEDEX = "https://play.pokemonshowdown.com/data/pokedex.json"
URL_POKEDEX_ICON = "https://archives.bulbagarden.net/media/upload/thumb/6/61/DP_Pok%C3%A9dex.png/726px-DP_Pok%C3%A9dex.png"
URL_SPRITE = "https://play.pokemonshowdown.com/sprites"
WEBSOCKET = "wss://sim3.psim.us/showdown/websocket"
ACTION_URL = "https://play.pokemonshowdown.com/action.php"

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

class Websocket():
    @classmethod
    async def create(cls, username, password=None):
        self = Websocket()
        self.username = username
        self.password = password
        self.log_path = None # jsp a quel point c important on triera plus tard
        self.challstr = ""
        self.battle_id = ""
        self.player = ""
        self.rqid = 0
        self.websocket = await websockets.connect(WEBSOCKET)
        await self.connect()
        await self.login()
        message = await self.websocket.recv() #updateuser (jsp exactement ce que c)
        message = await self.websocket.recv() #updatesearch
        #await self.challenge("homiboot", "gen9randombattle")
        return self
    async def connect(self):
        updateuser = await self.websocket.recv()
        challstr = await self.websocket.recv()
        self.challstr = challstr.split("|challstr|")[1]
    async def login(self):
        data = {
            "act": "getassertion",
            "userid": self.username,
            "challstr": self.challstr
        } if self.password is None else {
            "act": "login",
            "name": self.username,
            "pass": self.password,
            "challstr": self.challstr
        }
        res = requests.post(ACTION_URL, data=data)
        if res.status_code != 200:
            print("Login failed")
            logging.error("Login failed")
            return
        if self.password is None:
            assertion = res.text
        else:
            assertion = json.loads(res.text[1:])["assertion"]
        change_name = f"|/trn {self.username},0,{assertion}"
        await self.websocket.send(change_name)
        response = await self.websocket.recv()
    async def challenge(self, opponent, battleformat):
        await self.websocket.send(f"|/challenge {opponent}, {battleformat}")
        response = await self.websocket.recv()
    async def request_pokemon_search(self, searched: str):
        """
        This function will send a message to the websocket
        and return the response
        """
        await self.websocket.send(f"|/dt {searched}")
        message = await self.websocket.recv()
        return message

ws = None

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

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

    #create the websocket connection
    global ws
    ws = await Websocket.create("pokebotdiscord")
    print("Websocket connection created")
    logging.info("Websocket connection created")

@bot.command()
async def duel(ctx, arg):
    dueler = ctx.message.author
    duelee = ctx.message.mentions[0]
    await ctx.send(f"{dueler.mention} wants to duel {duelee.mention}", view=DuelRequest(dueler=dueler, duelee=duelee, timeout=60))

@bot.command()
async def dex(ctx, arg):
    #get the message from the websocket
    message = await ws.request_pokemon_search(arg)
    try:
        #parse the message
        soup = parse_pokemon(message)
        #get the pokemon name
        name = soup.a.string.lower()
        search = name.replace(" ", "")
        embed = discord.Embed(
            title=f"{pokedex_data.get(search).get('num')}. {name.title()}",
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
        logging.error(f"Error: {e}")
        await ctx.reply("Pokemon not found")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
            "-c", "--config", help="Config file", required=True, dest="config"
        )
    args = parser.parse_args()

    config = json.load(open(args.config))
    handler = logging.FileHandler(filename=config["log_config"]["log_file"], encoding='utf-8', mode='w')
    bot.run(config["token"], log_handler = handler, log_level = config["log_config"]["log_level"])