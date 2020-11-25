"""Tests for src/link_handler_with_multithreading.py"""
import unittest
from unittest.mock import patch

from link_handler_with_multithreading import ThreadPoolLinkHandler


class TestThreadPoolLinkHandler(unittest.TestCase):
    def setUp(self):
        self.link = "http://en.wikipedia.org/wiki/Genus"
        self.max_workers = 10
        self.wiki = ThreadPoolLinkHandler(self.link, self.max_workers)

    @patch('requests.sessions.Session.get')
    def test_url_downloader(self, mocked_session):
        # attrs = {'status_code.return_value': 200, 'text': 'text'}
        # mocked_session.configure_mock(**attrs)
        self.wiki.url_downloader(self.link)
        mocked_session.assert_called_once()
        mocked_session.assert_called_once_with(self.link, timeout=1)
        # assert mocked_session.status_code() == 200
        # assert mocked_session.text == 'text'

    @patch('requests.sessions.Session.head')
    def test_check_url_headers(self, mocked_session):
        self.wiki.check_url_headers(self.link)
        mocked_session.assert_called_once()
        mocked_session.assert_called_once_with(self.link, timeout=1)
