import logging
from abc import abstractmethod

from utils import http
from utils.views import Confirm, Options

logger = logging.getLogger('botlogs')


class BookCommands():
    def __init__(self):
        pass

    @abstractmethod
    async def search(self, ctx, query_text):
        if not await self.is_query_text_valid(query_text):
            return await ctx.send("Query cannot be an empty string!")
        async with ctx.typing():
            results = await self.get_search_query_results(query_text)
        if len(results) == 0:
            return await ctx.reply(f"No results found for '{query_text}'")
        e = self.SearchEmbed(bot=self.bot)
        e.create(query_text, results)
        options = []
        for i, res in enumerate(results):
            options.append({'label': res['title'], 'emoji': "📕",
                           'value': i, 'description': res['authors']})
        view = Options(options=options)
        sent_message = await ctx.reply("To see details of a particular book, "
                                       "select the choice from the dropdown", embed=e, view=view)
        await view.wait()
        async with ctx.typing():
            if len(view.dropdown.values) == 0:
                return
            details = await self.get_book_query_results(results[int(view.dropdown.values[0])])
            embed = self.BookEmbed(bot=self.bot)
            embed.create(details)
        await sent_message.delete()
        return await ctx.reply(embed=embed)

    @abstractmethod
    async def link(self, ctx, query_text):
        if not await self.is_query_text_valid(query_text):
            return await ctx.send("Query cannot be an empty string!")
        async with ctx.typing():
            results = await self.get_search_query_results(query_text, num_results=1)
        if len(results) == 0:
            return await ctx.reply(f"No results found for '{query_text}'")

        result = results[0]
        return await ctx.reply(
            f"**{result['title']}** - *{result['authors']}*\n"
            f"{self.url_prefix + result['book_url']}")

    @abstractmethod
    async def book(self, ctx, query_text):
        if not await self.is_query_text_valid(query_text):
            return await ctx.reply("Query cannot be an empty string!")
        async with ctx.typing():
            results = await self.get_search_query_results(query_text, num_results=1)
        if len(results) == 0:
            return await ctx.reply("Couldn't find anything for given input")
        async with ctx.typing():
            details = await self.get_book_query_results(results[0])
            embed = self.BookEmbed(bot=self.bot)
            embed.create(details)
        view = Confirm(ctx.author.id)
        sent = await ctx.reply(embed=embed, view=view)
        await view.wait()
        if view.value is False:
            await sent.delete()
        return

    @abstractmethod
    async def cover(self, ctx, query_text):
        if not await self.is_query_text_valid(query_text):
            return await ctx.reply("Query cannot be an empty string!")
        async with ctx.typing():
            results = await self.get_search_query_results(query_text, num_results=1)
        if len(results) == 0:
            return await ctx.reply("Couldn't find anything for given input")
        async with ctx.typing():
            details = await self.get_book_query_results(results[0])
        return await ctx.reply(details['thumbnail'])

    @abstractmethod
    async def is_query_text_valid(self, query_text):
        if query_text == "":
            logger.error("search: Query cannot be an empty string!")
            return False
        else:
            return True

    @abstractmethod
    async def get_search_query_results(self, query_text, num_results=5):
        queryWords = query_text.split()
        queryParam = '+'.join(queryWords)
        queryUrl = self.search_url.format(queryParam)
        logger.debug("search: queryUrl:{}".format(queryUrl))
        response = await http.get(queryUrl)
        parser = self.parser(response)
        results = parser.parse_search_page(num_results)
        logger.debug("search: results:{}".format(results))
        return results

    @abstractmethod
    async def get_book_query_results(self, search_query_result):
        book_query_url = self.url_prefix + search_query_result["book_url"]
        response = await http.get(book_query_url)
        parser = self.parser(response)
        details = parser.parse_book_page()
        search_query_result["book_url"] = book_query_url
        return details
