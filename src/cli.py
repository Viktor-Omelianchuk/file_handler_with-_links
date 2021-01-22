"""Module for parsing CLI args"""
import argparse


def parse_arguments():
    """
    Parse CLI args
    :return: (argparse.Namespace) List of arguments value
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--link",
        type=str,
        help="URL link to Wikipedia page",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Name of directory where file will be save",
    )
    parser.add_argument(
        "-n",
        "--number-of-links",
        type=int,
        help="The number of url links that will be queued for processing",
    )
    parser.add_argument(
        "-mw", "--max-workers", type=int, help="The humber of work threads"
    )
    parser.add_argument(
        "-ll",
        "--logging-level",
        type=str,
        default="INFO",
        help="level for logging module",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="../etc/config.ini",
        help="config file for config parser",
    )

    return parser.parse_args()
