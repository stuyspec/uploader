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

from read_article import read_article
from credentials import get_credentials

args = None
try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--read-article', help='reads article in file')
    parser.add_argument('--local', help='post data to a specified port (for testing purposes)')
    parser.add_argument('-s', action='store_true')

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

    sections_response = requests.get(STUY_SPEC_API_URL + '/sections')
    sections = json.loads(sections_response.text)

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

            article_attributes = [ 'title', 'content', 'summary', 'content' ]
            article_post_data = {
                key: value for key, value in article_data.items()
                               if key in article_attributes
            }
            for attr in ('volume', 'issue', 'section_id'):
                article_post_data[attr] = int(locals()[attr])  # adds specified local variables

            promise = Promise(
                lambda resolve, reject: post_article(resolve, reject,
                                                     article_post_data)
            ).then(lambda article_id: post_contributors(article_id,
                                                        article_data.
                                                            .get('contributors',
                                                                 [])
                                                        ))
            P
            article_id = json.loads(article_request.text).get('id', -1)

            #print(article_id)
            print('\n')

    if len(unprocessed_files) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_files, sep='\n')
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return

def post_article(resolve, reject, data):
    article_response = requests.post(STUY_SPEC_API_URL + '/articles',
                                    data=json.dumps(data),
                                    headers={'Content-Type': 'application/json'})
    article_response_json = article_response.json()
    try:
        article_response.raise_for_status()
        resolve(article_response_json['text'].get('id', -1))
    except requests.HTTPError as e:
        reject('HTTP ERROR %d' % e.code)


def post_contributors(article_id, contributors):
    for c in contributors:
        c_name = c.split(' ')
        c_post_data = {
            'first_name': ' '.join(c_name[:-1])
            'last_name': c_name[-1]
        }
        c_request = requests.post(STUY_SPEC_API_URL + '/users',
                                  data=json.dumps(c_post_data),
                                  headers={'Content-Type': 'application/json'})
    contributors_response = requests.post(STUY_SPEC_API_URL + '/articles',
                                          data=json.dumps(data),
                                          headers={'Content-Type': 'application/json'})
    contributors_response_json = article_response.json()
    try:
        article_response.raise_for_status()
        resolve(article_response_json['text'].get('id', -1))
    except requests.HTTPError as e:
        reject('HTTP ERROR %d' % e.code)


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
            read_article(file.read())
    elif args.local:
        STUY_SPEC_API_URL = 'http://localhost:' + args.local
        main()
    else:
        main()
