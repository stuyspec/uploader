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
    parser.add_argument('--window', dest='window', action='store_true', help='open windows on Drive load')
    parser.set_defaults(window=False)

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
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    # volume_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL).strip())
    # issue_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL.strip()))
    process_issue(108, 2)


def process_issue(volume, issue):
    volume_folder = drive.get_file(r"Volume {}".format(volume), 'folder')
    issue_folder = drive.get_file(r"Issue\s?{}".format(issue), 'folder', volume_folder['id'])
    sbc_folder = drive.get_file(r"SBC", 'folder', issue_folder['id'])
    newspaper_pdf = drive.get_file("(?i)Issue\s?\d(\.pdf)$", 'application/pdf',
                         issue_folder['id'])
    art_folder = drive.get_file(r"(?i)art", 'folder', issue_folder['id'])
    photo_folder = drive.get_file(r"(?i)(photo\s?color)", 'folder',
                                  issue_folder['id'])
    if not photo_folder:
        photo_folder = drive.get_file(r"(?i)(photo\s?b&?w)", 'folder',
                                      Issue['id'])

    media_files = drive.get_children([art_folder['id'], photo_folder['id']],
                                     'image')

    if flags.window:
        webbrowser.open(
            'https://drive.google.com/file/d/{}/view'.format(newspaper_pdf['id']), new=2)
        webbrowser.open(
            'https://drive.google.com/drive/folders/' + photo_folder['id'],
            new=2)
        webbrowser.open(
            'https://drive.google.com/drive/folders/' + art_folder['id'],
            new=2)

    unprocessed_file_names = []

    issue_sections = {}
    for section in drive.get_children(sbc_folder['id'], 'folder'):
        issue_sections[section['name']] = section
    ordered_issue_sections = [
        issue_sections[section_name]
        for section_name in
        ['News', 'Features', 'Opinions', 'A&E', 'Humor', 'Sports']
    ]

    for section in ordered_issue_sections:

        section_id = sections.get_section_id_by_name(section['name'])
        section_articles = drive.get_children(section['id'], 'document')

        if section['name'] == 'Opinions':
            section_articles.append(
                drive.get_file(r'(?i)staff\s?ed', 'document', sbc_folder['id']))

        f = 0
        while f < len(section_articles):  # indexed for rollbacking
            file = section_articles[f]
            print('\n')

            file_unwanted = re.search(r"(?i)worldbeat|survey|newsbeat", file['name'])
            if file_unwanted:
                print(Fore.RED + Style.BRIGHT + file_unwanted.group().upper() +
                      ' skipped.' + Style.RESET_ALL)
                f = f + 1
                continue

            print(
                Fore.CYAN + Style.BRIGHT + section['name'].upper() +
                Fore.BLUE + ' ' + file['name'] + Style.RESET_ALL,
                end=' ')
            article_text = drive.download_document(file)

            if articles.file_article_exists(article_text):
                print(Fore.RED + Style.BRIGHT + file['name'].encode("utf-8")
                      + ' already exists.' + Style.RESET_ALL)
                f = f + 1
                continue

            if re.search(r'(?i)staff\s?ed', file['name']):
                article_data = articles.read_staff_ed(article_text)
            else:
                article_data = articles.read_article(article_text)

            media_data = []
            media_confirmation = raw_input(Fore.GREEN + Style.BRIGHT + 'upload media? (y/n): ' +
                         Style.RESET_ALL)
            while media_confirmation != 'y' and media_confirmation != 'n':
                media_confirmation = raw_input(Fore.GREEN + Style.BRIGHT + 'upload media? (y/n): ' +
                         Style.RESET_ALL)
            if media_confirmation == 'y':
                media_data = choose_media(
                    media_files,
                    art_folder_id=art_folder['id'],
                    photo_folder_id=photo_folder['id'])

            if section['name'] == 'Humor':
                if issue == 4:
                    article_section_id = sections.get_section_id_by_name('Spooktator')
                elif issue == 12:
                    article_section_id = sections.get_section_id_by_name(
                        'Disrespectator')
            elif re.search(r'(?i)staff\s?ed', file['name']):
                article_section_id = sections.get_section_id_by_name('Staff Editorials')
            else:
                article_section_id = sections.choose_subsection(
                    section_id) or section_id

            article_attributes = ['title', 'content', 'summary', 'content']
            article_post_data = {
                key: value
                for key, value in article_data.items()
                if key in article_attributes
            }
            for attr in ('volume', 'issue'):
                article_post_data[attr] = int(
                    locals()[attr])  # adds specified local variables
            article_post_data['section_id'] = article_section_id

            article_data['id'] = articles.post_article(article_post_data)

            rollbacked = False

            def rollback(res):
                try:
                    print(Fore.RED + Style.BRIGHT + '\nCaught error: {}.'.format(res))
                    destroy_response = requests.delete(constants.API_ARTICLES_ENDPOINT + '/{}'.format(article_data['id']))
                    destroy_response.raise_for_status()
                    return True
                except Exception as e:
                    print('Rollback failed with {}. Article {} remains evilly.'.format(e, article_data['id']))

            promise = Promise(lambda resolve, reject: resolve(users.post_contributors(article_data)))\
                .then(lambda authorship_data:
                      authorships.post_authorships(authorship_data))\
                .then(lambda res: outquotes.post_outquotes(article_data))\
                .then(lambda article_id:
                      media.post_media(article_id, media_data))\
                .then(lambda article_id: print(
                      Fore.GREEN + Style.BRIGHT
                            + '\nSuccessfully wrote Article #{}: {}.'
                                .format(article_data['id'], article_post_data['title'])
                            + Style.RESET_ALL))\
                .catch(lambda res: rollback(res))

            result = promise.get()
            if result is not None and result is True:
                f = f - 1
                print('Rollback completed. Re-prompting article.' + Style.RESET_ALL)

            f = f + 1
            
                
    if len(unprocessed_file_names) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_file_names, sep='\n')


def choose_media(media_files, art_folder_id, photo_folder_id):
    output = []
    while 1:
        media_data = {}

        while 1:
            filename = raw_input(Fore.GREEN + Style.BRIGHT +
                                 '-> filename (press ENTER to exit): ' +
                                 Style.RESET_ALL).strip()
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
                    raise ValueError('The parents of {} are not the folders ' +
                                     'Art ({}) or Photo ({}).'
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
                print(
                    '\tartist name cannot be empty. check the Issue PDF for credits.'
                )
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
