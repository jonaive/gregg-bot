import logging
import random

from classes.Parser import Parser

logger = logging.getLogger('botlogs')


class GoodreadsParser(Parser):
    def __init__(self, content):
        super().__init__(content)

    def parse_search_page(self, numResults=5):
        bookList = self.soup.find("table", class_="tableList")
        if bookList is None:
            return []
        rows = bookList.find_all("tr")
        results = []
        for row in rows[:numResults]:
            bookInfo = self.parse_search_result(row)
            results.append(bookInfo)
        return results

    def parse_search_result(self, row):
        result = {}
        title, book_url = self.extract_title_info(row)
        result["title"] = title
        result["book_url"] = book_url
        authorNames, author_url = self.extract_author_info(row)
        result["authors"] = authorNames
        result["author_url"] = author_url
        return result

    def extract_title_info(self, field):
        titleField = field.find('a', class_="bookTitle")
        title = titleField.find('span').get_text().strip()
        book_url = titleField['href'].split('?')[0]
        return title, book_url

    def extract_author_info(self, field):
        authors = field.find_all('a', class_="authorName")
        authorNames = ', '.join([author.get_text().strip()
                                for author in authors])
        author_url = authors[0]['href'].split('?')[0]
        return authorNames, author_url

    def parse_book_page(self):
        result = {}
        result["title"] = self.soup.find(
            "h1", id="bookTitle").get_text().strip()
        authorNames, author_url = self.extract_author_info(self.soup)
        result["authors"] = authorNames
        result["author_url"] = author_url
        result["thumbnail"] = self.extract_thumbnail()
        result["description"] = self.extract_description()
        result['genres'] = self.extract_genres()
        result["num_pages"] = self.extract_num_pages()
        result["avg_rating"] = self.extract_avg_rating()
        result["num_rating"] = self.extract_num_rating()

        return result

    def extract_num_rating(self):
        try:
            metaDiv = self.soup.find('div', id='bookMeta')
            num_rating = metaDiv.find('meta', attrs={'itemprop': "ratingCount"})[
                'content'].strip()
            return num_rating
        except Exception as e:
            logger.error(e)
            return "N/A"

    def extract_avg_rating(self):
        try:
            metaDiv = self.soup.find('div', id='bookMeta')
            avg_rating = metaDiv.find(
                'span', attrs={'itemprop': "ratingValue"}).get_text().strip()
            return avg_rating
        except Exception as e:
            logger.error(e)
            return "N/A"

    def extract_num_pages(self):
        try:
            num_pages = self.soup.find(
                'span', attrs={'itemprop': "numberOfPages"}).get_text().strip()
            return num_pages
        except Exception as e:
            logger.error(e)
            return "N/A"

    def extract_description(self):
        try:
            descDiv = self.soup.find('div', id="description")
            descText = descDiv.find_all('span')[1]
            for br in descText.find_all("br"):
                br.replace_with("\n")
            descText = descText.get_text().strip()
            return descText
        except Exception as e:
            logger.error(e)
            return "Not available"

    def extract_genres(self):
        try:
            genres = self.soup.find_all(
                'a', class_="actionLinkLite bookPageGenreLink")
            genres = [genre.get_text().title() for genre in genres]
            if len(genres) == 0:
                return ["N/A"]
            return genres
        except Exception as e:
            logger.error(e)
            return ["N/A"]

    def extract_thumbnail(self):
        try:
            return self.soup.find('img', id='coverImage')['src']
        except Exception as e:
            logger.error(e)
            return "https://via.placeholder.com/150"

    def parse_quotes_page(self):
        quoteDivs = self.soup.find_all('div', class_="quote")
        if len(quoteDivs) == 0:
            return ""
        quoteNum = random.randint(0, len(quoteDivs)-1)
        selected = quoteDivs[quoteNum]
        quoteText = selected.find(
            'div', class_="quoteText").get_text("\n", strip=True)
        return quoteText
