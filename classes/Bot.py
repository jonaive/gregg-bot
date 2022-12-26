import logging
import os

from discord.ext import commands
from utils import permissions


logger = logging.getLogger('botlogs')


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_message(self, msg):
        if self.is_ready() and permissions.can_handle(msg, "send_messages"):
            return await self.process_commands(msg)

    def load_cogs(self):
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                self.load_extension(f"cogs.{name}")
        return
