"""Module with additional functions"""

import os
import re
import sqlite3
import time
from functools import wraps

from pymemcache import PooledClient


def retry(delay=5, retries=4, logger=None):
    """calling the decorated function applying an exponential backoff."""

    def retry_decorator(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            opt_dict = {"retries": retries, "delay": delay}
            while opt_dict["retries"] > 1:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if logger:
                        logger.info("Exception: {}".format(e))
                    time.sleep(opt_dict["delay"])
                    opt_dict["retries"] -= 1
            return f(*args, **kwargs)

        return f_retry

    return retry_decorator


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
                os.path.join("https://en.wikipedia.org/wiki/", link)
                for link in result
            ]
        )
    )
    return list_with_url_links


def save_to_file(
    file_name: str, content: str, path_to_file_save: str, logger=None
):
    """Saves data content to .html file"

    :param file_name: (str), the name of file which much be save
    :param content: (str), some content which need save
    :param path_to_file_save: (str), path where file will be save
    :param logger: connect the logging module logging
    """
    if not os.path.exists(path_to_file_save):
        os.mkdir(path_to_file_save)
    try:
        with open(
            os.path.join(path_to_file_save, f"{file_name}.html"), "w"
        ) as file:
            file.write(content)
    except IOError as error:
        if logger:
            logger.error("%s occurred %s was not saved" % (error, file_name))


def update_cache(
    link: str, last_modified: str, cache: PooledClient, logger=None
):
    """
    The function check if link in CACHE

    :param link: (str), URL link
    :param last_modified: (str), last modified date
    :param cache: (PooledClient). Session to memcached
    :param logger: connect the logging module logging
    :return: True if block try worked correct, else False
    """
    try:
        if last_modified:
            result = cache.get(link)
            if result is None or result.decode("utf-8") != last_modified:
                cache.set(link, last_modified)
                return True
    except Exception as error:
        if logger:
            logger.error(f"{error}, while processing the link into memcached ")


def initial_db(db, logger=None):
    """
    Funtction if is not database create db,
    :param db: Connection to database
    :return True: if current timestamp more 3600 seconds
    than databases timestamp
    """
    try:
        sql = db.cursor()
        sql.execute(
            """CREATE TABLE IF NOT EXISTS timestamp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time INTEGER)"""
        )
        db.commit()

        sql.execute(
            f"INSERT OR REPLACE INTO timestamp (id, time) "
            f"VALUES (1, {int(time.time()) - 3700})"
        )
        db.commit()

        sql.execute(
            """CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE,
                modified INTEGER)"""
        )
        db.commit()

    except sqlite3.Error as error:
        if logger:
            logger.error("%s Error while working with SQLite" % error)


def get_last_db_ts(db, logger=None):
    """
    Funtction compare current timestamt with timesmamp in database
    :param db: Connection to database
    :return True: if current timestamp more 3600 seconds
    than databases timestamp
    """
    try:
        sql = db.cursor()
        for value in sql.execute("SELECT * FROM timestamp WHERE ID = 1"):
            if int(time.time()) - value[1] >= 3600:
                sql.execute(
                    f"UPDATE timestamp SET time = {int(time.time())} "
                    f"WHERE id = 1"
                )
                db.commit()
                return True
    except sqlite3.Error as error:
        if logger:
            logger.error("%s Error while working with SQLite" % error)


def cache_cold_start(cache, db, logger=None):
    """The function fills the cache with data from the database
    :param cache: Connection to pymemcached
    :param db: Connection to database
    :param logger: connect the logging module logging
    """
    try:
        sql = db.cursor()
        for value in sql.execute("SELECT * FROM links"):
            cache.set(value[1], value[2])
    except sqlite3.Error as error:
        if logger:
            logger.error("%s Error while working with SQLite" % error)


def save_url_links_to_database(db, list_with_urls, logger=None):
    """The function saves url links and date of content last modified
    to database

    :param db: Connection to database
    :param list_with_urls: List with contain pair url and date of last modified
    :param logger: Connect the logging module logging
    :return:
    """
    try:
        sql = db.cursor()
        sql.executemany(
            "INSERT OR REPLACE INTO links (link, modified) VALUES (?, ?)",
            list_with_urls,
        )
        db.commit()

    except sqlite3.Error as error:
        if logger:
            logger.error("%s Error while working with SQLite" % error)
