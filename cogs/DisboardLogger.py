import logging
from datetime import datetime
import re

from discord.ext import commands
from models.UserRepository import UserRepository
from utils.const import BUMP_CHANNEL_ID, DISBOARD_BOT_ID

logger = logging.getLogger('botlogs')


class DisboardLogger(commands.Cog, name="BumpLog"):
    def __init__(self, bot):
        self.bot = bot
        self.user_repo = UserRepository()

    @commands.Cog.listener("on_message")
    async def disboard_message_handler(self, message):
        if message.author.id == DISBOARD_BOT_ID and message.channel.id == BUMP_CHANNEL_ID:
            logger.debug("Message by Disboard bot detected")
            m_embed = message.embeds[0]
            desc = m_embed.description
            if not (":thumbsup:" in desc or "👍" in desc):
                return
            mentions = re.search(r"<@!*([0-9]+)>", desc)
            member_id = mentions.group(1).strip()
            logger.debug(f"mention extracted as : {member_id}")
            logger.debug(member_id)
            member = message.guild.get_member(int(member_id))
            logger.debug(f"Bump by user {member.name}")
            if self.user_repo.read({"id": member.id}) is None:
                self.user_repo.insert({
                    "id": member.id,
                    "name": member.name,
                    "discriminator": member.discriminator,
                    "display_name": member.display_name,
                    "joined_at": datetime.now().timestamp()
                })
            user_doc = self.user_repo.read({"id": member.id})
            if "bump_count" in user_doc:
                bump_count = user_doc["bump_count"]
            else:
                bump_count = 0
            logger.debug(f"Current bump count: {bump_count}")
            bump_count += 1
            await message.channel.send(
                f"{member.mention}, thanks for bumping! "
                f"Your total bump count is **{str(bump_count)}**.")
            return self.user_repo.update(
                {"id": member.id}, {"$set": {"bump_count": bump_count}})


def setup(bot):
    bot.add_cog(DisboardLogger(bot))
