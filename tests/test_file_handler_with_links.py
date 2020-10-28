"""Tests for `src` package."""
import requests

from unittest.mock import mock_open, patch
from src.file_handler import save_to_file, url_downloader

# class TestUrlDownloader(unittest.TestCase):
#     def test_url_downloader(self):
#         self.session = requests.session()
#         self.link = "http://en.wikipedia.org/wiki/Genus"
#         self.response = url_downloader(self.session, self.link)
#         self.assertEqual(self.response.status_code, 200)
#         self.assertIsNotNone(self.response)
#         self.assertIsInstance(self.response, requests.models.Response)
#         self.assertIsInstance(self.response.text, str)


def test_url_downloader():
    link = "http://en.wikipedia.org/wiki/Genus"
    session = requests.Session()
    with patch('requests.sessions.Session.get') as mock_get:
        mock_get.return_value.ok = True
        url_downloader(session, link)
    mock_get.assert_called_once_with(link)


def test_save_to_file():
    link = "http://en.wikipedia.org/wiki/Genus"
    content = "Message to write on file to be written"
    m = mock_open()
    with patch("builtins.open", m) as mocked_file:
        save_to_file(link, content)

    mocked_file().write.assert_called_once_with(content)
