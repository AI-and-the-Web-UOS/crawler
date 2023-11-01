"""A single-server HTML webcrawler for a search engine.

The web crawler crawls all valid HTML pages from a single server from a single start-URL and adds
new entries to a MongoDB.
"""

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import validators
from urllib.parse import urlparse
import regex as re


logging.basicConfig(format='%(asctime)s_%(levelname)s: %(message)s', level=logging.INFO)

class WebCrawler:
    """The WebCrawler will subsequently crawl all HTML pages from a single server starting from the start URL
    defined in main.
    
    It searches the HTML pages for links and evaluates whether the links are valid, whether the response is an
    HTML page and whether tha URL is already in the search-backlog or has been visited and will add new URLs to
    the backlog of pages that the crawler still needs to visit. The crawler then extracts the H1 headers for each
    URL in the backlog. **TO BE IMPLEMENTED:** The headers will then be converted to a semantic embedding vector.
    The URL, the headers and the vectors will then be added to a database of pages.

    Attributes:
        urls_backlog: A list with a backlog of URLs that need to be visited that is appended while crawling.
        urls_visited: A list of visited URLs that have been crawled already.
        urls_invalid: A list of invalid URLs for logging.
        urls_non_html: A list of non-HTML URLs for logging.
        page_results: A dict with URLs, headers and vectors to be added to the MongoDB.
    """
    def __init__(self, urls=[]):
        """Initializes the instance of the webcrawler with start-URL list.

        Args:
            urls_backlog: A list with a backlog of URLs that need to be visited that is appended while crawling.
            urls_visited: A list of visited URLs that have been crawled already.
            urls_invalid: A list of invalid URLs for logging.
            urls_non_html: A list of non-HTML URLs for logging.
            page_results: A dict with URLs, headers and vectors to be added to the MongoDB.
        """
        self.urls_backlog = urls
        self.urls_visited = []
        self.urls_invalid = []
        self.urls_non_html = []
        self.page_results = {'url': [], 'headers': [], 'vector': []}
    
    def get_url(self, url):
        """
        Retrieving and returning the HTML text from a url.

        Args:
            url: The URL from which the HTML text should be retrieved.

        Returns:
            url_content: The extracted HTML content from the page as a string.
        """
        s = requests.Session()
        s.headers = req_header
        url_content = s.get(url).text
        return url_content

    
    def get_headers(self, url_content):
        """
        Retrieving all H1-headers from an HTML string and concating them to a single string.

        Args:
            url_content: The extracted HTML content from a web page as a string.

        Returns:
            text: A single string with all H1-headers from the web page.
        """
        try:
            soup = BeautifulSoup(url_content,'html.parser')
            text = ''
            for h1 in soup.find_all('h1'):
                text += h1.text
            return text
        except Exception as e:
            logging.exception(e)

    def get_links(self, url, html):
        """
        Extracting all links from an HTML page with BeautifulSoup and valdliating them. For invalid links
        the path from the HTML href will be joined with the base-URL and the new URL will be re-evaluated.
        Links that are still invalid are added to a list for logging. Links are yielded if they have been
        successfully validated.

        Args:
            url: URL of web page to fix relative links on page.
            html: HTML page content as a string.

        Returns:
            path: Valid URL found on page.
        """
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if not validators.url(path):
                path = urljoin(url, path)
            
            if validators.url(path):
                yield path
            else:
                self.urls_invalid.append(path)

    def add_new_url(self, url):
        """
        Evaluating if a URL is already in the backlog, has been visited previously as well as whether the domain is the same as
        the domain of the start page and whether the content is an HTML page and adding new HTML pages from the same domain to
        the backlog. Appending non-HTML page URLs to a list for logging.

        Args:
            url: The URL found on a webpage.
        """
        if url not in self.urls_visited and url not in self.urls_backlog and url not in self.urls_invalid and urlparse(url).netloc == server_domain:
            s = requests.Session()
            s.headers = req_header
            if 'text/html' in s.head(url).headers['Content-Type']:
                self.urls_backlog.append(url)
            else:
                self.urls_non_html.append(url)
    

    def crawl(self, url):
        """
        Crawling URLs and headers from a page and appending the results to a dict.

        Args:
            url: The URL to crawl.
        """
        html = self.get_url(url)
        for url in self.get_links(url, html):
            self.add_new_url(url)
        headers = str(self.get_headers(html))
        self.page_results['url'].append(url)
        self.page_results['headers'].append(headers)

    def run(self):
        """
        Running the crawler for each URL in the backlog, removing crawled URLs from the backlog and adding them
        to a list with previously visited URLs.
        """
        while self.urls_backlog:
            url = self.urls_backlog.pop(0)
            logging.info(msg=f'Crawling {url}')
            try:
                self.crawl(url)
            except Exception as e:
                logging.exception(f'Failed crawling {url}:\n{e}')
            finally:
                self.urls_visited.append(url)
        if len(self.urls_invalid) > 0:
            logging.info(f'Found {len(self.urls_invalid)} non-valid urls: {self.urls_invalid}')
        if len(self.urls_non_html) > 0:
            logging.info(f'Found {len(self.urls_non_html)} non-HTML urls: {self.urls_non_html}')
        logging.info(f'Finished crawling - Results:\n{self.page_results}')
    

if __name__ == '__main__':
    start_url = 'https://vm009.rz.uos.de/crawl/index.html'
    server_domain = urlparse(start_url).netloc
    # header to make requests seem more human-user-like to avoid being blocked when crawling - based on personal headers extracted from: https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending
    req_header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'}
    
    WebCrawler(urls=[start_url]).run()

