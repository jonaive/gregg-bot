import logging
from abc import ABC, abstractmethod

import bs4

logger = logging.getLogger('botlogs')


class Parser(ABC):
    def __init__(self, content):
        self.content = content
        self.soup = bs4.BeautifulSoup(self.content, 'lxml')

    @abstractmethod
    def parse_search_page(self, numResults):
        pass

    @abstractmethod
    def parse_search_result(self, result):
        pass

    @abstractmethod
    def parse_book_page(self):
        pass
