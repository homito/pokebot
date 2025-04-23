"""
Contains the utility functions for the bot.
"""

from bs4 import BeautifulSoup
from constants import TYPE_COLORS

def parse_pokemon(message:str):
    """
    This function will parse the message from the websocket
    it returns the soup object of the pokemon
    """
    m = [w for w in message.split("|pm|") if "pokemonnamecol" in w]
    html = m[0].split("/raw ")[1]
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
