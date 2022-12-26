import logging

from classes.BookCommands import BookCommands
from classes.Embeds import StorygraphBookEmbed, StorygraphSearchEmbed
from classes.StorygraphParser import StorygraphParser
from discord.ext import commands
from utils.const import STORYGRAPH_PREFIX, STORYGRAPH_SEARCH_URL

logger = logging.getLogger('botlogs')


class StoryGraphCommands(commands.Cog, BookCommands, name="StoryGraph"):
    def __init__(self, bot):
        self.bot = bot
        self.parser = StorygraphParser
        self.search_url = STORYGRAPH_SEARCH_URL
        self.url_prefix = STORYGRAPH_PREFIX
        self.SearchEmbed = StorygraphSearchEmbed
        self.BookEmbed = StorygraphBookEmbed
        super().__init__()

    @commands.command(
        description="Shows the link of a book from StoryGraph",
        usage="sgl <title>", aliases=["sgl"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def sglink(self, ctx, *, query_text):
        return await super().link(ctx, query_text)

    @commands.command(name='sg',
                      description="Gets information about a book from StoryGraph",
                      usage="sg <title>")
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def book(self, ctx, *, query_text):
        return await super().book(ctx, query_text)

    @commands.command(
        name="sgsearch",
        description="Gets a list of book links from StoryGraph",
        usage="sgs <title>",
        aliases=["sgs"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def search(self, ctx, *, query_text):
        return await super().search(ctx, query_text)

    @commands.command(name="sgcover",
                      description="Shows the cover of a book from StoryGraph",
                      usage="sgcover <title>", aliases=["sgc", "sgthumbnail"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def cover(self, ctx, *, query_text):
        return await super().cover(ctx, query_text)

    async def get_book_query_results(self, searchQueryResult):
        details = await super().get_book_query_results(searchQueryResult)
        searchQueryResult["author_url"] = self.url_prefix + \
            searchQueryResult["author_url"]
        details.update(searchQueryResult)
        return details


def setup(bot):
    bot.add_cog(StoryGraphCommands(bot))
