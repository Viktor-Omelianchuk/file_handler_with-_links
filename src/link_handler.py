import argparse
import logging
import os
import queue
import re
from concurrent.futures.thread import ThreadPoolExecutor

import requests
from pymemcache.client.base import PooledClient

WORK_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

MAX_WORKERS = 10

CACHE = PooledClient("127.0.0.1", max_pool_size=MAX_WORKERS)

logging.basicConfig(level=logging.INFO, filename="link_handler_log.log")
logger = logging.getLogger()


def links_extractor(content: str) -> list:
    """The method allows you to get all url links on the page
    linking to an article from wikipedia

    :param content, HTML content from Wikipedia page
    :type content: str
    :return list with all links to 'wikipedia' from the main_url_links:
    :rtype list
    """
    result = re.findall(r"(?<=/wiki/)[\w()]+", content)
    list_with_url_links = list(
        set([os.path.join("http://en.wikipedia.org/wiki/", link)
             for link in result])
    )
    return list_with_url_links


def save_to_file(file_name: str, content: str, directory="html_downloads"):
    """Saves data content to .html file"

    :param file_name: The name of file which much be save
    :type file_name: str
    :param content: Some content which need save
    :rtype str
    :param directory: Directory where file will be save
    :rtype str.
    """
    if not os.path.exists(os.path.join("html_downloads")):
        os.mkdir(os.path.join(WORK_DIRECTORY, directory))
    try:
        with open(
            os.path.join(WORK_DIRECTORY, directory, f"{file_name}.html"), "w"
        ) as file:
            file.write(content)
            return True
    except IOError as error:
        logger.info(
            f"{error}, while processing the link "
            f'"{file_name}" the data was not saved.'
        )
    return False


def check_into_memcached(link: str, content: str):
    """
    The function check if link in CACHE

    :param link: URL link
    :rtype str
    :param content: Content HTML page
    :rtype str
    :return: True if block try worked correct, else False
    """
    try:
        result = CACHE.get(link)
        if result is None or int(result) != hash(content):
            CACHE.set(link, hash(content))
            return True
    except Exception as error:
        logger.info(f"{error}, while processing the link ")
    return False


class LinkHandler:
    """
    Class for handling links.
    Checks for other links after receiving data on the main link,
    allows you to receive and save data on found links in multi-threaded mode
    """

    def __init__(self, url_link):
        self.url_link = url_link
        self.session = requests.Session()
        self.queue = queue.Queue()
        self.max_workers = MAX_WORKERS
        self.counter = 0

    def url_downloader(self, link: str) -> str:
        """Gets data by link

        :param link, the link by which we will receive some data:
        :type link, str
        :return response:
        :rtype str
        """
        try:
            response = self.session.get(link, timeout=1)
            if response.status_code == 200:
                return response.text
        except Exception as error:
            logger.info(
                f"{error} occurred while "
                f"retrieving data from the link '{link}'"
            )

    def worker(self):
        """Handle links from queue"""

        while not self.queue.empty():
            try:
                url_link = self.queue.get()
                content = self.url_downloader(url_link)
                if check_into_memcached(url_link, content):
                    file_name = url_link.split("/")[-1]
                    save_to_file(file_name, content)
                if self.counter <= 500:
                    for link in links_extractor(content):
                        self.queue.put(link)
                        self.counter += 1
            except Exception as error:
                logger.info(error)

    def runner(self):
        """Run links handler by thread"""

        response = self.url_downloader(self.url_link)
        URLS = links_extractor(response)
        for link in URLS:
            self.queue.put(link)
        threads = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for thread in range(self.max_workers):
                threads.append(executor.submit(self.worker))


# wiki = LinkHandler('https://en.wikipedia.org/wiki/'
#                    'Special:WhatLinksHere/Portal:Current_events')
# wiki.runner()
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--link",
        type=str,
        required=True,
        help="Name of file with HTTP URLs from current directory",
    )
    args = parser.parse_args()

    if args.link:
        wiki = LinkHandler(args.link)
        wiki.runner()
