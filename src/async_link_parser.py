#!/usr/bin/python3
"""Module for parsing url link"""

import asyncio
import json
import logging.handlers
import os
import sqlite3
import time
from configparser import ConfigParser
from logging.config import fileConfig

import aiohttp
from pymemcache.client.base import PooledClient

from cli import parse_arguments
from utils.utils import (
    cache_cold_start,
    update_cache,
    links_extractor,
    save_to_file,
    save_url_links_to_database,
    get_last_db_ts,
    initial_db,
)

DEFAULT_CONFIG_PATH = "../etc/logging.json"


class AsyncioLinkHandler:
    """
    Class for handling links.
    Checks for other links after receiving data on the main link,
    allows you to receive and save data on found links in multi-threaded mode
    """

    def __init__(self, url_link, max_workers):
        self.url_link = url_link
        self.max_workers = max_workers
        self.queue = asyncio.Queue()
        self.last_modified_for_db = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        logger.info("Finished")

    async def url_downloader(self, url, session):
        """Gets data by link

        :param url: (str), the link by which we will receive some content:
        :return response: (str), text
        """
        try:
            async with session.get(url) as response:
                return await response.text()
        except Exception as error:
            logger.info(
                "%s occurred, no data received when processing the %s"
                % (error, url)
            )

    async def worker(self, session):
        """Handle links from queue"""
        while True:
            try:
                url_link = await self.queue.get()
                self.queue.task_done()
                response = await session.head(url_link)
                last_modified = response.headers.get("Last-Modified")
                if last_modified and update_cache(
                    url_link, last_modified, cache, logger
                ):
                    content = await self.url_downloader(url_link, session)
                    if content:
                        file_name = url_link.split("/")[-1]
                        save_to_file(file_name, content, path_to_file_save)
                        self.last_modified_for_db.append(
                            (url_link, last_modified)
                        )
            except Exception as error:
                logger.info(error)

    async def runner(self):
        """Run links handler with asyncio"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            html = await self.url_downloader(self.url_link, session)
            urls = links_extractor(html)
            # Put url into the queue.
            for url in urls:
                self.queue.put_nowait(url)
            for i in range(self.max_workers):
                task = asyncio.create_task(self.worker(session))
                tasks.append(task)
            # Wait until the queue is fully processed.
            await self.queue.join()
            # Cancel our worker tasks.
            for task in tasks:
                task.cancel()
            # add url and last modified date to database
            save_url_links_to_database(db, self.last_modified_for_db, logger)
            self.last_modified_for_db.clear()

            # Wait until all worker tasks are cancelled.
            await asyncio.gather(*tasks, return_exceptions=True)


async def main(url_link, max_workers):
    if cache.stats()[b"total_items"] == 0:
        cache_cold_start(cache, db, logger)
    while True:
        if get_last_db_ts(db, logger):
            async with AsyncioLinkHandler(url_link, max_workers) as new_wiki:
                await new_wiki.runner()
        time.sleep(int(config["sync"]["timeout"]))


if __name__ == "__main__":
    args = parse_arguments()

    config = ConfigParser()
    config.read(args.config)

    if os.path.exists(DEFAULT_CONFIG_PATH):
        with open(DEFAULT_CONFIG_PATH, "rt") as f:
            logger_config = json.load(f)
            logger_config["loggers"]["main"][
                "level"
            ] = args.logging_level
        logging.config.dictConfig(logger_config)
    else:
        logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger("main")

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

    db = sqlite3.connect(path_to_db)
    initial_db(db, logger)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(url_link, max_workers))
    loop.close()
