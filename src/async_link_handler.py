import asyncio
import logging.handlers
import os
import time
from configparser import ConfigParser
from logging.config import fileConfig

import aiohttp
from pymemcache.client.base import PooledClient

from cli import parse_arguments
from utils.utils import (
    links_extractor,
    check_into_memcached,
    save_to_file,
    save_url_links_to_database,
    cache_cold_start,
)


class AsyncioLinkHandler:
    def __init__(self, url_link, max_workers):
        self.url_link = url_link
        self.max_workers = max_workers
        self.queue = asyncio.Queue()
        self.last_modified_for_db = list()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass

    async def url_downloader(self, url, session):
        try:
            async with session.get(url) as response:
                return await response.text()
        except Exception as error:
            logger.info(
                "%s occurred, no data received when processing the %s"
                % (error, url)
            )

    async def worker(self, session):
        while True:
            try:
                url_link = await self.queue.get()
                self.queue.task_done()
                response = await session.head(url_link)
                if "Last-Modified" in response.headers:
                    last_modified = response.headers["Last-Modified"]
                    if last_modified and check_into_memcached(
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
        # cache cold start
        if cache.stats()[b"total_items"] == 0:
            cache_cold_start(cache, path_to_db, logger)
        async with aiohttp.ClientSession() as session:
            html = await self.url_downloader(self.url_link, session)
            urls = links_extractor(html)
            # Put url into the queue.
            for url in urls:
                self.queue.put_nowait(url)
            # Create workers tasks to process the queue concurrently.
            tasks = []
            for i in range(self.max_workers):
                task = asyncio.create_task(self.worker(session))
                tasks.append(task)
            # Wait until the queue is fully processed.
            await self.queue.join()
            # Cancel our worker tasks.
            for task in tasks:
                task.cancel()
            # add url and last modified date to database
            save_url_links_to_database(
                path_to_db, self.last_modified_for_db, logger
            )
            self.last_modified_for_db.clear()

            # Wait until all worker tasks are cancelled.
            await asyncio.gather(*tasks, return_exceptions=True)


async def main(url_link, max_workers):
    async with AsyncioLinkHandler(url_link, max_workers) as new_wiki:
        await new_wiki.runner()


if __name__ == "__main__":
    args = parse_arguments()

    config = ConfigParser()
    config.read(args.config)

    fileConfig("../etc/logging_config_for_async_link_handler.ini")
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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(url_link, max_workers))
    loop.close()
