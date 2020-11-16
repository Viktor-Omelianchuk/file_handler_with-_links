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
                os.path.join("http://en.wikipedia.org/wiki/", link)
                for link in result
            ]
        )
    )
    return list_with_url_links


def save_to_file(file_name: str, content: str, path_to_file_save: str, logger=None):
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
            logger.info("%s occurred %s was not saved" % (error, file_name))


def check_into_memcached(
    link: str, content: str, cache: PooledClient, logger=None
):
    """
    The function check if link in CACHE

    :param link: (str), URL link
    :param content: (str), content HTML page
    :param cache: (PooledClient). Session to memcached
    :param logger: connect the logging module logging
    :return: True if block try worked correct, else False
    """
    try:
        result = cache.get(link)
        if result is None or int(result) != hash(content):
            cache.set(link, hash(content))
            return True
    except Exception as error:
        if logger:
            logger.info(f"{error}, while processing the link into memcached ")


def create_connection_to_db(path_to_db, logger=None):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(path_to_db)
    except sqlite3.Error as error:
        if logger:
            logger.info("%s Error while working with SQLite" % error)
    return conn


def timestamp_sql_chacker(path_to_db: str, logger=None):
    """
    Funtction if is not database create db,
    compare current timestamt with timesmamp in database

    :return True: if current timestamp more 3600 seconds
    than databases timestamp
    """
    global db
    try:
        db = create_connection_to_db(path_to_db)
        sql = db.cursor()
        sql.execute(
            """CREATE TABLE IF NOT EXISTS timestamp (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                TIME INTEGER)"""
        )
        db.commit()
        for value in sql.execute("SELECT * FROM timestamp WHERE ID = 1"):
            if int(time.time()) - value[1] >= 3600:
                sql.execute(
                    f"UPDATE timestamp SET TIME = {int(time.time())} "
                    f"WHERE ID = 1"
                )
                db.commit()
                return True
    except sqlite3.Error as error:
        if logger:
            logger.info("%s Error while working with SQLite" % error)
    finally:
        if db:
            db.close()


def cache_cold_start(cache, path_to_db, logger=None):
    try:
        for value in get_url_links_from_database(path_to_db, logger):
            cache.set(value[0], value[1])
    except Exception as error:
        if logger:
            logger.info(f"{error}, while processing the link ")


def save_url_links_to_database(path_to_db, url, html_hash, logger=None):
    global db, sql
    try:
        db = create_connection_to_db(path_to_db)
        sql = db.cursor()
        sql.execute(
            """CREATE TABLE IF NOT EXISTS links (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                LINK TEXT UNIQUE,
                HASH INTEGER)"""

        )
        db.commit()
        sql.execute(f"""INSERT INTO links (LINK, HASH) VALUES ('{url}', {html_hash})""")
        db.commit()
    except sqlite3.Error as error:
        if 'UNIQUE' in str(error):
            sql.execute(
                f"""UPDATE links SET HASH = {html_hash} WHERE LINK = '{url}'"""
            )
            db.commit()
            print(f'{url} was updated')
        else:
            if logger:
                logger.info("%s Error while working with SQLite" % error)
    finally:
        if db:
            db.close()


def get_url_links_from_database(path_to_db, logger=None):
    global db
    try:
        db = create_connection_to_db(path_to_db)
        sql = db.cursor()
        for value in sql.execute("SELECT * FROM timestamp"):
            yield value
    except sqlite3.Error as error:
        if logger:
            logger.info("%s Error while working with SQLite" % error)
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    pass
