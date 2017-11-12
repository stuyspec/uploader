#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import tools
from promise import Promise
from termcolor import cprint
from pyfiglet import figlet_format
import httplib2
import io, re

from credentials import get_credentials
import constants, users, authorships, articles, sections

args = None
try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--local', help='post data to a specified port')
    args = parser.parse_args()
except ImportError:
    flags = None

from colorama import Fore, Back, Style
import colorama

# todo: text/html has hope. special styles are stored within spans in p's.


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    print('\n')
    print(figlet_format('SPEC CLI', font='slant'))

    page_token = None
    response = drive_service.files().list(
        q= "(mimeType='application/vnd.google-apps.folder'"
        + " or mimeType='application/vnd.google-apps.document')"
        + " and not trashed",
        spaces='drive',
        fields='nextPageToken, files(id, name, parents, mimeType)',
        pageToken=page_token).execute()
    files = response.get('files', [])
    Issue1 = next((
        f for f in files if f['name'] == 'Issue 1'
    ), None)
    SBC = next(
        (f for f in files
         if (f['mimeType'] == 'application/vnd.google-apps.folder' and
             f['name'] == 'SBC' and
             f.get('parents', [None])[0] == Issue1['id'])),
        None
    )
    if not SBC:
        print("No SBC folder found.")
        return
    SBC_folders = get_folders_in_file(files, SBC['id'])
    SBC_folders[SBC['id']] = SBC['name']

    volume = 107 #int(raw_input('Volume (number): '))
    issue = 1 #int(raw_input('Issue: '))

    unprocessed_file_names = []
    for file in files:
        if (file['mimeType'] == 'application/vnd.google-apps.document' and
                file.get('parents', [None])[0] in SBC_folders):
            print('\n')

            file_unwanted = None
            for unwanted_keyword in ['worldbeat', 'survey']:
                if unwanted_keyword in file['name'].lower():
                    file_unwanted = file
                    print(Fore.RED + Style.BRIGHT + unwanted_keyword.upper()
                          + ' skipped.' + Style.RESET_ALL)
            if file_unwanted:
                continue

            if re.match(r'(?i)staff\s?ed', file['name']):
                section_name = "Staff Editorials"
            else:
                section_name = SBC_folders[file.get('parents', [None])[0]]
            section_id = sections.get_section_name_by_id(section_name)

            request = drive_service.files().export_media(
                fileId=file['id'], mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(Fore.CYAN + Style.BRIGHT + section_name.upper()
                      + Fore.BLUE + ' ' + file['name'] + Style.RESET_ALL,
                      end=' ')
                print('%d%%' % int(status.progress() * 100))

            content = fh.getvalue()
            
            if articles.file_article_exists(content):
                print(Fore.RED + Style.BRIGHT + '{} already exists. TODO: update'
                        .format(file['name'].encode("utf-8")) + Style.RESET_ALL)
                continue

            if content.count('%') > 10:  # possibly a survey
                survey_confirmation = ''
                is_survey = False
                while survey_confirmation == '':
                    survey_confirmation = raw_input((
                        Fore.RED + Style.BRIGHT +
                        'Is this article, with {} counts of "%", a survey? (y/n) '
                        + Style.RESET_ALL).format(content.count('%')))
                    if survey_confirmation == 'y':
                        print(Fore.RED + Style.BRIGHT + 'Survey skipped.')
                        unprocessed_file_names.append(file['name'])
                        is_survey = True
                        break
                    elif survey_confirmation == 'n':
                        break
                if is_survey:
                    continue  # continue to next file

            if re.match(r'(?i)staff\s?ed', file['name']):
                article_data = articles.read_staff_ed(fh.getvalue())
            else:
                article_data = articles.read_article(fh.getvalue())

            section_id = sections.choose_subsection(section_id) or section_id
            if type(article_data) is str:
                # read_article failed and returned file title
                unprocessed_file_names.append(file['name'])
                continue

            article_attributes = ['title', 'content', 'summary', 'content']
            article_post_data = {
                key: value for key, value in article_data.items()
                               if key in article_attributes
            }
            for attr in ('volume', 'issue', 'section_id'):
                article_post_data[attr] = int(locals()[attr])  # adds specified local variables

            article_promise = Promise(
                lambda resolve, reject: resolve(articles.post_article(article_post_data))
            )\
                .then(lambda article_id:
                      users.post_contributors(article_id,
                                              article_data.get(
                                                  'contributors',
                                                  []
                                              )))\
                .then(lambda authorship_data:
                      authorships.post_authorships(authorship_data))\
                .then(lambda article_id:
                      print(Fore.GREEN + Style.BRIGHT
                            + 'Successfully wrote Article {}: {}.'
                                .format(article_id, article_post_data['title'])
                            + Style.RESET_ALL))
    if len(unprocessed_file_names) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessed_file_names, sep='\n')
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return


# NEEDS A BACK FUNCTION TODO
def get_folders_in_file(files, parent_folder_id):
    folders = {}
    for file in files:
        # check if parent folder is SBC and file type is folder
        if file.get('parents', [None])[0] == parent_folder_id and file.get(
                'mimeType') == 'application/vnd.google-apps.folder':
            folders[file['id']] = file['name']
    return folders


# DO NOT CHANGE THE ORDER OF THESE INIT'S
if __name__ == '__main__':
    colorama.init()
    if args.local is not None:
        constants.init('localhost:{}'.format(args.local))
    else:
        constants.init('not-deployed.yet')
    sections.init()
    articles.init()
    users.init()
    main()
