"""Tests for `src` package."""
import requests

from unittest.mock import mock_open, patch
from src.file_handler import save_to_file, url_downloader


@patch('requests.sessions.Session.get')
def test_url_downloader(mock_get):
    link = "http://en.wikipedia.org/wiki/Genus"
    session = requests.Session()
    mock_get.return_value.ok = True
    url_downloader(session, link)
    mock_get.assert_called_once_with(link)


@patch('builtins.open', new_callable=mock_open)
def test_save_to_file(mocked_file):
    link = "http://en.wikipedia.org/wiki/Genus"
    content = "Message to write on file to be written"
    save_to_file(link, content)
    mocked_file().write.assert_called_once_with(content)
