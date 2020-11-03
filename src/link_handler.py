import logging
import os
import queue
import re
from concurrent.futures.thread import ThreadPoolExecutor
from configparser import ConfigParser

import requests
from pymemcache.client.base import PooledClient

from cli import parse_arguments

WORK_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def links_extractor(content: str) -> list:
    """The method allows you to get all url links on the page
    linking to an article from wikipedia

    :param content: (str), HTML content from Wikipedia page
    :return (list), list with all links to 'wikipedia' from the main_url_links:
    """
    result = re.findall(r"(?<=/wiki/)[\w()]+", content)
    list_with_url_links = list(
        set(
            [
                os.path.join("http://en.wikipedia.org/wiki/", link)
                for link in result
            ]
        )
    )
    return list_with_url_links


def save_to_file(file_name: str, content: str, directory="html_downloads"):
    """Saves data content to .html file"

    :param file_name: (str), the name of file which much be save
    :param content: (str), some content which need save
    :param directory: (str), directory where file will be save
    """
    if not os.path.exists(os.path.join(WORK_DIRECTORY, directory)):
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
    return


def check_into_memcached(link: str, content: str):
    """
    The function check if link in CACHE

    :param link: (str), URL link
    :param content: (str), content HTML page
    :return: True if block try worked correct, else False
    """
    try:
        result = CACHE.get(link)
        if result is None or int(result) != hash(content):
            CACHE.set(link, hash(content))
            return True
    except Exception as error:
        logger.info(f"{error}, while processing the link ")
    return


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
        self.max_workers = max_workers
        self.counter = 0

    def url_downloader(self, link: str) -> str:
        """Gets data by link

        :param link: (str), the link by which we will receive some content:
        :return response: (str), text
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
                if content:
                    if check_into_memcached(url_link, content):
                        file_name = url_link.split("/")[-1]
                        save_to_file(file_name, content, directory)
                if self.counter <= number_of_links:
                    for link in links_extractor(content):
                        self.queue.put(link)
                        self.counter += 1
            except Exception as error:
                logger.info(error)

    def runner(self):
        """Run links handler by thread"""

        response = self.url_downloader(self.url_link)
        urls = links_extractor(response)
        if self.counter <= number_of_links:
            for link in urls:
                self.queue.put(link)
                self.counter += 1
        threads = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for thread in range(self.max_workers):
                threads.append(executor.submit(self.worker))


if __name__ == "__main__":
    args = parse_arguments()

    logging.basicConfig(
        level=args.logging_level, filename="link_handler_log.log"
    )
    logger = logging.getLogger()

    config = ConfigParser()
    config.read(args.config)

    max_workers = (
        int(args.max_worker)
        if args.max_worker
        else int(config["file_handler"]["max_workers"])
    )

    directory = (
        args.directory
        if args.directory
        else config["file_handler"]["default_directory"]
    )

    number_of_links = (
        int(args.number_of_links)
        if args.number_of_links
        else int(config["file_handler"]["number_of_links"])
    )

    CACHE = PooledClient("127.0.0.1", max_pool_size=max_workers)

    if args.link:
        wiki = LinkHandler(args.link)
        wiki.runner()
