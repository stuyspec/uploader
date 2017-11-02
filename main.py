from __future__ import print_function
import httplib2
import os
import io
import re

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
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
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# TODO: make Issue for terminal calculating columns wrong. see https://bugs.python.org/issue17337 and its attached S.O. post

def readArticle(text):
    metadata = text.split('\n', 6)
    title = metadata[0] # gets first line of text
    if 'Title: ' in title:
        title = title[title.find('Title: ') + len('Title: '):]
    title = raw_input('title: ({0})'.format(title[:-1])) or title

    byline = next((line for line in metadata if line.find('By') >= 0))
    print(byline)
    if 'By:' in byline:
        byline = byline[len('By:'):].strip()
    else:
        byline = byline[len('By'):].strip()

    # splits string into words and punctuation
    byline = re.findall(r"[\w']+|[.,!?;]", byline)
    print(byline)
    contributors = []
    cutoff = 0
    for i in range(0, len(byline)):
        if byline[i] in ',&and':
            contributors.append(' '.join(byline[cutoff:i]))
            cutoff = i + 1
    contributors.append(' '.join(byline[cutoff:])) # clean up last one
    contributors = filter(None, contributors) # removes empty strings
    hi = raw_input("%s" % contributors)


def getFoldersInFile(files, parentFolderId):
    folders = {}
    # find first file in files with name 'SBC'

    for file in files:
        # check if parent folder is SBC and file type is folder
        if file.get('parents', [None])[0] == parentFolderId and file.get('mimeType') == 'application/vnd.google-apps.folder':
            folders[file['id']] = file['name']
    return folders

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http)

    # Gets all folder names under SBC
    page_token = None
    response = drive_service.files().list(q="(mimeType='application/vnd.google-apps.folder' or mimeType='application/vnd.google-apps.document') and not trashed",
                                          spaces='drive',
                                          fields='nextPageToken, files(id, name, parents, mimeType)',
                                          pageToken=page_token).execute()
    files = response.get('files', []) # if no key 'files', defaults to []
    SBC = next((file for file in files if file['name'] == 'SBC'), None)
    folders = getFoldersInFile(files, SBC['id'])
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.document' and file.get('parents', [None])[0] in folders:

            # find sectionName by getting folder with parentId
            sectionName = folders[file.get('parents', [None])[0]].upper()

            # create new download request
            request = drive_service.files().export_media(fileId=file['id'],
                                                         mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(Back.BLACK + Fore.WHITE + sectionName, end='')
                print(Back.RESET + Fore.BLUE + ' ' + file['name'] + Fore.RESET, end=' ')
                print('%d%%' % int(status.progress() * 100))

            readArticle(fh.getvalue())
    page_token = response.get('nextPageToken', None)
    if page_token is None:
        return

if __name__ == '__main__':
    main()