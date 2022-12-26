import logging

from classes.Embeds import RecommendationEmbed
from discord.ext import commands
from discord.ext.commands.core import guild_only
from models.RecommendationRepository import RecommendationRepository
from utils import tools
from utils.views import Confirm

logger = logging.getLogger('botlogs')


class RecommendationCommands(commands.Cog, name="Recommendations"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description="For submitting a book recommendation",
        usage="recommend <link>", aliases=["rec"])
    @guild_only()
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def recommend(self, ctx, url: tools.clean_url):
        if not tools.is_valid_url(url):
            return await ctx.send("Invalid URL, cancelling...", delete_after=60)

        async with ctx.typing():
            book = await tools.get_book_from_url(url)

        if not await self.rec_is_confirmed(ctx, book):
            return await ctx.send("Cancelling...", delete_after=60)

        rec_reason = await self.get_rec_reason(ctx)
        rec = {
            "book": book,
            "recommendedBy": [ctx.author.id],
            "reason": rec_reason,
            "rec_id": None
        }
        rec_repo = RecommendationRepository()
        result = rec_repo.insert(rec)
        if result.acknowledged is False:
            return await ctx.send("Error inserting rec to db. Cancelling...", delete_after=60)
        embed = RecommendationEmbed(rec_by=ctx.author.display_name)
        embed.create(rec)
        sent = await ctx.send(embed=embed)
        rec_repo.update(
            {"_id": result.inserted_id}, {"$set": {"rec_id": sent.id}})
        return

    async def rec_is_confirmed(self, ctx, book):
        view = Confirm(ctx.author.id)
        await ctx.send(
            f"{ctx.author.mention}, you are giving a recommendation for"
            f" **{book['title']}** by *{book['authors']}*. Please confirm.",
            delete_after=60, view=view)
        await view.wait()
        return view.value

    async def get_rec_reason(self, ctx):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        timeout_min = 10
        await ctx.send(
            "Give a reason for the recommendation. "
            "What did you like about the book? Why should other people read it?\n"
            "Please type carefully and try to write an informative message"
            " rather than just messages along the lines like"
            " \"I liked it\", \"It was good\" etc.\n"
            f"The bot will time-out in {timeout_min} minutes.",
            delete_after=600)
        try:
            reason_msg = await self.bot.wait_for("message", timeout=60*timeout_min, check=check)
        except Exception as e:
            logger.error(e)
            return None
        reason = str(reason_msg.content)
        await reason_msg.delete()
        return reason


def setup(bot):
    bot.add_cog(RecommendationCommands(bot))
