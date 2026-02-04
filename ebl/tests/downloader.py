from pymongo_inmemory.context import Context
from pymongo_inmemory.downloader import download


if __name__ == "__main__":
    download(Context())
