"""Tests for src/link_parser.py"""
import unittest
from unittest.mock import patch, Mock

from link_parser import ThreadPoolLinkHandler


class TestThreadPoolLinkHandler(unittest.TestCase):
    def setUp(self):
        self.link = "http://en.wikipedia.org/wiki/Genus"
        self.max_workers = 10
        self.wiki = ThreadPoolLinkHandler(self.link, self.max_workers)

    @patch("link_parser.requests.Session.get")
    def test_url_downloader(self, mocked_get):
        mocked_get.return_value = Mock(status_code=200, text="1")
        result = self.wiki.url_downloader(self.link)
        mocked_get.assert_called_with(self.link, timeout=1)
        assert result == "1"

    @patch("requests.sessions.Session.head")
    def test_check_url_headers(self, mocked_head):
        mocked_head.return_value.status_code = 200
        mocked_head.return_value.headers = {"Last-Modified": "some_date"}
        result = self.wiki.check_url_headers(self.link)
        mocked_head.assert_called_with(self.link, timeout=1)
        assert result == "some_date"
