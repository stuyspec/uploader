from colorama import Fore, Back, Style

import requests
import constants
import drive, users, main, config

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
        filename = drive.download_file(media['file'])
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


def choose_media(media_files):
    images = []
    media_confirmation = None
    while media_confirmation != 'y' and media_confirmation != 'n':
        media_confirmation = raw_input(
            Fore.GREEN + Style.BRIGHT + 'upload media? (y/n): ' +
            Style.RESET_ALL)
    if media_confirmation == 'n':
        return images

    while True:
        image = {
            'is_featured': False,
            'media_type': 'illustration',
        }
        while True:
            filename = raw_input(Fore.GREEN + Style.BRIGHT +
                                 '-> filename (press ENTER to exit): ' +
                                 Style.RESET_ALL).strip()
            if filename == '':
                return images
            if filename[0] == '*':
                image['is_featured'] = True
                filename = filename[1:]
            try:
                target_file = next((
                    medium for medium in media_files
                        if medium['name'] == filename
                ))
                image['file'] = target_file
                if any(parent_id == config.photo_folder_id
                       for parent_id in target_file.get('parents', [])):
                    image['media_type'] = 'photo'
                break
            except StopIteration:
                print(Fore.RED + Style.BRIGHT
                      + 'No file matches {}.'.format(filename)
                      + Style.REST_ALL)

        for optional_field in ['title', 'caption']:
            field_input = raw_input(Fore.GREEN + Style.BRIGHT + '-> '
                                    + optional_field + ': ' + Style.RESET_ALL)\
                .strip()
            image[optional_field] = field_input

        while True:
            artist_name = raw_input(Fore.GREEN + Style.BRIGHT
                                    + '-> artist name: ' + Style.RESET_ALL)\
                .strip()
            if field_input == '':
                print(
                    '\tartist name cannot be empty. check the Issue PDF for credits.'
                )
            else:
                image['artist_name'] = field_input
                break

        images.append(image)