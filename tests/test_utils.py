"""Tests for src/utils/utils.py"""
from unittest.mock import mock_open, patch

# from utils.utils import links_extractor, save_to_file
import sys
sys.path.append('/mnt/STORAGE/python_project/SS/first_task/file_handler_with_links/src/utils/')
from utils import links_extractor, save_to_file


def test_links_extractor():
    content = """
        en.wikipedia.org/wiki/Sahrawi_Arab_Democratic_Republic,
        en.wikipedia.org/wiki/Car,
        en.wikipedia.org/wiki/Gondar_Airport,
        en.wikipedia.org/wiki/Gondar_Airport,
        en.wikipedia.org/wiki/Prime_Minister_of_Vietnam
    """
    result = [
        'https://en.wikipedia.org/wiki/Sahrawi_Arab_Democratic_Republic',
        'https://en.wikipedia.org/wiki/Car',
        'https://en.wikipedia.org/wiki/Gondar_Airport',
        'https://en.wikipedia.org/wiki/Prime_Minister_of_Vietnam',
    ]
    function_result = links_extractor(content)
    assert len(function_result) == len(result)
    assert sorted(result) == sorted(function_result)


@patch('builtins.open', new_callable=mock_open)
def test_save_to_file(mocked_file):
    file_name = "http://en.wikipedia.org/wiki/Genus"
    content = "Message to write on file to be written"
    path_to_file_save = '../'
    save_to_file(file_name, content, path_to_file_save)
    mocked_file().write.assert_called_once_with(content)


# @patch()
# def test_check_into_memcached():
#     link = "http://en.wikipedia.org/wiki/Genus"
#     last_modified = 'Wed, 18 Nov 2020 04:46:06 GMT'


if __name__ == "__main__":
    test_links_extractor()
    test_save_to_file()

# @patch('requests.sessions.Session.get')
# def test_url_downloader(mock_get):
#     link = "http://en.wikipedia.org/wiki/Genus"
#     session = requests.Session()
#     mock_get.return_value.ok = True
#     url_downloader(session, link)
#     mock_get.assert_called_once_with(link)
