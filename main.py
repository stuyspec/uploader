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

try:
    import argparse
    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--read-article', help='reads article in file')
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


def get_title(line):
    if 'Title: ' in line:
        line = line[line.find('Title: ') + len('Title: '):]
    line = line.strip()
    return raw_input(
        (Fore.GREEN + Style.BRIGHT + 'title: ' + Style.RESET_ALL +
         '({}) ').format(line)) or line  # if no user input, defaults to line


def get_contributors(byline):
    byline = re.sub(r"By:?", '', byline).strip()
    byline = re.findall(r"[\w']+|[.,!-?;]", byline)
    contributors = []
    cutoff = 0
    """Looks through tokens from left to right until a separator is reached,
    then joins the previous tokens into a name. 
    """
    for i in range(0, len(byline)):
        if byline[i] in ',&' or byline[i] == 'and':
            name = clean_name(' '.join(byline[cutoff:i]))
            contributors.append(name)
            cutoff = i + 1
    contributors.append(clean_name(' '.join(
        byline[cutoff:])))  # add last contributor
    contributors = filter(None, contributors)  # removes empty strings
    byline = raw_input(
        (Fore.GREEN + Style.BRIGHT +
         'contributors : ' + Style.RESET_ALL + '({0}) ').format(
             ', '.join(contributors))) or byline  # confirm contributors
    return contributors


def get_summary(line):
    line = re.sub(r"(?i)Focus Sentence:?", '', line).strip()
    return raw_input((Fore.GREEN + Style.BRIGHT + 'summary/focus: ' +
                      Style.RESET_ALL + '({0}) ').format(line)).strip() or line


def manual_article_read(content, message):
    print(Back.RED + Fore.WHITE + Style.BRIGHT + message \
          +' You have entered manual article-reading mode for headers. ' \
          + 'Input "m" to extend the article, input "f" to show the whole ' \
          + 'article, or press ENTER to continue.' + Style.RESET_ALL + Fore.RED)
    content = content.split('\n')
    lineNum = 0
    while lineNum < len(content):
        print(*content[lineNum:lineNum + 5], sep='\n')
        lineNum += 5
        showMore = raw_input()
        if showMore == 'f':
            print(*content[lineNum:], sep='\n')
        elif showMore != 'm':
            break


def post_article(content):
    input = content.split('\n')
    input = [line.strip() for line in input]

    post_data = {}

    post_data['title'] = get_title(input[0])

    byline = next((line for line in input
                   if line.find('By') >= 0), None)  # defaults to None
    if not byline:
        manual_article_read(content, 'No byline found.')
        byline = raw_input(Fore.GREEN + Style.BRIGHT \
                                 + 'enter contributors separated by ", ": ' \
                                 + Style.RESET_ALL)
    post_data['contributors'] = get_contributors(byline)

    summary = next((line for line in input
                    if 'focus sentence:' in line.lower()), '')
    if not summary:
        manual_article_read(content, 'No focus sentence found.')
    post_data['summary'] = get_summary(summary)

    HEADER_LINE_PATTERN = re.compile(
        r'(?i)(outquote(\(s\))?s?:)|(focus sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|article:?'
    )
    headerEndIndex = len(input) - next(
        (index for index, value in enumerate(reversed(input))
         if HEADER_LINE_PATTERN.match(value)), -1)
    if headerEndIndex == -1:
        print(
            Back.RED + Fore.WHITE +
            'No focus sentence or outquote; content could not be isolated. Article skipped.'
            + Back.RESET + Fore.RED)
        return post_data['title']
    paragraphs = filter(None, input[headerEndIndex:])
    post_data['paragraphs'] = raw_input(
        (Fore.GREEN + Style.BRIGHT +
         'content: ' + Style.RESET_ALL + '({} ... {}) ').format(
             paragraphs[0], paragraphs[-1])).split('\n') or paragraphs

    r = requests.post("https://requestb.in/sky5ktsk", data=post_data)

    return True


def clean_name(name):
    name = name.replace(' - ', '-')
    # remove nickname formatting e.g. "By Ying Zi (Jessy) Mei"
    name = re.sub(r"\([\w\s-]*\)\s", '', name)
    return name


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
    folders = getFoldersInFile(files, SBC['id'])

    unprocessedFiles = []
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.document' and file.get(
                'parents', [None])[0] in folders:

            # find sectionName by getting folder with parentId
            sectionName = folders[file.get('parents', [None])[0]].upper()

            # create new download request
            request = drive_service.files().export_media(
                fileId=file['id'], mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(Fore.CYAN + Style.BRIGHT + sectionName, end='')
                print(
                    Fore.BLUE + ' ' + file['name'] + Style.RESET_ALL, end=' ')
                print('%d%%' % int(status.progress() * 100))

            content = fh.getvalue()

            if 'worldbeat' in file['name'].lower():
                print(Fore.RED + Style.BRIGHT + 'Worldbeat skipped.' +
                      Style.RESET_ALL)
                continue

            if 'survey' in file['name'] or content.count(
                    '%') > 10:  # possibly a survey
                surveyConfirmation = ''
                isSurvey = False
                while surveyConfirmation == '':
                    surveyConfirmation = raw_input((
                        Fore.RED + Style.BRIGHT +
                        'Is this article, with {} counts of "%", a survey? (y/n) '
                        + Style.RESET_ALL).format(content.count('%')))
                    if surveyConfirmation == 'y':
                        print(Fore.RED + Style.BRIGHT + 'Survey skipped.')
                        unprocessedFiles.append(file['name'])
                        isSurvey = True
                        break
                    elif surveyConfirmation == 'n':
                        break
                if isSurvey:
                    print('\n')
                    continue  # continue to next file

            status = post_article(fh.getvalue())
            if type(status) is str:  # readArticle failed, returned filename
                unprocessedFiles.append(file['name'])
            print('\n')

    if len(unprocessedFiles) > 0:
        print(Back.RED + Fore.WHITE + 'The title of unprocessed files: ' +
              Back.RESET + Fore.RED)
        print(*unprocessedFiles, sep='\n')
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return


def getFoldersInFile(files, parentFolderId):
    folders = {}
    for file in files:
        # check if parent folder is SBC and file type is folder
        if file.get('parents', [None])[0] == parentFolderId and file.get(
                'mimeType') == 'application/vnd.google-apps.folder':
            folders[file['id']] = file['name']
    return folders


if __name__ == '__main__':
    if args.read_article:
        with open(args.read_article) as file:
            post_article(file.read())
    else:
        main()
