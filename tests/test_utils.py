"""Tests for src/utils/utils.py"""
from unittest.mock import mock_open, patch

from utils.utils import (
    links_extractor,
    save_to_file,
    update_cache,
    cache_cold_start,
    get_last_db_ts,
    save_url_links_to_database,
    initial_db,
)


def test_links_extractor():
    content = """
        en.wikipedia.org/wiki/Sahrawi_Arab_Democratic_Republic,
        en.wikipedia.org/wiki/Car,
        en.wikipedia.org/wiki/Gondar_Airport,
        en.wikipedia.org/wiki/Gondar_Airport,
        en.wikipedia.org/wiki/Prime_Minister_of_Vietnam
    """
    result = [
        "https://en.wikipedia.org/wiki/Sahrawi_Arab_Democratic_Republic",
        "https://en.wikipedia.org/wiki/Car",
        "https://en.wikipedia.org/wiki/Gondar_Airport",
        "https://en.wikipedia.org/wiki/Prime_Minister_of_Vietnam",
    ]
    function_result = links_extractor(content)
    assert len(function_result) == len(result)
    assert sorted(result) == sorted(function_result)


@patch("builtins.open", new_callable=mock_open)
def test_save_to_file(mocked_file):
    file_name = "http://en.wikipedia.org/wiki/Genus"
    content = "Message to write on file to be written"
    path_to_file_save = "../html_downloads"
    save_to_file(file_name, content, path_to_file_save)
    mocked_file().write.assert_called_once()
    mocked_file().write.assert_called_once_with(content)


@patch("link_parser.PooledClient")
def test_check_into_memcached(mocked_cache):
    mocked_cache.get.return_value = None
    link = "http://en.wikipedia.org/wiki/Genus"
    last_modified = "Wed, 18 Nov 2020 04:46:06 GMT"
    update_cache(link, last_modified, mocked_cache)
    mocked_cache.get.assert_called_once_with(link)
    mocked_cache.set.assert_called_once_with(link, last_modified)


@patch("link_parser.sqlite3.connect")
def test_get_last_db_ts(mocked_connect):
    get_last_db_ts(mocked_connect)
    mocked_connect.cursor().execute.assert_called()
    mocked_connect.cursor().execute.assert_called_with(
        "SELECT * FROM timestamp WHERE ID = 1"
    )


@patch("link_parser.sqlite3.connect")
@patch("link_parser.PooledClient")
def test_cache_cold_start(mocked_cache, mocked_sqlite):
    mocked_sqlite.cursor().execute.return_value = [(1, 2, 3)]
    cache_cold_start(mocked_cache, mocked_sqlite)
    mocked_sqlite.cursor().execute.assert_called_with("SELECT * FROM links")
    mocked_cache.set.assert_called()


@patch("link_parser.sqlite3.connect")
def test_save_url_links_to_database(mocked_connect):
    list_with_urls = [
        ("link", "modified"),
    ]
    save_url_links_to_database(mocked_connect, list_with_urls)
    mocked_connect.cursor.assert_called_once()
    mocked_connect.cursor().executemany.assert_called_with(
        "INSERT OR REPLACE INTO links (link, modified) VALUES (?, ?)",
        list_with_urls,
    )
    mocked_connect.commit.assert_called()


@patch("link_parser.sqlite3.connect")
def test_initial_db(mocked_connect):
    initial_db(mocked_connect)
    mocked_connect.cursor.assert_called_once()
    mocked_connect.cursor().execute.assert_called_with(
        """CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT UNIQUE,
                modified INTEGER)"""
    )
    mocked_connect.commit.assert_called()
