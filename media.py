from colorama import Fore, Back, Style

import requests
import constants
import drive, users, main, config, utils

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
        for field in [
                'artist_name', 'file', 'title', 'caption', 'is_featured',
                'media_type'
        ]:
            if field not in media:
                raise ValueError('Media object has no attribute {}.'
                                 .format(field))
        filename = download_file(media['file'])
        user_id = users.create_artist(media['artist_name'],
                                      media['media_type'])
        response = drive.post_media_file(filename, {
            'article_id': article_id,
            'user_id': user_id,
            'media_type': media['media_type'],
            'is_featured': media['is_featured'],
            'title': media['title'],
            'caption': media['caption']
        })
        main.updateHeaders(response)