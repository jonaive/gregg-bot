import os
import time

import discord
import psutil
from discord.ext import commands
from utils.const import OWNERS


class InformationCommands(commands.Cog, name="Info"):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())

    @commands.command(description="Pong!", usage="ping")
    async def ping(self, ctx):
        before = time.monotonic()
        before_ws = int(round(self.bot.latency * 1000, 1))
        message = await ctx.send("🏓 Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"🏓 WS: {before_ws}ms  |  REST: {int(ping)}ms")

    @commands.command(
        description="About the Bot",
        usage="about", aliases=['info', 'stats', 'status'])
    async def about(self, ctx):
        ramUsage = self.process.memory_full_info().rss / 1024**2
        avgmembers = sum(
            g.member_count for g in self.bot.guilds) / len(self.bot.guilds)

        embedColour = discord.Embed.Empty
        if hasattr(ctx, 'guild') and ctx.guild is not None:
            embedColour = ctx.me.top_role.colour
        embed = discord.Embed(colour=embedColour, title=str(ctx.bot.user))
        embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        embed.add_field(
            name=f"Developer{'' if len(OWNERS) == 1 else 's'}",
            value=', '.join([str(self.bot.get_user(int(x)))
                             for x in OWNERS]),
            inline=True
        )
        embed.add_field(name="Library", value="discord.py", inline=True)
        embed.add_field(
            name="Servers",
            value=f"{len(ctx.bot.guilds)} ( avg: {avgmembers:,.2f} users/server )", inline=True)
        embed.add_field(name="Commands loaded", value=len(
            [x.name for x in self.bot.commands]), inline=True)
        embed.add_field(name="RAM", value=f"{ramUsage:.2f} MB", inline=True)

        await ctx.send(content=f"ℹ About **{ctx.bot.user}**", embed=embed)


def setup(bot):
    bot.add_cog(InformationCommands(bot))
