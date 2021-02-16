import requests
from bs4 import BeautifulSoup

class WebScraper:

    def __init__(self, url):
        self.soup = self.get_soup(url)
        self.url = url
        self.description = self.get_description()
        self.author = self.get_author()
        self.book_id = self.get_book_id()
        #self.isbn = self.get_isbn()
        self.average_rating = self.get_average_rating()

    def get_soup(self, url):
        """
        Given a URL for a page, returns it as a
        BeautifulSoup object
        """
        page = requests.get(url)

        soup = BeautifulSoup(page.content, 'html.parser')

        return soup

    def get_author(self):
        """
        Returns the author of the book
        """
        authorDiv = self.soup.find(id='bookAuthors')

        authorName = authorDiv.find('span', itemprop="name")

        return authorName.text

    def get_description(self):
        """
        Returns the full description of the book that
        is hidden on the webpage
        """
        descriptionDiv = self.soup.find(id='description')

        para = descriptionDiv.find('span', style="display:none")

        return para.text

    def get_book_id(self):
        """
        Returns the Goodreads book id
        """
        book_idDiv = self.soup.find(id='book_id')

        return book_idDiv['value']

    def get_isbn(self):
        """
        Returns the ISBN number of the book
        """
        isbnDiv =  self.soup.find('script')
        print (isbnDiv)
        isbn = isbnDiv.find('div', class_='editionInfo')

        return isbn

    def get_average_rating(self):
        """
        Returns the average rating of the book after removing
        other text elements from average rating div
        """
        avg_ratingDiv = self.soup.find('div', class_="reviewControls--left")
        avg_ratingDiv.find('span', class_="u-visuallyHidden").decompose()
        avg_ratingDiv.find('span', class_="greyText").decompose()

        return avg_ratingDiv.text.strip()

    def get_image_url(self):
        """
        Returns the image url of the book
        """
        pass

    def get_publication_year(self):
        """
        Returns the publication year of the book
        """
        pass

    def get_review_text(self):
        """
        Returns a list of all review texts for the book
        """
        pass




if __name__ == "__main__":

    webScraperPage = WebScraper('https://www.goodreads.com/book/show/25752783-web-scraping-with-python')

    #print (webScraperPage.soup.prettify())
    print (webScraperPage.average_rating)
