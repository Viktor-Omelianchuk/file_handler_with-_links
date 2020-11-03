"""Console script for link_handler."""
import argparse
import sys

CONSOLE_ARGUMENTS = None


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--link",
        type=str,
        required=True,
        help="Name of file with HTTP URLs from current directory",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Name of directory where file will be save"
    )
    parser.add_argument(
        "-n",
        "--number_of_links",
        type=int,
        help="The number of url links that will be queued for processing",
    )
    parser.add_argument(
        "-mw", "--max_worker", type=int, help="The humber of work threads"
    )
    parser.add_argument(
        '-ll',
        '--logging_level',
        type=int,
        default=20,
        help='level for logging module'
    )
    parser.add_argument(
        '-c',
        '--config',
        type=str,
        default='config.ini',
        help='config file for config parser'
    )
    global CONSOLE_ARGUMENTS
    CONSOLE_ARGUMENTS = parser.parse_args()
    return CONSOLE_ARGUMENTS


if __name__ == "__main__":
    sys.exit(parse_arguments())
