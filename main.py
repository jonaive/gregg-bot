import os
import logging
import discord
from classes.Bot import Bot
from discord.ext import commands
from utils.const import PREFIX, OWNERS


def initializeLogger():
    logger = logging.getLogger('botlogs')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(
        filename='discord.log', encoding='utf-8', mode='w')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def main():
    initializeLogger()
    print("Logging in...")

    bot = Bot(
        command_prefix=commands.when_mentioned_or(PREFIX),
        owner_ids=OWNERS, command_attrs=dict(hidden=True),
        help_command=None, case_insensitive=True, intents=discord.Intents(
            guilds=True, members=True, messages=True, reactions=True, presences=True
        ))

    bot.load_cogs()
    bot.run(os.environ["BOT_TOKEN"])


main()
