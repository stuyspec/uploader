from promise import Promise
from colorama import Fore, Back, Style
from slugify import slugify

import requests
import constants

media = []

def init():
    """Initiates globals with API data"""
    print('[0%] Loading media.\r'),  # comma lets next print overwrite.
    global media
    media = requests.get(constants.API_MEDIA_ENDPOINT).json()
    print('[100%] Loaded media.')
