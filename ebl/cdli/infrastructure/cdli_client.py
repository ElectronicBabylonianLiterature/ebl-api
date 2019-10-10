import requests


def get_photo_url(cdli_number):
    url = f'https://cdli.ucla.edu/dl/photo/{cdli_number}.jpg'
    response = requests.head(url)
    return url if response.ok else None
