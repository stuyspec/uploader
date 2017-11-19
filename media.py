from promise import Promise
from colorama import Fore, Back, Style
from slugify import slugify

import requests
import constants
import drive, users

media = []


def init():
    """Initiates globals with API data"""
    print('[0%] Loading media.\r'),  # comma lets next print overwrite.
    global media
    media = requests.get(constants.API_MEDIA_ENDPOINT).json()
    print('[100%] Loaded media.')


def post_media(article_id, medias):
    """Takes array of objects with artist_name, file, title, caption."""
    for media in medias:
        for field in ['artist_name', 'file', 'title', 'caption']:
            if field not in media:
                raise ValueError('Media object has no attribute {}.'
                                 .format(field))
        filename = drive.download_file(media['file'])
        drive.post_media_file(filename, {
            'article_id': article_id,
            'user_id': users.create_artist()
        })
        #imageName = drive.download_file(drive.get_file