import asyncio
import datetime
import random

import discord
from discord.ext import commands, tasks
from discord.ext.commands.core import guild_only, has_role
from models.ContentRepository import ContentRepository
from utils.const import (QOTD_MENTION_ROLE, QOTD_SEND_CHANNEL,
                         QOTD_SUGGESTION_CHANNEL)
from utils.views import Confirm


class QotdCommands(commands.Cog, name="Qotd"):
    def __init__(self, bot):
        self.bot = bot
        # self.send_qotd.start()

    @tasks.loop(time=datetime.time(hour=15))
    async def send_qotd(self):
        await self.publish_qotd(0)

    @commands.command(
        name="qotd",
        description="Suggests a QOTD for verification",
        usage="qotd <question>")
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    @guild_only()
    async def suggest_qotd(self, ctx, *, suggestion):
        # TODO: Move this out into Embeds class
        e = self.create_qotd_embed(ctx, suggestion)
        verify_channel = self.bot.get_channel(QOTD_SUGGESTION_CHANNEL)
        view = Confirm(timeout=None)
        msg = await verify_channel.send(embed=e, view=view)
        await ctx.message.delete()
        await view.wait()
        if view.value is False:
            return await msg.delete()
        content_repo = ContentRepository()
        return content_repo.insert({
            "content": suggestion,
            "suggested_by": ctx.message.author.id,
            "published": False, "type": "QOTD"})

    def create_qotd_embed(self, ctx, suggestion):
        e = discord.Embed(title=f"QOTD Suggestion by {ctx.message.author.display_name}",
                          description=suggestion,
                          color=discord.Color.blurple())
        e.set_author(name=ctx.message.author.display_name,
                     url=ctx.message.author.avatar.url)
        return e

    async def publish_qotd(self, delay: int = 0):
        content_repo = ContentRepository()
        choices = list(content_repo.read_many(
            {"type": "QOTD", "published": False}))
        if len(choices) == 0:
            return
        qotd = random.choice(choices)
        send_ch = await self.bot.fetch_channel(QOTD_SEND_CHANNEL)
        await asyncio.sleep(delay*60)
        msg = await send_ch.send(
            f"<@&{int(QOTD_MENTION_ROLE)}>\n"
            f"{qotd['content']}")
        today = datetime.date.today()
        await msg.create_thread(name=f"QOTD: {today.strftime('%d-%b-%Y')}")
        content_repo.update({"content": qotd["content"]}, {
                            "$set": {"published": True}})
        return

    @commands.command(
        name="sendqotd",
        description="Automatically chooses and sends a QOTD",
        usage="sendqotd <delay (minutes, optional, default 0)>")
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    @has_role("Staff")
    @guild_only()
    async def sendqotd(self, ctx, delay: int = 0):
        await self.publish_qotd(delay)

    @commands.command(
        name="qotdcount",
        description="Number of valid QotDs left",
        usage="qotdcount")
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    @has_role("Staff")
    @guild_only()
    async def qotdcount(self, ctx, delay: int = 0):
        content_repo = ContentRepository()
        choices = list(content_repo.read_many(
            {"type": "QOTD", "published": False}))
        return await ctx.reply(f"{str(len(choices))} valid QoTDs are left")


def setup(bot):
    bot.add_cog(QotdCommands(bot))
