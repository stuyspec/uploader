#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from oauth2client import tools
from promise import Promise
import io, re, os, requests
import webbrowser
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import constants, users, authorships, articles, sections, outquotes, media, drive

try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--local', help='post data to a specified port')
    parser.add_argument('--w', help='open windows on Drive load')
    flags = parser.parse_args()
except ImportError:
    flags = None

from colorama import Fore, Back, Style
import colorama


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Spec-Uploader CLI'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def find_matching_folder_in(parent_id, files, name_pattern):
    parent_file = next((f for f in files if f['id'] == parent_id), None)
    if not parent_file:
        raise ValueError('No parent {} found.'.format(parent_id))
    if parent_file['mimeType'] != 'application/vnd.google-apps.folder':
        raise ValueError('File {} is not a folder.'
                         .format(parent_file['name']))
    return next((
        f for f in files if (parent_id in f.get('parents', [None])
                             and re.match(name_pattern, f['name']))
    ), None)


def main():
    Volume = drive.get_file(r"Volume 108", 'folder')
    Issue = drive.get_file(r"Issue\s?1", 'folder', Volume['id'])
    SBC = drive.get_file(r"SBC", 'folder', Issue['id'])

    art_folder = drive.get_file(r"(?i)art", 'folder', Issue['id'])
    photo_folder = drive.get_file(r"(?i)(photo\s?color)",
                                  'folder',
                                  Issue['id'])
    if not photo_folder:
        photo_folder = drive.get_file(r"(?i)(photo\s?b&?w)",
                                      'folder',
                                      Issue['id'])
    media_files = drive.get_children([art_folder['id'],
                                      photo_folder['id']],
                                     'image')

    PDF = drive.get_file("(?i)Issue\s?\d(\.pdf)$",
                         'application/pdf',
                         Issue['id'])

    webbrowser.open('https://drive.google.com/file/d/{}/view'
                    .format(PDF['id']),
                    new=2)
    webbrowser.open('https://drive.google.com/drive/folders/' + photo_folder['id'],
                    new=2)
    webbrowser.open('https://drive.google.com/drive/folders/' + art_folder['id'],
                    new=2)
    volume = 107
    issue = 1
    unprocessed_file_names = []
    
    issue_sections = {}
    for section in drive.get_children(SBC['id'], 'folder'):
        issue_sections[section['name']] = section
    ordered_issue_sections = [
        issue_sections[section_name] for section_name in [
            'News', 'Features', 'Opinions', 'A&E', 'Humor', 'Sports'
        ]
    ]

    for section in ordered_issue_sections:

        section_id = sections.get_section_id_by_name(section['name'])
        section_articles = drive.get_children(section['id'], 'document')

        if section['name'] == 'Opinions':
            section_articles.append(drive.get_file(r'(?i)staff\s?ed',
                                                   'document',
                                                   SBC['id']))

        for file in section_articles:
            print('\n')

            file_unwanted = re.search(r"(?i)worldbeat|survey",
                                          file['name'])
            if file_unwanted:
                print(Fore.RED + Style.BRIGHT + file_unwanted.group().upper()
                      + ' skipped.' + Style.RESET_ALL)
                continue

            print(Fore.CYAN + Style.BRIGHT + section['name'].upper()
                  + Fore.BLUE + ' ' + file['name'] + Style.RESET_ALL, end=' ')
            article_text = drive.download_document(file)

            if articles.file_article_exists(article_text):
                print(Fore.RED + Style.BRIGHT + file['name'].encode("utf-8")
                      + ' already exists.' + Style.RESET_ALL)
                continue

            if re.search(r'(?i)staff\s?ed', file['name']):
                article_data = articles.read_staff_ed(article_text)
            else:
                article_data = articles.read_article(article_text)

            media_data = []
            if raw_input(Fore.GREEN + Style.BRIGHT + 'upload media? (y/n): '
                                 + Style.RESET_ALL) == 'y':
                media_data = choose_media(media_files,
                                          art_folder_id=art_folder['id'],
                                          photo_folder_id=photo_folder['id'])
            if type(article_data) is str:
                # read_article failed and returned file title
                unprocessed_file_names.append(file['name'])
                continue

            if section_name == 'Humor':
                if issue == 4:
                    article_section_id = get_section_id_by_name('Spooktator')
                elif issue == 12:
                    article_section_id = get_section_id_by_name('Disrespectator')
            else:
                article_section_id = sections.choose_subsection(section_id) or section_id

            article_attributes = ['title', 'content', 'summary', 'content']
            article_post_data = {
                key: value for key, value in article_data.items()
                               if key in article_attributes
            }
            for attr in ('volume', 'issue'):
                article_post_data[attr] = int(locals()[attr])  # adds specified local variables
            article_post_data['section_id'] = article_section_id

            article_promise = Promise(
                lambda resolve, reject:
                    resolve(articles.post_article(article_post_data))
            )\
                .then(lambda article_id:
                      users.post_contributors(article_id,
                                              article_data['contributors']))\
                .then(lambda authorship_data:
                      authorships.post_authorships(authorship_data))\
                .then(lambda article_id:
                      outquotes.post_outquotes(article_id,
                                               article_data['outquotes']))\
                .then(lambda article_id:
                      media.post_media(article_id, media_data))\
                .then(lambda article_id:
                      print(Fore.GREEN + Style.BRIGHT
                            + '\nSuccessfully wrote Article {}: {}.'
                                .format(article_id, article_post_data['title'])
                            + Style.RESET_ALL))
    if len(unprocessed_file_names) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_file_names, sep='\n')


def choose_media(media_files, art_folder_id, photo_folder_id):
    output = []
    while 1:
        media_data = {}

        while 1:
            filename = raw_input(Fore.GREEN + Style.BRIGHT
                                 + '-> filename (press ENTER to exit): '
                                 + Style.RESET_ALL).strip()
            if filename == '':
                return output
            if filename[0] == '*':
                media_data['is_featured'] = True
                filename = filename[1:]
            else:
                media_data['is_featured'] = False
            media = next((media_file for media_file in media_files
                          if media_file['name'] == filename), None)
            if media is not None:
                media_data['file'] = media
                if any(p == photo_folder_id for p in media.get('parents', [])):
                    media_data['media_type'] = 'photo'
                elif any(p == art_folder_id for p in media.get('parents', [])):
                    media_data['media_type'] = 'illustration'
                else:
                    raise ValueError('The parents of {} are not the folders '
                                     + 'Art ({}) or Photo ({}).'
                                     .format(filename, art_folder_id,
                                             photo_folder_id))
                break
            print('No media matches filename {}.'.format(filename))

        for field in ['title', 'caption']:
            field_input = raw_input(Fore.GREEN + Style.BRIGHT + '-> '
                                    + field + ': ' + Style.RESET_ALL)\
                .strip()
            media_data[field] = field_input

        while 1:
            field_input = raw_input(Fore.GREEN + Style.BRIGHT + '-> artist name: '
                                    + Style.RESET_ALL)\
                .strip()
            if field_input == '':
                print('\tartist name cannot be empty. check the Issue PDF for credits.')
            else:
                media_data['artist_name'] = field_input
                break


        output.append(media_data)


        # imageName = drive.download_file(drive.get_file


# DO NOT CHANGE THE ORDER OF THESE INIT'S
if __name__ == '__main__':
    creds = get_credentials()
    colorama.init()
    if flags.local is not None:
        constants.init('localhost:{}'.format(flags.local))
    else:
        constants.init()
    drive.init(creds)
    sections.init()
    articles.init()
    users.init()
    print('\n')
    main()
