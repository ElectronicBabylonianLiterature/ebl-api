import requests


BASE_URL = 'https://cdli.ucla.edu/dl'


def get_photo_url(cdli_number):
    url = f'{BASE_URL}/photo/{cdli_number}.jpg'
    response = requests.head(url)
    return url if response.ok else None


def get_line_art_url(cdli_number):
    url = f'{BASE_URL}/lineart/{cdli_number}_l.jpg'
    response = requests.head(url)
    return url if response.ok else None


def get_detail_line_art_url(cdli_number):
    url = f'{BASE_URL}/lineart/{cdli_number}_ld.jpg'
    response = requests.head(url)
    return url if response.ok else None
