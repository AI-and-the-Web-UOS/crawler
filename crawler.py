"""A single-server HTML webcrawler for a search engine.

The web crawler crawls all valid HTML pages from a single server from a single start-URL and adds
new entries to a MongoDB.
"""
from urllib.parse import urljoin
from urllib.parse import urlparse
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import validators
from sent2vec.vectorizer import Vectorizer
from pymongo import MongoClient
from ttictoc import tic, toc

logging.basicConfig(format='%(asctime)s_%(levelname)s: %(message)s', level=logging.INFO)

class WebCrawler:
    """The WebCrawler will subsequently crawl all HTML pages from a single server starting from the
    start URL defined in main.
    
    It searches the HTML pages for links and evaluates whether the links are valid, whether the
    response is an HTML page and whether tha URL is already in the search-backlog or has been
    visited and will add new URLs to the backlog of pages that the crawler still needs to visit.
    The crawler then extracts the H1 headers for each URL in the backlog. The headers will then be
    converted to a semantic embedding vector. The URL, the headers and the vectors will then be
    added to a database of pages.

    Attributes:
        urls_backlog: List with backlog of URLs that need to be visited (appended while crawling).
        urls_visited: A list of visited URLs that have been crawled already.
        urls_invalid: A list of invalid URLs for logging.
        urls_non_html: A list of non-HTML URLs for logging.
        page_results: A list of dicts with URLs, headers, vectors, content and date to be added to the MongoDB.
    """
    def __init__(self, urls: list):
        self.urls_backlog = urls
        self.urls_visited = []
        self.urls_invalid = []
        self.urls_non_html = []
        self.page_results = []

    def get_url(self, url: str, session: requests.Session) -> str:
        """
        Retrieving and returning the HTML text from a url.

        Args:
            url: The URL from which the HTML text should be retrieved.

        Returns:
            url_content: The extracted HTML content from the page as a string.
        """
        tic()
        url_content = session.get(url, timeout=0.1).text
        logging.info(msg=f'Getting HTML content in {toc()} s')
        return url_content

    def get_content(self, url_content: str) -> str:
        """
        Retrieving all paragraph-sections from an HTML string and concating them to a single string
        to retrieve content of webpage.

        Args:
            url_content: The extracted HTML content from a web page as a string.

        Returns:
            text: A single string with all p-tagged sections from the web page.
        """
        #tic()
        try:
            # merge all paragraphs to single string
            soup = BeautifulSoup(url_content,'html.parser')
            text = ''
            for p in soup.find_all('p'):
                text += p.text
            #logging.info(msg=f'Get paragraph content of page in {toc()} s')
            return text
        except Exception as e:
            logging.exception('Could not extract paragraphs from HTML. Returning HTML text. %s',e)
            return url_content

    def get_headers(self, url_content):
        """
        Retrieving all H1-headers from an HTML string and concating them to a single string.

        Args:
            url_content: The extracted HTML content from a web page as a string.

        Returns:
            text: A single string with all H1-headers from the web page.
        """
        #tic()
        try:
            # merge all h1 headers to single string
            soup = BeautifulSoup(url_content,'html.parser')
            text = ''
            for h1 in soup.find_all('h1'):
                text += h1.text
            #logging.info(msg=f'Getting headers of page in {toc()} s')
            return text
        except Exception as e:
            logging.exception('Could not extract h1 from HTML. Returning HTML text. %s',e)
            return url_content

    def get_links(self, url, html):
        """
        Extracting all links from an HTML page with BeautifulSoup and valdliating them. For invalid
        links the path from the HTML href will be joined with the base-URL and the new URL will be
        re-evaluated. Links that are still invalid are added to a list for logging. Links are
        yielded if they have been successfully validated.

        Args:
            url: URL of web page to fix relative links on page.
            html: HTML page content as a string.

        Returns:
            path: Valid URL found on page.
        """
        tic()
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            # find all links
            path = link.get('href')
            # validate if url is valid, if not try to join with base and check again
            if not validators.url(path):
                path = urljoin(url, path)
            if validators.url(path):
                yield path
            else:
                self.urls_invalid.append(path)
        logging.info(msg=f'Getting URLs linked on page in {toc()} s')

    def add_new_url(self, url, session):
        """
        Evaluating if a URL is already in the backlog, has been visited previously as well as
        whether the domain is the same as the domain of the start page and whether the content is an
        HTML page and adding new HTML pages from the same domain to the backlog. Appending non-HTML
        page URLs to a list for logging.

        Args:
            url: The URL found on a webpage.
        """
        # check if page is html, new, valid and on same server
        if url not in self.urls_visited and url not in self.urls_backlog and \
            url not in self.urls_invalid and urlparse(url).netloc == server_domain:
            if 'text/html' in session.head(url).headers['Content-Type']:
                self.urls_backlog.append(url)
            else:
                self.urls_non_html.append(url)

    def calc_vector(self, text: str, vectorizer):
        """
        Creating a vector for the input text (heading of a web page).
        
        Args:
            text: The text to be vectorized.
            model: A string specifying which model to use for vectorization.

        Returns:
            vectorizer.vectors: A list with the vectorization of the text.
        """
        vectorizer.run([text])
        return vectorizer.vectors

    def crawl(self, url):
        """
        Crawling URLs and headers from a page and appending the results to a dict.

        Args:
            url: The URL to crawl.
        """
        # create session, set header, get html
        s = requests.Session()
        s.headers = req_header
        html = self.get_url(url, session = s)
        # search for linked pages and add new to backlog
        for url in self.get_links(url, html):
            self.add_new_url(url, session = s)
        # add extracted content to page_results
        headers = str(self.get_headers(html))
        content = str(self.get_content(html))
        vector = self.calc_vector(text=headers, vectorizer=vect)
        crawled_page_result = {'title': headers, 'content': content, 'added': datetime.now(),\
            'url': url, 'vector': vector}
        self.page_results.append(crawled_page_result)

    def run(self):
        """
        Running the crawler for each URL in the backlog, removing crawled URLs from the backlog and
        adding them to a list with previously visited URLs.
        """
        while self.urls_backlog:
            url = self.urls_backlog.pop(0)
            logging.info(msg=f'Crawling {url}')
            try:
                self.crawl(url)
            except Exception as e:
                logging.critical('Failed crawling %s.\n%s', url, e, exc_info=True)
            finally:
                self.urls_visited.append(url)

        if len(self.urls_invalid) > 0:
            logging.info('Found %s non-valid urls: %s', len(self.urls_invalid),self.urls_invalid)
        if len(self.urls_non_html) > 0:
            logging.info('Found %s non-HTML urls: %s',len(self.urls_non_html), self.urls_non_html)
        logging.info('Finished crawling')

if __name__ == '__main__':
    # mongoDB connection
    client = MongoClient('mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS\
        =2000&appName=mongosh+2.0.2')
    db = client['searchDatabase']
    websiteCollection = db['Website']

    # define objects and variables
    vect = Vectorizer('distilbert-base-multilingual-cased')
    start_url = 'https://vm009.rz.uos.de/crawl/index.html'
    server_domain = urlparse(start_url).netloc
    # header to make requests seem more human-user-like to avoid being blocked when crawling
    # based on personal headers extracted from:
    # https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending
    req_header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) \
        Gecko/20100101 Firefox/119.0','Accept':'text/html,application/xhtml+xml,application/xml;\
            q=0.9,image/avif,image/webp,*/*;q=0.8'}
    crawler = WebCrawler(urls=[start_url])

    # run crawler and push results to mongoDB
    crawler.run()
    x = websiteCollection.insert_many(crawler.page_results)
