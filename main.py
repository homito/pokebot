import logging
import json
from argparse import ArgumentParser
import discord
from discord import Client

class Logger:

    def __init__(self, config:dict):

        print ("logger name ",__name__)
        self.__level___ = config["log_level"] 

        formatter = logging.Formatter(config["log_format"])

        handler = logging.StreamHandler()
        handler.setLevel(self.__level___)
        handler.setFormatter(formatter)

        f_handler = logging.FileHandler(config["log_file"])
        f_handler.setLevel(self.__level___)
        f_handler.setFormatter(formatter)

        self.log = logging.getLogger(__name__)
        self.log.setLevel(self.__level___)
        self.log.addHandler(handler)
        self.log.addHandler(f_handler)

    def infolog(self, msg: str):
        self.log.info(msg)

    def errorlog(self, msg: str):
        self.log.error(msg)

    def debuglog(self, msg: str):
        self.log.debug(msg)


class MyBot(Client):
    log: Logger = None

    def __init__(self, log_instance: Logger):
        super().__init__(intents=discord.Intents.all())
        self.log = log_instance

    async def on_ready(self):
        self.log.infolog(f"{self.user} has connected to Discord!")

    async def on_message(self, message):
        self.log.infolog(f"Message from {message.author} in {message.channel}: {message.content}")

        if message.content == config["prefix"] + "ping":
            await message.channel.send("Pong!")

        if message.content == config["prefix"] + "help":
            await message.channel.send("Hello! I am a bot. I can respond to the following commands:\n\n" +
                "ping - I will respond with 'Pong!'\n" +
                "prompt <message> - I will respond with a message generated using GPT-3"
            )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
            "-c", "--config", help="Config file", required=True, dest="config"
        )
    args = parser.parse_args()

    config = json.load(open(args.config))
    logger = Logger(config["log_config"])

    client = MyBot(logger)
    client.run(config["token"])
