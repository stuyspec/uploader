from promise import Promise
from colorama import Fore, Back, Style
from slugify import slugify

import requests
import constants

media = []

def init():
    """Initiates globals with API data"""
    global media
    media = requests.get(constants.API_MEDIA_ENDPOINT).json()