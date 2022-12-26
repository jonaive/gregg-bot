import logging

from classes.GoodreadsParser import GoodreadsParser

from utils import http

log = logging.getLogger(__name__)


def clean_url(url):
    return url.split('?')[0]


def is_valid_url(url):
    # TODO: Validate URL
    return True


async def get_book_from_url(url: clean_url):
    response = await http.get(url)
    parser = GoodreadsParser(response)
    book = parser.parse_book_page()
    book["book_url"] = url
    return book
