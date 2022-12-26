from utils.views import Paginator
from classes.Embeds import ReaderboardEmbed, UserEventsListEmbed
import discord
from discord.ext import commands
from models.EventRepository import EventRepository


class ReaderboardCommands(commands.Cog, name="Readerboard"):
    def __init__(self, bot):
        self.bot = bot

    async def create_readerboard_embed(self, ctx, scores):
        e = discord.Embed(title="Reading Leaderboard",
                          color=discord.Color.blue())
        e.description = ""
        for i, result in enumerate(scores):
            userId = result[0]
            score = result[1]
            e.description += f"{str(i+1)}) <@{str(userId)}> --> **{str(score)}**\n"
        e.set_author(icon_url=ctx.guild.icon.url, name=ctx.guild.name)
        e.set_footer(text=f"Fetched by {self.bot.user.name}")
        return e

    @commands.command(
        description="Gets top 10 members on the Readerboard", usage="readerboard", aliases=["rb"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def readerboard(self, ctx):
        async with ctx.typing():
            event_repo = EventRepository()
            results = event_repo.get_all_readers()
            all_pages = ReaderboardEmbed.create_many(results)
        view = Paginator(all_pages)
        return await ctx.send(embed=all_pages[0], view=view)

    @commands.command(
        description="Get a users's score on the Readerboard", usage="score [@user]",
        aliases=["points", "rank"])
    @commands.guild_only()
    async def score(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        async with ctx.typing():
            event_repo = EventRepository()
            score = event_repo.calculate_score(user.id)
        return await ctx.reply(
            f"__**{user.display_name}'s Score**__\n"
            f"Total Score: {score['BR'] + score['MR']}\n"
            f"BR Points: {score['BR']}\n"
            f"MR Points: {score['MR']}\n")

    async def event_list(self, ctx, user, event_type, list_type="read"):
        if user is None:
            user = ctx.author
        async with ctx.typing():
            event_repo = EventRepository()
            if list_type == "read":
                events = event_repo.get_user_participated_events(user.id, event_type)
            elif list_type == "reacted":
                events = event_repo.get_user_interacted_events(user.id, event_type)

        embed = UserEventsListEmbed()
        all_pages = embed.create_many(
            f"{user.display_name}'s {event_type}s ({list_type})", events, user.id)
        view = Paginator(all_pages)
        if len(all_pages) == 0:
            return await ctx.send(f"No {event_type}s found for {user.display_name}")
        return await ctx.send(embed=all_pages[0], view=view)

    @commands.command(
        description="Get a users's participated BRs", usage="brlist [@user]",
        aliases=["brl", "brlist", "brread"])
    @commands.guild_only()
    async def br_list(self, ctx, user: discord.Member = None):
        return await self.event_list(ctx, user, "BR")

    @commands.command(
        description="Get a users's participated MRs", usage="mrlist [@user]",
        aliases=["mrl", "mrlist", "mrrread"])
    @commands.guild_only()
    async def mr_list(self, ctx, user: discord.Member = None):
        return await self.event_list(ctx, user, "MR")

    @commands.command(
        description="Get a users's reacted BRs", usage="brr [@user]",
        aliases=["brr", "brlistr", "brreacted"])
    @commands.guild_only()
    async def br_interacted(self, ctx, user: discord.Member = None):
        return await self.event_list(ctx, user, "BR", "reacted")

    @commands.command(
        description="Get a users's reacted MRs", usage="mrr [@user]",
        aliases=["mrr", "mrlistr", "mrreacted"])
    @commands.guild_only()
    async def mr_interacted(self, ctx, user: discord.Member = None):
        return await self.event_list(ctx, user, "MR", "reacted")


def setup(bot):
    bot.add_cog(ReaderboardCommands(bot))
