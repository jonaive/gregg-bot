import logging

from classes.Parser import Parser

logger = logging.getLogger('botlogs')


class StorygraphParser(Parser):
    def __init__(self, content):
        super().__init__(content)

    def parse_search_page(self, numResults=5):
        bookList = self.soup.find('span', class_="search-results-books-panes")
        if bookList is None:
            return []
        rows = bookList.find_all('div', class_="book-title-author-and-series")
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
        titleField = field.find('h3').find('a')
        title = titleField.get_text().strip()
        book_url = titleField['href']
        return title, book_url

    def extract_author_info(self, field):
        authors = field.find('p', class_="mb-1").find_all('a')
        authorNames = ', '.join([author.get_text().strip()
                                for author in authors])
        author_url = authors[0]['href']
        return authorNames, author_url

    def parse_book_page(self):
        result = {}
        result["title"] = self.extract_title_info(self.soup.find(
            "div", class_="book-title-author-and-series"))
        authorNames, author_url = self.extract_author_info(self.soup)
        result["authors"] = authorNames
        result["author_url"] = author_url
        result["thumbnail"] = self.extract_thumbnail()
        result["avg_rating"] = self.extract_avg_rating()

        leftPane = self.soup.find("div", class_="standard-pane mb-5")

        result["content_warnings"] = self.extract_content_warnings(leftPane)
        result["moods"] = self.extract_moods(leftPane)
        result["pace"] = self.extract_pace(leftPane)
        questions, answers = self.extract_questions_answers(leftPane)
        result["questions"] = questions
        result["answers"] = answers

        return result

    def extract_thumbnail(self):
        try:
            return self.soup.find("div", class_="book-cover").find("img")["src"]
        except Exception as e:
            logger.error(e)
            return "https://via.placeholder.com/150"

    def extract_avg_rating(self):
        try:
            div = self.soup.find("div", class_="standard-pane mb-5")
            avg_rating = div.find(
                'span', class_="average-star-rating").get_text().strip()
            return avg_rating
        except Exception as e:
            logger.error(e)
            return "N/A"

    def extract_content_warnings(self, div):
        try:
            content_warnings = div.find(
                'div', class_="content-warnings-information").stripped_strings
            result = ""
            for warn in content_warnings:
                if warn == "Graphic" or warn == "Moderate" or warn == "Minor":
                    warn = "*__" + warn + "__*"
                result += warn + "\n"
            return result
        except Exception as e:
            logger.error(e)
            return "N/A"

    def extract_moods(self, div):
        try:
            moodsDiv = div.find('div', class_="moods-list-reviews")
            moods = []
            for i, span in enumerate(moodsDiv.find_all('span')):
                if i % 2 == 0:
                    mood = span.get_text().title()
                else:
                    mood += " ("+span.get_text() + ")"
                    moods.append(mood)
            return moods
        except Exception as e:
            logger.error(e)
            return ["N/A"]

    def extract_pace(self, div):
        try:
            pacesDiv = div.find('div', class_="paces-reviews")
            paces = []
            for i, span in enumerate(pacesDiv.find_all('span')):
                if i % 2 == 0:
                    pace = span.get_text().title()
                else:
                    pace += " ({})".format(span.get_text())
                    paces.append(pace)
            return paces
        except Exception as e:
            logger.error(e)
            return ["N/A"]

    def extract_questions_answers(self, div):
        try:
            questions = [question.get_text() for question in div.find_all(
                'p', class_="review-character-question")]
            answers = [answer.get_text() for answer in div.find_all(
                'span', class_="review-response-summary")]
            return questions, answers
        except Exception as e:
            logger.error(e)
            return [], []
