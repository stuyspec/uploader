from promise import Promise
from colorama import Fore, Back, Style
from slugify import slugify

import requests
import constants
import drive

media = []


def init():
    """Initiates globals with API data"""
    print('[0%] Loading media.\r'),  # comma lets next print overwrite.
    global media
    media = requests.get(constants.API_MEDIA_ENDPOINT).json()
    print('[100%] Loaded media.')


def choose_media(media_files):
    while True:
        filename = raw_input(Fore.GREEN + Style.BRIGHT + 'filename: '
                             + Style.RESET_ALL)
        #imageName = drive.download_file(drive.get_file