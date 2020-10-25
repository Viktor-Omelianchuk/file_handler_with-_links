#!/usr/bin/env python

"""Tests for `file_handler_with_links` package."""
import unittest

import requests

from file_handler_with_links.file_handler_with_links import process_file_with_url, save_to_file, url_downloader


class TestViews(unittest.TestCase):
    def setup(self):
        self.session = requests.Session()

    def test_url_downloader(self):
        pass
