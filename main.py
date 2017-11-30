#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from oauth2client import tools
from promise import Promise
import re, os, requests
import webbrowser
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import json

import constants, users, authorships, articles, sections, outquotes, media, drive, config

try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--local', help='post data to a specified port')
    parser.add_argument('--window', dest='window', action='store_true', help='open windows on Drive load')
    parser.set_defaults(window=False)
    parser.add_argument('-u', dest='u', action='store_true', help='use as utility')
    parser.set_defaults(u=False)
    parser.add_argument('-c', dest='c', action='store_true', help='read custom article in custom.in')
    parser.set_defaults(c=False)
    parser.add_argument('-nd', dest='nd', action='store_true', help='don\'t download drive info')
    parser.set_defaults(nd=False)

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
    the OAuth2 flow is completed to obtain the    credentials.

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
    config.sign_in()
    # volume_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL).strip())
    print(Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL + '108')
    # issue_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL.strip()))
    print(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL + '5')

    config.volume = 108
    config.issue = 5

    process_issue(108, 5)





def read_custom(filename):
    with open(filename, 'r') as f:
        text = filter(None, f.read().split('\n'))
        output = {
            'title': text[0],
            'summary': '',
            'outquotes': []
        }
        contributors = articles.get_contributors(text[1])
        content_start = 2
        try:
            output['summary'] = next((s for s in text if 'focus sentence:' in s.lower()))
            content_start = 3
        except StopIteration:
            print('no summary found')
        try:
            for s in text:
                if s.lower().find('outquote') == 0:
                    output['outquotes'].append(s)
                    content_start += 1
        except StopIteration:
            print('no outquotes found')
        output['content'] = '<p>' + '</p><p>'.join(text[content_start:]) + '</p>'
        output['contributors'] = contributors

        output['id'] = articles.post_article({
            'title': output['title'],
            'content': output['content'],
            'summary': output['summary'],
            'volume': 108,
            'issue': 5,
            'section_id': 11
        })

        article_promise = Promise(
            lambda resolve, reject: resolve(users.post_contributors(output))) \
            .then(lambda authorship_data:
                  authorships.post_authorships(authorship_data)) \
            .then(lambda res: outquotes.post_outquotes(output)) \
            .then(lambda article_id: print(
                Fore.GREEN + Style.BRIGHT
                + '\nSuccessfully wrote Article #{}: {}.'
                .format(output['id'], output['title'])
                + Style.RESET_ALL)) \
            .catch(lambda res: print(res))

def process_issue(volume, issue):
    volume_folder = drive.get_file(r"Volume {}".format(volume), 'folder')
    issue_folder = drive.get_file(r"Issue\s?{}".format(issue), 'folder', volume_folder['id'])
    # sbc_folder = drive.get_file(r"SBC", 'folder', issue_folder['id'])
    sbc_folder = drive.get_file(r"Tuesday Attack", 'folder')
    newspaper_pdf = drive.get_file("(?i)Issue\s?\d{1,2}(\.pdf)$", 'application/pdf',
                         issue_folder['id'])


    # art_folder = drive.get_file(r"(?i)art", 'folder', issue_folder['id'])
    # try:
    #     photo_folder = drive.get_file(r"(?i)(photo\s?color)", 'folder',
    #                                   issue_folder['id'])
    # except StopIteration:
    #     photo_folder = drive.get_file(r"(?i)(photo\s?b&?w)", 'folder',
    #                                   issue_folder['id'])

    # media_files = drive.get_children([art_folder['id'], photo_folder['id']],
    #                                  'image')
    what_happened = drive.get_file(r"What Happened On Tuesday", 'folder', issue_folder['id'])
    art_folder = drive.get_file(r"(?i)art", 'folder', issue_folder['id'])
    try:
        photo_folder = drive.get_file(r"(?i)(photo\s?color)", 'folder',
                                      what_happened['id'])
    except StopIteration:
        photo_folder = drive.get_file(r"(?i)(photo\s?b&?w)", 'folder',
                                      what_happened['id'])

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
        print(section['name'])
        issue_sections[section['name']] = section

    ordered_issue_sections = [
        issue_sections[section_name]
        for section_name in
        # ['News', 'Features', 'Opinions', 'A&E', 'Humor', 'Sports']
        ['News', 'Features', 'A&E', 'Opinions']
        if section_name in issue_sections
    ]

    for section in ordered_issue_sections:

        section_id = sections.get_section_id_by_name(section['name'])
        section_articles = drive.get_children(section['id'], 'document')

        if section['name'] == 'Opinions':
            try:
                section_articles.append(
                    drive.get_file(r'(?i)staff\s?ed', 'document', sbc_folder['id']))
            except StopIteration:
                print(Fore.RED + Style.BRIGHT + 'No staff-ed found in Volume {} Issue {}.'.format(volume, issue))

        f = 0
        while f < len(section_articles):  # indexed for rollbacking
            print('\n')
            drive_file = section_articles[f]
            try:
                process_article(drive_file, section['name'], volume, issue, art_folder['id'], photo_folder['id'], media_files)
            except ValueError as e:
                message = e.args[0]
                if message == 'SKIP':
                    f = f + 1
                    continue
                elif message == 'ROLLBACK':
                    print('Rollback completed. Re-prompting article.'
                          + Style.RESET_ALL)
                    continue
            f = f + 1

                
    if len(unprocessed_file_names) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_file_names, sep='\n')




def utility_init(locally=False):
    creds = get_credentials()
    colorama.init()
    if locally:
        constants.init('localhost:{}'.format(locally))
    else:
        constants.init()
    drive.utility_init(creds)
    users.init()



# DO NOT CHANGE THE ORDER OF THESE INIT'S
if __name__ == '__main__':
    # if flags.u is not None:
    #     utility_init()
    #     # f = drive.download_document(
    #     #     drive.get_file_by_id('1QeC3a-MSvl-JL5Dv7eImbV4yOZteyqC90zxHB-9dspc')
    #     # )
    #     # volume_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL).strip())
    #     # issue_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL.strip()))

    #     # process_photo_essay(f)
    #     # print(f)
    #     images = drive.get_media_in_folder('0B2DmTEvyEQvibGZtLVlFT01IbEE')
    #     for i in images:
    #         print(i['name'], i ['parents'])

    # if flags.c is True:
    #     utility_init()
    #     read_custom('custom.in')

    creds = get_credentials()
    colorama.init()
    if flags.local is not None:
        constants.init('localhost:{}'.format(flags.local))
    else:
        constants.init()
    if flags.nd is False: # no drive
        drive.init(creds)
        f = open('files.in', 'w')
        f.write(str(drive.files))
        f.close()
        raise ValueError('stop it')
    sections.init()
    articles.init()
    users.init()
    print('\n')
    main()
