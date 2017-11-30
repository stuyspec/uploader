from __future__ import print_function
import httplib2
import os
import re
import json

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from colorama import Fore, Back, Style
import colorama
import ast

try:
    import argparse

    parser = argparse.ArgumentParser(
        description='Automatically upload Spectator articles.',
        parents=[tools.argparser])
    parser.add_argument('--local', help='post data to a specified port')
    parser.add_argument('-s', dest='scan', action='store_true',
                        help='first scan files for id adjustments')
    parser.set_defaults(scan=False)
    flags = parser.parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Spec CLI'


DRIVE_STORAGE_FILENAME = 'files.in'
files = []
service = None


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


def scan_drive_files(service):
    page_token = None
    files = []

    while 1:
        response = service.files().list(
            q="not trashed and (mimeType='application/vnd.google-apps.folder'" +
              " or mimeType='application/vnd.google-apps.document'" +
              " or mimeType='application/pdf'" +
              " or mimeType contains 'image')",
            spaces='drive',
            fields='nextPageToken, files(id, name, parents, mimeType)',
            pageToken=page_token).execute()
        files += response.get('files', [])
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
        print('Scanned {} Drive files.'.format(len(files)))

    with open(DRIVE_STORAGE_FILENAME, 'w') as f:
        f.write(str(files))
        print('[100%] Scanned all {} Drive files into {}.'
              .format(len(files), DRIVE_STORAGE_FILENAME))


def get_file(name_pattern, file_type, parent_id=None):
    mime_type = 'application/vnd.google-apps.' + file_type if file_type in ['folder', 'document'] else file_type
    if parent_id is not None:
        return next((
            f for f in files
            if (f['mimeType'] == mime_type
                and re.search(name_pattern, f['name'])
                and parent_id in f.get('parents', []))
        ))
    return next((
        f for f in files
        if (f['mimeType'] == mime_type
            and re.search(name_pattern, f['name']))
    ))


def analyze_issue(volume, issue):
    volume_folder = get_file(r"Volume {}".format(volume), 'folder')
    issue_folder = get_file(r"Issue\s?{}".format(issue), 'folder',
                                  volume_folder['id'])
    sbc_folder = get_file(r"SBC", 'folder', issue_folder['id'])
    newspaper_pdf = get_file("(?i)Issue\s?\d{1,2}(\.pdf)$",
                                   'application/pdf',
                                   issue_folder['id'])
    art_folder = drive.get_file(r"(?i)art", 'folder', issue_folder['id'])
    try:
        photo_folder = drive.get_file(r"(?i)(photo\s?color)", 'folder',
                                      issue_folder['id'])
    except StopIteration:
        photo_folder = drive.get_file(r"(?i)(photo\s?b&?w)", 'folder',
                                      issue_folder['id'])

    media_files = drive.get_children([art_folder['id'], photo_folder['id']],
    print(volume_folder, issue_folder, sbc_folder, newspaper_pdf)


def main():


    # volume_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL).strip())
    print(
        Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL + '108')
    volume = 108
    # issue_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL.strip()))
    print(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL + '5')
    issue = 6

    analyze_issue(108, 6)


def init():
    global service
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    if flags.scan:
        scan_drive_files(service)

    global files
    with open(DRIVE_STORAGE_FILENAME, 'r') as f:
        files = ast.literal_eval(f.read())
    print('Scanned in {} Drive files from storage.'.format(len(files)))


if __name__ == '__main__':
    colorama.init()
    init()
    main()