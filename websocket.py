import json
import websockets
import requests
from constants import *

class Websocket():
    @classmethod
    async def create(cls, logger, username, password=None):
        self = Websocket()
        self.username = username
        self.password = password
        self.log = logger
        self.challstr = ""
        self.battle_id = ""
        self.player = ""
        self.rqid = 0
        self.websocket = await websockets.connect(WEBSOCKET)
        await self.connect()
        await self.login()
        message = await self.websocket.recv() #updateuser
        message = await self.websocket.recv() #updatesearch
        #await self.challenge("homiboot", "gen9randombattle")
        return self
    
    async def connect(self):
        updateuser = await self.websocket.recv()
        challstr = await self.websocket.recv()
        self.challstr = challstr.split("|challstr|")[1]
        self.log.infolog(f"connected with challstr: {self.challstr}")

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
            self.log.errorlog("Login failed")
            return
        if self.password is None:
            assertion = res.text
        else:
            assertion = json.loads(res.text[1:])["assertion"]
        change_name = f"|/trn {self.username},0,{assertion}"
        await self.websocket.send(change_name)
        response = await self.websocket.recv()
        self.log.infolog("Logged in successfully")

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