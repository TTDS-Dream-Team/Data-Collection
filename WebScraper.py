import json
import zlib
import time
import base64
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Book:

    def __init__(self, db, url):

        self.db = db

        self.soup = self.get_soup(url)
        self.url = url
        self.description = self.get_description()
        self.author = self.get_author()
        self.book_id = self.get_book_id()
        self.isbn = self.get_isbn()
        self.average_rating = self.get_average_rating()
        self.image_url = self.get_image_url()
        self.title = self.get_book_title()
        self.publication_year = self.get_publication_year()
        self.reviews, self.review_ratings = self.get_reviews()
        self.review_count = self.get_review_count()

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

        return authorName.text.strip()

    def get_description(self):
        """
        Returns the full description of the book that
        is hidden on the webpage
        """
        descriptionDiv = self.soup.find(id='description')

        para = descriptionDiv.find('span', style="display:none")

        compressed_text = zlib.compress(bytes(para.text.strip(), 'utf-8'))

        return compressed_text

    def get_book_id(self):
        """
        Returns the Goodreads book id
        """
        book_idDiv = self.soup.find(id='book_id')

        return book_idDiv['value'].strip()

    def get_isbn(self):
        """
        Returns the ISBN number of the book
        """
        detailsDiv = self.soup.find('div', id="details")

        date = detailsDiv.text.split("Published")[1].split()

        isbn = [s for s in date if s.isdigit()][1]

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
        imageDiv = self.soup.findAll('meta', attrs={'name':"twitter:image"})

        return imageDiv[0]['content']

    def get_publication_year(self):
        """
        Returns the year the book was published
        """
        detailsDiv = self.soup.find('div', id="details")

        date = detailsDiv.text.split("Published")[1].split()

        year = [s for s in date if s.isdigit()][0]

        return year.strip()

    def get_book_title(self):
        """
        Returns the title of the book
        """

        detailsDiv = self.soup.find('h1', id="bookTitle")
        return detailsDiv.text.strip()

    def get_review_count(self):
        """
        Returns the number of reviews the book has at the
        time of scrapping
        """
        reviewCountDiv = self.soup.find('div', class_="reviewControls--left greyText")

        review_text = reviewCountDiv.text.strip()

        tokens = review_text.split()

        reviewCount = [s for s in tokens if s.replace(',', '').isdigit()][1]

        return reviewCount.strip()

    def get_review_rating_num(self, review_rating):
        if (review_rating == "it was amazing"):
            return 5
        elif (review_rating == "really liked it"):
            return 4
        elif (review_rating == "liked it"):
            return 3
        elif (review_rating == "it was ok"):
            return 2
        else:
            return 1

    def get_reviews(self):
        """
        Returns a list of all compressed review texts
        for the current book
        """
        reviews = self.soup.findAll('div', class_="left bodycol")
        review_texts = []
        review_ratings = {}
        for review in reviews:
            review_text = review.find('span', style="display:none")
            if not review_text is None:
                compressed_text = zlib.compress(bytes(review_text.text.strip(), 'utf-8'))

                review_texts.append(compressed_text)

                review_rating = review.find('span', class_="staticStars notranslate")['title']

                rating = self.get_review_rating_num(review_rating)

                review_ratings[compressed_text] = rating

        return review_texts, review_ratings

    def construct_JSON(self):
        """
        Established a JSON object for each review
        about the current book and returns an
        array of all the reviews
        """

        array_JSON = []

        for review in self.reviews:

            review_json = {}

            review_json['book_id'] = self.book_id
            review_json['isbn'] = self.isbn
            review_json['average_rating'] = self.average_rating
            review_json['image_url'] = self.image_url
            review_json['publication_year'] = self.publication_year
            review_json['text_reviews_count'] = self.review_count
            review_json['url'] = self.url
            review_json['description'] = self.description
            review_json['review_text'] = review
            review_json['rating'] = self.review_ratings[review]
            review_json['book_title'] = self.title

            array_JSON.append(review_json)

        return array_JSON

    def upload(self, array_reviews):
        """
        Given an array of JSON objects
        uploads them to the database assigned
        to this book object
        """

        print (bcolors.OKBLUE + "\n\nUPLOADING REVIEWS FOR {}...".format(self.title) + bcolors.ENDC)

        result= self.db.scraper_test.insert_many(array_reviews)

        print (bcolors.OKGREEN + "COMPLETE\n\n" + bcolors.ENDC)


def get_book_urls():
    """
    Goes through the list of top 200 books published in
    the current month and returns an array containing
    the url to each book
    """

    page = requests.get('https://www.goodreads.com/book/popular_by_date')

    soup = BeautifulSoup(page.content, 'html.parser')

    book_url_divs = soup.findAll('a', class_="bookTitle")

    urls = ['https://www.goodreads.com' + str(div['href']) for div in book_url_divs]

    return urls


def main():

    start = time.process_time()

    # Connect to Mongo client
    client = MongoClient("mongodb+srv://cluster0.pdjrf.mongodb.net/Reviews_Data",
        username='CalumMcM',
        password='T3chN0l0gyT33m')

    db = client.Reviews_Data

    # Get urls for top 199 books this month
    book_urls = get_book_urls()

    #Upload top 199 books for this month
    for url in book_urls:

        print (url)
        webScraperPage = Book(db, url)

        book_reviews = Book.construct_JSON(webScraperPage)

        Book.upload(webScraperPage, book_reviews)

    print("FINISHED IN: {:.2f} Seconds".format(time.process_time() - start))

if __name__ == "__main__":

    main()
