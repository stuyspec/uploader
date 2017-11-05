#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import httplib2
import os
import io
import re
import requests

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from article_read import read_article

try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--read-article', help='reads article in file')
    parser.add_argument('--local', help='post data to localhost:3000 (for testing purposes)')
    args = parser.parse_args()
except ImportError:
    flags = None

from colorama import init, Fore, Back, Style
init()

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Spec-Uploader CLI'
STUY_SPEC_API_URL = 'http://NOT_DEPLOYED_YET.com'

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
    print(
        "This utility will walk you through the uploading of all articles in the current Issue."
    )
    print("Press ^C at any time to quit.\n")
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    # Gets all folder names under SBC
    page_token = None
    response = drive_service.files().list(
        q=
        "(mimeType='application/vnd.google-apps.folder' or mimeType='application/vnd.google-apps.document') and not trashed",
        spaces='drive',
        fields='nextPageToken, files(id, name, parents, mimeType)',
        pageToken=page_token).execute()
    files = response.get('files', [])  # if no key 'files', defaults to []
    SBC = next((file for file in files if file['name'] == 'SBC'), None)
    folders = get_folders_in_file(files, SBC['id'])

    unprocessed_files = []
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.document' and file.get(
                'parents', [None])[0] in folders:

            # find section_name by getting folder with parentId
            section_name = folders[file.get('parents', [None])[0]].upper()
            # create new download request
            request = drive_service.files().export_media(
                fileId=file['id'], mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(Fore.CYAN + Style.BRIGHT + section_name, end='')
                print(
                    Fore.BLUE + ' ' + file['name'] + Style.RESET_ALL, end=' ')

                # spaces to override " loading..."
                print('%d%%' % int(status.progress() * 100))

            content = fh.getvalue()

            if 'worldbeat' in file['name'].lower():
                print(Fore.RED + Style.BRIGHT + 'Worldbeat skipped.' +
                      Style.RESET_ALL)
                continue

            if 'survey' in file['name'] or content.count(
                    '%') > 10:  # possibly a survey
                survey_confirmation = ''
                is_survey = False
                while survey_confirmation == '':
                    survey_confirmation = raw_input((
                        Fore.RED + Style.BRIGHT +
                        'Is this article, with {} counts of "%", a survey? (y/n) '
                        + Style.RESET_ALL).format(content.count('%')))
                    if survey_confirmation == 'y':
                        print(Fore.RED + Style.BRIGHT + 'Survey skipped.')
                        unprocessed_files.append(file['name'])
                        is_survey = True
                        break
                    elif survey_confirmation == 'n':
                        break
                if is_survey:
                    print('\n')
                    continue  # continue to next file

            post_data = read_article(fh.getvalue())
            if type(post_data) is str:  # readArticle failed, returned filename
                unprocessed_files.append(file['name'])
                continue
            r = requests.post(STUY_SPEC_API_URL, data=post_data)
            print('\n')

    if len(unprocessed_files) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_files, sep='\n')
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return


def get_folders_in_file(files, parent_folder_id):
    folders = {}
    for file in files:
        # check if parent folder is SBC and file type is folder
        if file.get('parents', [None])[0] == parent_folder_id and file.get(
                'mimeType') == 'application/vnd.google-apps.folder':
            folders[file['id']] = file['name']
    return folders


if __name__ == '__main__':
    if args.read_article:
        with open(args.read_article) as file:
            post_article(file.read())
    elif args.local:
        STUY_SPEC_API_URL = 'localhost:3000'
    else:
        main()
