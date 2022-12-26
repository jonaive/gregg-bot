import logging
import random

from classes.BookCommands import BookCommands
from classes.Embeds import GoodreadsBookEmbed, GoodreadsSearchEmbed
from classes.GoodreadsParser import GoodreadsParser
from discord.ext import commands
from discord.ext.commands.core import guild_only, has_any_role
from utils import http
from utils.const import (GOODREADS_PREFIX, GOODREADS_QUOTES_URL,
                         GOODREADS_SEARCH_URL)

logger = logging.getLogger('botlogs')


class GoodreadsCommands(commands.Cog, BookCommands, name="Goodreads"):
    def __init__(self, bot):
        self.bot = bot
        self.parser = GoodreadsParser
        self.search_url = GOODREADS_SEARCH_URL
        self.url_prefix = GOODREADS_PREFIX
        self.SearchEmbed = GoodreadsSearchEmbed
        self.BookEmbed = GoodreadsBookEmbed
        super().__init__()

    @commands.command(
        description="Shows the link of a book from Goodreads",
        usage="grl <title>", aliases=["grl"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def link(self, ctx, *, query_text):
        return await super().link(ctx, query_text)

    @commands.command(
        description="Shows the information about a book from Goodreads",
        usage="gr <title>", aliases=["gr"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def book(self, ctx, *, query_text):
        return await super().book(ctx, query_text)

    @commands.command(
        description="Gets a list of book links from Goodreads",
        usage="search <title>", aliases=["grs"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def search(self, ctx, *, query_text):
        return await super().search(ctx, query_text)

    @commands.command(
        description="Shows the cover of a book from Goodreads",
        usage="cover <title>", aliases=["cov", "thumbnail"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def cover(self, ctx, *, query_text):
        return await super().cover(ctx, query_text)

    @commands.command(
        description="Fetches a random quote from Goodreads",
        usage="quote [tag]", aliases=["q"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    @guild_only()
    @has_any_role('Elder', 'Elite', 'Ultra', 'Maniac')
    async def quote(self, ctx, *tags):
        async with ctx.typing():
            quote = await self.get_quote_query_results(tags)
        if len(quote) > 1000:
            return await ctx.send("The fetched quote didn't fit the character limit,\
                 please run the command again :/")
        if quote == "":
            return await ctx.send("Oops! Something went wrong, please try again, \
                or use the command without the tag")
        return await ctx.send(quote)

    async def get_book_query_results(self, searchQueryResult):
        details = await super().get_book_query_results(searchQueryResult)
        details.update(searchQueryResult)
        return details

    async def prepare_query_for_quote(self, tags):
        tagParam = '+'.join(tags)
        queryUrl = GOODREADS_QUOTES_URL
        if tagParam != "":
            queryUrl += "/search?q=" + tagParam + "&"
        pageNum = random.randint(1, 15)
        queryUrl += "?page=" + str(pageNum)
        return queryUrl

    async def get_quote_query_results(self, tags):
        quoteQueryUrl = await self.prepare_query_for_quote(tags)
        response = await http.get(quoteQueryUrl)
        parser = self.parser(response)
        quote = parser.parse_quotes_page()
        return quote


def setup(bot):
    bot.add_cog(GoodreadsCommands(bot))
