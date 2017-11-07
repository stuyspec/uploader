#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import httplib2
import io
import requests
import json

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import tools
from promise import Promise

from articles import read_article
from credentials import get_credentials
import constants, backups, users, authorships

args = None
try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--local', help='post data to a specified port (for testing purposes)')
    parser.add_argument('-s', action='store_true', help='stop POSTing articles')
    args = parser.parse_args()
except ImportError:
    flags = None

from colorama import Fore, Back, Style
import colorama
colorama.init()

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Spec-Uploader CLI'


def main():
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

    volume = 107 #int(raw_input('Volume (number): '))
    issue = 1 #int(raw_input('Issue: '))

    sections_response = requests.get(constants.API_SECTIONS_ENDPOINT)
    sections = sections_response.json()

    unprocessed_files = []
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.document' and file.get(
                'parents', [None])[0] in folders:

            # find section_name by getting folder with parentId
            section_name = folders[file.get('parents', [None])[0]]
            section_id = next(
                (s for s in sections
                    if (s['name'].lower() == section_name.lower() or
                        section_name == 'A&E'
                        and s['name'] == "Arts & Entertainment")
                 )
            )['id']
            # create new download request
            request = drive_service.files().export_media(
                fileId=file['id'], mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(Fore.CYAN + Style.BRIGHT + section_name.upper(), end='')
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

            article_data = read_article(fh.getvalue())
            if type(article_data) is str or args.s:
                # read_article failed and returned file title or flag s, stop post.
                unprocessed_files.append(file['name'])
                continue

            article_attributes = ['title', 'content', 'summary', 'content']
            article_post_data = {
                key: value for key, value in article_data.items()
                               if key in article_attributes
            }
            for attr in ('volume', 'issue', 'section_id'):
                article_post_data[attr] = int(locals()[attr])  # adds specified local variables

            promise = Promise(
                lambda resolve, reject: resolve(post_article(article_post_data))
            )\
                .then(lambda article_id:
                      users.post_contributors(article_id,
                                              article_data.get(
                                                  'contributors',
                                                  []
                                              )))\
                .then(lambda authorship_data:
                      authorships.post_authorships(authorship_data))

            print(Fore.GREEN + Style.BRIGHT
                  + 'Successfully wrote {}.\n'.format(article_post_data['title'])
                  + Style.RESET_ALL)

    if len(unprocessed_files) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_files, sep='\n')
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return

def post_article(data):
    article_response = requests.post(constants.API_ARTICLES_ENDPOINT,
                                    data=json.dumps(data),
                                    headers={'Content-Type': 'application/json'})
    article_response.raise_for_status()
    return article_response.json().get('id', -1)


def post_authorships(contributor_data):
    article_id, contributor_ids = contributor_data
    authorship_post_data = [
        {'article_id': article_id, 'user_id': c_id} for c_id in contributor_ids
    ]
    authorships_response = requests.post(constants.API_AUTHORSHIPS_ENDPOINT,
                                         data=json.dumps(authorship_post_data),
                                         headers={
                                             'Content-Type': 'application/json'
                                         })
    return authorships_response.json()


def get_folders_in_file(files, parent_folder_id):
    folders = {}
    for file in files:
        # check if parent folder is SBC and file type is folder
        if file.get('parents', [None])[0] == parent_folder_id and file.get(
                'mimeType') == 'application/vnd.google-apps.folder':
            folders[file['id']] = file['name']
    return folders


if __name__ == '__main__':
    colorama.init()
    if args.local is not None:
        constants.init('localhost:{}'.format(args.local))
    else:
        constants.init('not-deployed.yet')
    backups.init()
    users.init()
    main()
