#!/usr/bin/python3
import logging.handlers
import os
import queue
import time
from concurrent.futures.thread import ThreadPoolExecutor
from configparser import ConfigParser
from logging.config import fileConfig

import requests
from pymemcache.client.base import PooledClient

from cli import parse_arguments
from utils.utils import (
    cache_cold_start,
    check_into_memcached,
    links_extractor,
    retry,
    save_to_file,
    save_url_links_to_database,
    timestamp_sql_checker,
)


class ThreadPoolLinkHandler:
    """
    Class for handling links.
    Checks for other links after receiving data on the main link,
    allows you to receive and save data on found links in multi-threaded mode
    """

    def __init__(self, url_link, max_workers):
        self.url_link = url_link
        self.max_workers = max_workers
        self.session = requests.Session()
        self.queue = queue.Queue()
        self.last_modified_for_db = list()

    @retry(delay=2, retries=2)
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
                "%s occurred, no data received when processing the %s"
                % (error, link)
            )

    def check_url_headers(self, link: str) -> str:
        """Gets headers by link

        :param link: (str), the link by which we will receive some headers
        :return response: (str), text
        """
        try:
            response = self.session.head(link, timeout=1)
            if (
                response.status_code == 200
                and "Last-Modified" in response.headers
                and response.headers["Last-Modified"]
            ):
                return response.headers["Last-Modified"]
        except Exception as error:
            logger.info(
                "%s occurred, no headers received when processing the %s"
                % (error, link)
            )

    def worker(self):
        """Handle links from queue"""

        while not self.queue.empty():
            try:
                url_link = self.queue.get()
                last_modified = self.check_url_headers(url_link)
                if last_modified and check_into_memcached(
                    url_link, last_modified, cache, logger
                ):
                    content = self.url_downloader(url_link)
                    if content:
                        file_name = url_link.split("/")[-1]
                        save_to_file(file_name, content, path_to_file_save)
                        self.last_modified_for_db.append(
                            (url_link, last_modified)
                        )

            except Exception as error:
                logger.info(error)

    def runner(self):
        """Run links handler by thread"""
        if cache.stats()[b"total_items"] == 0:
            cache_cold_start(cache, path_to_db, logger)
        while True:
            if timestamp_sql_checker(path_to_db, logger):
                html = self.url_downloader(self.url_link)
                urls = links_extractor(html)
                for link in urls:
                    self.queue.put(link)
                with ThreadPoolExecutor(
                    max_workers=self.max_workers
                ) as executor:
                    for thread in range(self.max_workers):
                        executor.submit(self.worker)
                # add url and last modified date to database
                save_url_links_to_database(
                    path_to_db, self.last_modified_for_db, logger
                )
                self.last_modified_for_db.clear()
            time.sleep(int(config["sync"]["timeout"]))


if __name__ == "__main__":
    args = parse_arguments()

    config = ConfigParser()
    config.read(args.config)

    fileConfig(
        "../etc/logging_config_for_link_handler_with_multithreading.ini"
    )
    logger = logging.getLogger()

    max_workers = int(
        args.max_workers or config["file_handler"]["max_workers"]
    )

    number_of_links = int(
        args.number_of_links or config["file_handler"]["number_of_links"]
    )

    directory = args.directory or config["file_handler"]["default_directory"]

    path_to_file_save = os.path.join("..", directory)

    url_link = args.link or config["file_handler"]["url_link"]

    cache = PooledClient(config["memcached"]["ip"], max_pool_size=max_workers)

    path_to_db = config["db"]["path_to_db"]

    wiki = ThreadPoolLinkHandler(url_link, max_workers)
    wiki.runner()
