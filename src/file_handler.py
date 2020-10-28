"""Main module."""
import argparse
import os

import requests
from requests.exceptions import (ConnectionError, HTTPError, Timeout,
                                 TooManyRedirects)

WORK_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def url_downloader(session: requests.Session, link: str):
    """Gets data by reference"""
    try:
        response = session.get(link)
        if response.status_code == 200:
            return response
    except (ConnectionError, Timeout, TooManyRedirects, HTTPError) as error:
        print(f'{error} occurred while retrieving data from the link "{link}"')


def save_to_file(link: str, data: str):
    """Saves data to .html file"""
    if not os.path.exists(os.path.join(WORK_DIRECTORY, "html_downloads")):
        raise FileExistsError("The catalog html_downloads doesn't exist")
    try:
        with open(
            os.path.join(
                WORK_DIRECTORY, "html_downloads", f'{link.split("/")[-1]}.html'
            ),
            "w",
        ) as file:
            file.write(data)
    except IOError as error:
        print(f"{error}, while processing the link "
              f'"{link}" the data was not saved.')


def process_file_with_urls(path_to_file: str,):
    """The function creates a request session,
    processes the file with links line by line"""
    if not os.path.exists(path_to_file):
        raise FileExistsError("The file with URL doesn't exist")

    session = requests.Session()
    with open(path_to_file, "r") as file:
        for line in file:
            link = line.rstrip()
            data = url_downloader(session, link)
            if data:
                save_to_file(link, data.text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Name of file with HTTP URLs from current directory",
    )
    args = parser.parse_args()

    if args.file:
        path_to_file_with_url = os.path.join(WORK_DIRECTORY, args.file)
        process_file_with_urls(path_to_file_with_url)
