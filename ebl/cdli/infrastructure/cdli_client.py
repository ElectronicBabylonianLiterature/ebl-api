import logging

import requests
from requests import Timeout

BASE_URL = "https://cdli.ucla.edu/dl"
TIMEOUT_SECONDS = 5


def get_photo_url(cdli_number):
    return _get_url(f"{BASE_URL}/photo/{cdli_number}.jpg")


def get_line_art_url(cdli_number):
    return _get_url(f"{BASE_URL}/lineart/{cdli_number}_l.jpg")


def get_detail_line_art_url(cdli_number):
    return _get_url(f"{BASE_URL}/lineart/{cdli_number}_ld.jpg")


def _get_url(url):
    try:
        response = requests.head(url, timeout=TIMEOUT_SECONDS)
        return url if response.ok else None
    except Timeout:
        _log_timeout(url)
        return None


def _log_timeout(url):
    logger = logging.getLogger("cdli_client")
    logger.warning("Connection to %s timed out.", url)
