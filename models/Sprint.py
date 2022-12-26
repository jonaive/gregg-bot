import logging
from datetime import datetime, timedelta

from discord.ext import timers

logger = logging.getLogger('botlogs')


class Sprint():

    def __init__(self, sprint_id, bot, duration):
        self.id = sprint_id
        self.start_timestamp = 0
        self.duration = duration
        self.start_counts = {}
        self.end_counts = {}
        self.bot = bot

    def start(self):
        try:
            self.timer = self.setup_timer()
            self.start_timestamp = datetime.now().timestamp()
            self.timer.start()
            logger.info(f"Sprint with ID {self.id} started")
            return
        except Exception as e:
            logger.error(e)
            logger.error("Error Starting Sprint")
            return

    def setup_timer(self):
        dur_timedelta = timedelta(0, 60*self.duration)
        timer = timers.Timer(self.bot, "sprint_finish",
                             dur_timedelta, args=(self.id,))
        return timer

    def add_start_count(self, user_id, count):
        self.start_counts[user_id] = count
        return

    def remove_from_sprint(self, user_id):
        del self.start_counts[user_id]
        return

    def add_end_count(self, user_id, count):
        self.end_counts[user_id] = count
        return

    def cancel(self):
        self.timer.cancel()
        return
