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


def post_media(article_id, media_files):
    output = []
    while 1:
        media_data = {}
        while 1:
            filename = raw_input(Fore.GREEN + Style.BRIGHT + 'filename: '
                                 + Style.RESET_ALL).strip()
            if filename[0] == '*':
                media_data['is_featured'] = True
                filename = filename[1:]
            media = next((media_file for media_file in media_files
                          if media_file['name'] == filename), None)
            if media is not None:
                break
            print('No ')
        media_data[]
        #imageName = drive.download_file(drive.get_file