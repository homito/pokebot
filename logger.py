"""
Contains the Logger class for logging messages to console and file.
imported from Moodle.
"""

import logging

class Logger:
    """
    A simple logger class that handles logging messages to both console and file.
    """
    def __init__(self, config:dict):
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

    def get_logger(self):
        return self

    def get_handler(self):
        return self.log.handlers[1]

    def infolog(self, msg: str):
        self.log.info(msg)

    def errorlog(self, msg: str):
        self.log.error(msg)

    def debuglog(self, msg: str):
        self.log.debug(msg)