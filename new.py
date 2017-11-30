from __future__ import print_function
import httplib2
import os
import re
import io
import ast
import json
import requests
import constants
import sections
import articles
import config
import utils
import Promise

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaIoBaseDownload

from colorama import Fore, Back, Style
import colorama

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

ISSUE_DATES = {
    '107': {
        '16': '2017-06-09',
        '15': '2017-05-26',
        '14': '2017-05-08',
        '13': '2017-04-21',
        '12': '2017-03-31',
        '11': '2017-03-10',
    },
    '108': {
        '1': '2017-09-11',
        '2': '2017-09-29',
        '3': '2017-10-17',
        '4': '2017-10-31',
        '5': '2017-11-10',
        '6': '2017-11-29'
    }
}

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


def get_children(parent_ids, file_type=None):
    if type(parent_ids) is unicode or type(parent_ids) is str:
        parent_ids = [parent_ids]
    if file_type is not None:
        if file_type in ['document', 'folder']:
            mime_type = 'application/vnd.google-apps.' + file_type
        elif file_type == 'image':
            mime_type = 'image'
        else:
            raise ValueError(
                'Expected file type document, folder, image, but received: {}.'.
                format(file_type))
        return [
            f for f in files
            if (mime_type in f['mimeType']
                and any(p in f.get('parents', []) for p in parent_ids))
        ]
    return [
        f for f in files if any(p in f.get('parents', []) for p in parent_ids)
    ]


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


def download_document(file):
    if file['mimeType'] != 'application/vnd.google-apps.document':
        raise ValueError('File of MIME type {} should not be downloaded here.'
                         .format(file['mimeType']))
    request = service.files().export_media(
        fileId=file['id'], mimeType='text/plain')
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print('%d%%' % int(status.progress() * 100))
    return fh.getvalue()



def post_article(data):
    data['created_at'] = ISSUE_DATES[str(data['volume'])][str(data['issue'])]
    article = utils.post_modify_headers(
        constants.API_ARTICLES_ENDPOINT,
        data=json.dumps(data),
        headers=config.headers
    )
    return article['id']


def analyze_issue(volume, issue):
    volume_folder = get_file(r"Volume {}".format(volume), 'folder')
    issue_folder = get_file(r"Issue\s?{}".format(issue), 'folder',
                                  volume_folder['id'])
    sbc_folder = get_file(r"SBC", 'folder', issue_folder['id'])
    newspaper_pdf = get_file("(?i)Issue\s?\d{1,2}(\.pdf)$",
                                   'application/pdf',
                                   issue_folder['id'])
    art_folder = get_file(r"(?i)art", 'folder', issue_folder['id'])
    try:
        photo_folder = get_file(r"(?i)(photo\s?color)", 'folder',
                                      issue_folder['id'])
    except StopIteration:
        photo_folder = get_file(r"(?i)(photo\s?b&?w)", 'folder',
                                      issue_folder['id'])
    images = get_children([art_folder['id'], photo_folder['id']], 'image')

    for section_name in ['News', 'Features', 'Opinions', 'A&E', 'Humor', 'Sports']:
        section_folder = get_file(section_name, 'folder', sbc_folder['id'])
        section_id = sections.get_section_id(section_name)
        for article_file in get_children(section_folder['id'], 'document'):
            print('\n')
            if re.search(r"(?i)worldbeat|survey|newsbeat|spookbeat",
                         article_file['name']):
                print(Fore.RED + Style.BRIGHT + article_file['name'] + 'skipped.'
                      + Style.RESET_ALL)
                continue
            print(
                Fore.CYAN + Style.BRIGHT + section_name.upper() +
                Fore.BLUE + ' ' + article_file['name'] + Style.RESET_ALL,
                end=' ')
            raw_text = download_document(article_file)
            if articles.does_file_exist(raw_text):
                print(Fore.RED + article_file['name'] + 'exists; skipped.'
                      + Style.RESET_ALL)
                continue
            article_data = articles.analyze_article(raw_text)
            article_data.update({
                'volume': volume,
                'issue': issue,
                'section_id': section_id
            })
            confirmation = raw_input(Fore.GREEN + Style.BRIGHT
                                     + 'post article? ' + Style.RESET_ALL)
            if confirmation == 'n':
                continue

            article_data['id'] = post_article(article_data)
            article_create = Promise(
                lambda resolve, reject: resolve(users.post_contirbutors(article_data))
            )


def main():
    # volume_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL).strip())
    print(
        Fore.BLUE + Style.BRIGHT + 'Volume #: ' + Style.RESET_ALL + '108')
    volume = 108
    # issue_number = int(raw_input(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL.strip()))
    print(Fore.BLUE + Style.BRIGHT + 'Issue #: ' + Style.RESET_ALL + '5')
    issue = 6

    try:
        ISSUE_DATES[str(volume)][str(issue)]
    except KeyError:
        print(Fore.RED + Style.BRIGHT + 'Volume {} Issue {} does not have a date'.format(volume, issue))
        return

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

    config.sign_in()

if __name__ == '__main__':
    colorama.init()
    if flags.local is not None:
        constants.init('localhost:{}'.format(flags.local))
    else:
        constants.init()
    config.init()
    init()
    sections.init()
    articles.init()
    main()